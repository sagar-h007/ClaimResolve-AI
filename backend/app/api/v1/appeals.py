from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.claim import Claim, ClaimStatus
from app.models.analysis import ClaimAnalysis, AnalysisStatus
from app.models.appeal import AppealLetter, AppealVersion, AppealStatus
from app.models.audit import AuditLog
from app.schemas.appeal import (
    AppealLetterResponse,
    AppealVersionResponse,
    UpdateAppealRequest,
    GenerateAppealRequest,
)
from app.ai.appeal_generator import AppealGenerator
from app.ai.evidence_comparator import EvidenceComparisonResult
from app.services.pdf_export_service import PDFExportService
from app.api.deps import get_current_user

router = APIRouter(tags=["Appeals"])


@router.post("/claims/{claim_id}/appeal/generate", response_model=AppealLetterResponse)
async def generate_appeal(
    claim_id: str,
    req: GenerateAppealRequest = GenerateAppealRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify claim & analysis exist
    claim_res = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id, Claim.organization_id == current_user.organization_id)
        .options(selectinload(Claim.patient))
    )
    claim = claim_res.scalars().first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    analysis_res = await db.execute(
        select(ClaimAnalysis)
        .where(ClaimAnalysis.claim_id == claim_id)
        .options(selectinload(ClaimAnalysis.evidence_references))
        .order_by(desc(ClaimAnalysis.created_at))
    )
    analysis = analysis_res.scalars().first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run AI analysis on this claim first before generating an appeal.",
        )

    # Build comparison result from stored analysis
    comparison = EvidenceComparisonResult(
        denial_reason=analysis.denial_reason or "",
        policy_section=analysis.policy_section or "General Policy",
        policy_requirements_summary=analysis.policy_requirements_summary or "",
        clinical_findings_summary=analysis.clinical_findings_summary or "",
        evidence_strength=analysis.evidence_strength.value if analysis.evidence_strength else "Moderate",
        supporting_evidence=[
            {
                "source": ref.source_document_title,
                "page": ref.page_number,
                "citation": ref.citation_text,
                "relevance": ref.relevance_score,
            }
            for ref in (analysis.evidence_references or [])
        ],
        missing_evidence=analysis.missing_evidence or [],
        conflicting_information=analysis.conflicting_information or [],
        potential_appeal_arguments=analysis.potential_appeal_arguments or [],
        recommended_next_steps=analysis.recommended_next_steps or [],
        risk_indicators=analysis.risk_indicators or [],
        raw_output=analysis.raw_llm_output or {},
    )

    patient = claim.patient
    patient_data = {
        "external_patient_id": patient.external_patient_id if patient else "PT-00000",
        "first_name": patient.first_name if patient else "Jane",
        "last_name": patient.last_name if patient else "Doe",
        "dob": patient.dob if patient else "1980-01-01",
    }
    claim_data = {
        "claim_number": claim.claim_number,
        "payer_name": claim.payer_name,
        "policy_number_masked": claim.policy_number_masked,
        "procedure_codes": claim.procedure_codes or [],
        "diagnosis_codes": claim.diagnosis_codes or [],
        "claim_amount": claim.claim_amount,
        "denied_amount": claim.denied_amount,
        "denial_date": claim.denial_date,
        "denial_code": claim.denial_code or analysis.denial_code or "CO-50",
    }

    appeal_data = await AppealGenerator.generate_appeal(
        claim_data=claim_data,
        patient_data=patient_data,
        comparison=comparison,
        tone=req.tone or "formal_assertive",
        provider_dept=req.provider_department or "Department of Patient Financial Services & Utilization Review",
    )

    # Check if appeal already exists
    existing_res = await db.execute(
        select(AppealLetter).where(AppealLetter.claim_id == claim_id)
    )
    existing = existing_res.scalars().first()
    if existing:
        # Update existing
        existing.clinical_justification = appeal_data["clinical_justification"]
        existing.policy_references = appeal_data["policy_references"]
        existing.supporting_evidence = appeal_data["supporting_evidence"]
        existing.request_for_reconsideration = appeal_data["request_for_reconsideration"]
        existing.full_letter_text = appeal_data["full_letter_text"]
        existing.provider_info = appeal_data["provider_info"]
        existing.patient_info = appeal_data["patient_info"]
        existing.claim_info = appeal_data["claim_info"]
        existing.original_denial_details = appeal_data["original_denial_details"]
        existing.supporting_document_references = appeal_data["supporting_document_references"]
        existing.current_version += 1
        existing.status = AppealStatus.DRAFT

        version = AppealVersion(
            appeal_id=existing.id,
            version_number=existing.current_version,
            full_letter_text=appeal_data["full_letter_text"],
            edited_by_user_id=current_user.id,
            change_summary="AI regenerated appeal letter",
        )
        db.add(version)
        appeal_obj = existing
    else:
        appeal_obj = AppealLetter(
            claim_id=claim.id,
            organization_id=current_user.organization_id,
            analysis_id=analysis.id,
            title=appeal_data.get("title", "Medical Necessity Appeal"),
            status=AppealStatus.DRAFT,
            current_version=1,
            provider_info=appeal_data["provider_info"],
            patient_info=appeal_data["patient_info"],
            claim_info=appeal_data["claim_info"],
            original_denial_details=appeal_data["original_denial_details"],
            clinical_justification=appeal_data["clinical_justification"],
            policy_references=appeal_data["policy_references"],
            supporting_evidence=appeal_data["supporting_evidence"],
            request_for_reconsideration=appeal_data["request_for_reconsideration"],
            supporting_document_references=appeal_data["supporting_document_references"],
            full_letter_text=appeal_data["full_letter_text"],
        )
        db.add(appeal_obj)
        await db.flush()

        version = AppealVersion(
            appeal_id=appeal_obj.id,
            version_number=1,
            full_letter_text=appeal_data["full_letter_text"],
            edited_by_user_id=current_user.id,
            change_summary="Initial AI-generated appeal",
        )
        db.add(version)

    claim.claim_status = ClaimStatus.APPEAL_DRAFTED

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="APPEAL_GENERATED",
        resource_type="appeal",
        resource_id=appeal_obj.id,
        details={"claim_id": claim.id},
    )
    db.add(audit)
    await db.commit()

    # Query versions directly
    ver_res = await db.execute(
        select(AppealVersion)
        .where(AppealVersion.appeal_id == appeal_obj.id)
        .order_by(desc(AppealVersion.version_number))
    )
    versions = list(ver_res.scalars().all())

    return _build_appeal_response(appeal_obj, versions=versions)


@router.get("/claims/{claim_id}/appeal", response_model=AppealLetterResponse)
async def get_appeal(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AppealLetter)
        .where(
            AppealLetter.claim_id == claim_id,
            AppealLetter.organization_id == current_user.organization_id,
        )
    )
    appeal = result.scalars().first()
    if not appeal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No appeal found for this claim")

    ver_res = await db.execute(
        select(AppealVersion)
        .where(AppealVersion.appeal_id == appeal.id)
        .order_by(desc(AppealVersion.version_number))
    )
    versions = list(ver_res.scalars().all())
    return _build_appeal_response(appeal, versions=versions)


@router.patch("/appeals/{appeal_id}", response_model=AppealLetterResponse)
async def update_appeal(
    appeal_id: str,
    update: UpdateAppealRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AppealLetter)
        .where(
            AppealLetter.id == appeal_id,
            AppealLetter.organization_id == current_user.organization_id,
        )
    )
    appeal = result.scalars().first()
    if not appeal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appeal not found")

    update_data = update.model_dump(exclude_unset=True)
    change_summary = update_data.pop("change_summary", "Manual revision")

    text_changed = False
    for field, val in update_data.items():
        if field == "status":
            appeal.status = val
            if val == AppealStatus.APPROVED:
                appeal.approved_by_user_id = current_user.id
                appeal.approved_at = datetime.now(timezone.utc)
        else:
            setattr(appeal, field, val)
            if field == "full_letter_text":
                text_changed = True

    if text_changed:
        appeal.current_version += 1
        version = AppealVersion(
            appeal_id=appeal.id,
            version_number=appeal.current_version,
            full_letter_text=appeal.full_letter_text,
            edited_by_user_id=current_user.id,
            change_summary=change_summary,
        )
        db.add(version)

    await db.commit()

    ver_res = await db.execute(
        select(AppealVersion)
        .where(AppealVersion.appeal_id == appeal.id)
        .order_by(desc(AppealVersion.version_number))
    )
    versions = list(ver_res.scalars().all())
    return _build_appeal_response(appeal, versions=versions)


@router.get("/appeals/{appeal_id}/export")
async def export_appeal_pdf(
    appeal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AppealLetter)
        .where(
            AppealLetter.id == appeal_id,
            AppealLetter.organization_id == current_user.organization_id,
        )
    )
    appeal = result.scalars().first()
    if not appeal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appeal not found")

    pdf_bytes = PDFExportService.generate_appeal_pdf(appeal)
    filename = f"Appeal_{appeal.claim_id[:8]}_v{appeal.current_version}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_appeal_response(appeal: AppealLetter, versions: Optional[List[AppealVersion]] = None) -> AppealLetterResponse:
    v_list = versions if versions is not None else getattr(appeal, "versions", [])
    return AppealLetterResponse(
        id=appeal.id,
        claim_id=appeal.claim_id,
        organization_id=appeal.organization_id,
        analysis_id=appeal.analysis_id,
        title=appeal.title,
        status=appeal.status,
        current_version=appeal.current_version,
        provider_info=appeal.provider_info or {},
        patient_info=appeal.patient_info or {},
        claim_info=appeal.claim_info or {},
        original_denial_details=appeal.original_denial_details or {},
        clinical_justification=appeal.clinical_justification,
        policy_references=appeal.policy_references,
        supporting_evidence=appeal.supporting_evidence,
        request_for_reconsideration=appeal.request_for_reconsideration,
        supporting_document_references=appeal.supporting_document_references or [],
        full_letter_text=appeal.full_letter_text,
        approved_by_user_id=appeal.approved_by_user_id,
        approved_at=appeal.approved_at,
        versions=[
            AppealVersionResponse(
                id=v.id,
                version_number=v.version_number,
                full_letter_text=v.full_letter_text,
                change_summary=v.change_summary,
                created_at=v.created_at,
            )
            for v in (v_list or [])
        ],
        created_at=appeal.created_at,
        updated_at=appeal.updated_at,
    )

