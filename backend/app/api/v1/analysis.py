from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.claim import Claim, ClaimStatus
from app.models.document import Document, DocumentChunk, DocumentCategory
from app.models.analysis import ClaimAnalysis, EvidenceReference, AnalysisStatus, EvidenceStrength
from app.models.audit import AuditLog
from app.schemas.analysis import ClaimAnalysisResponse, EvidenceReferenceSchema, AnalyzeClaimRequest
from app.ai.denial_analyzer import DenialAnalyzer
from app.ai.clinical_retriever import ClinicalEvidenceRetriever
from app.ai.policy_retriever import PayerPolicyRetriever
from app.ai.evidence_comparator import EvidenceComparator
from app.api.deps import get_current_user

router = APIRouter(prefix="/claims", tags=["AI Claim Analysis"])


@router.post("/{claim_id}/analyze", response_model=ClaimAnalysisResponse)
async def analyze_claim(
    claim_id: str,
    request: AnalyzeClaimRequest = AnalyzeClaimRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify claim belongs to user org
    claim_res = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id, Claim.organization_id == current_user.organization_id)
        .options(selectinload(Claim.documents), selectinload(Claim.patient))
    )
    claim = claim_res.scalars().first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim.claim_status = ClaimStatus.PROCESSING
    await db.commit()

    # Find documents for this claim
    denial_docs = [d for d in claim.documents if d.category == DocumentCategory.DENIAL_LETTER]
    clinical_docs = [d for d in claim.documents if d.category == DocumentCategory.CLINICAL_RECORD]
    policy_docs = [d for d in claim.documents if d.category == DocumentCategory.PAYER_POLICY]

    # Also check if organization has general policy docs if claim-specific not set
    if not policy_docs:
        org_policies = await db.execute(
            select(Document).where(
                Document.organization_id == current_user.organization_id,
                Document.category == DocumentCategory.PAYER_POLICY,
            )
        )
        policy_docs = list(org_policies.scalars().all())

    # Step 1: Denial Analysis
    denial_text = ""
    if denial_docs:
        # Get chunks from denial doc
        chunks_res = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == denial_docs[0].id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_res.scalars().all()
        denial_text = "\n".join([c.content for c in chunks])
    elif claim.denial_reason:
        denial_text = f"Denial Reason: {claim.denial_reason}\nDenial Code: {claim.denial_code or 'CO-50'}"
    else:
        denial_text = "Claim denied due to lack of medical necessity and conservative therapy documentation."

    denial_analysis = await DenialAnalyzer.analyze_denial(denial_text)

    # Step 2: Clinical Evidence Retrieval
    clinical_chunks = await ClinicalEvidenceRetriever.retrieve_clinical_evidence(
        db=db,
        claim_id=claim.id,
        denial_reason=denial_analysis.denial_reason,
        required_items=denial_analysis.required_supporting_documentation,
        top_k=5,
    )

    # Step 3: Policy Retrieval
    policy_chunks = await PayerPolicyRetriever.retrieve_policy_sections(
        db=db,
        claim_id=claim.id,
        procedure_codes=claim.procedure_codes or [],
        denial_code=denial_analysis.denial_code,
        denial_reason=denial_analysis.denial_reason,
        top_k=4,
    )

    # Step 4: Evidence Comparison & Gap Analysis
    comparison = await EvidenceComparator.compare_evidence(
        denial_reason=denial_analysis.denial_reason,
        denial_code=denial_analysis.denial_code,
        clinical_chunks=clinical_chunks,
        policy_chunks=policy_chunks,
    )

    # Create ClaimAnalysis record
    evidence_strength_val = EvidenceStrength(comparison.evidence_strength) if comparison.evidence_strength in [e.value for e in EvidenceStrength] else EvidenceStrength.MODERATE

    new_analysis = ClaimAnalysis(
        claim_id=claim.id,
        organization_id=current_user.organization_id,
        status=AnalysisStatus.COMPLETED,
        denial_reason=comparison.denial_reason,
        denial_code=denial_analysis.denial_code,
        payer_explanation=denial_analysis.payer_explanation,
        policy_section=comparison.policy_section,
        policy_requirements_summary=comparison.policy_requirements_summary,
        clinical_findings_summary=comparison.clinical_findings_summary,
        evidence_strength=evidence_strength_val,
        missing_evidence=comparison.missing_evidence,
        conflicting_information=comparison.conflicting_information,
        potential_appeal_arguments=comparison.potential_appeal_arguments,
        recommended_next_steps=comparison.recommended_next_steps,
        risk_indicators=comparison.risk_indicators,
        raw_llm_output=comparison.raw_output,
    )
    db.add(new_analysis)
    await db.flush()

    # Create Evidence References
    for item in comparison.supporting_evidence:
        # Match chunk if available
        matched_chunk_id = None
        matched_doc_id = None
        for cc in clinical_chunks:
            if cc.document_filename in item.get("source", ""):
                matched_chunk_id = cc.chunk_id
                matched_doc_id = cc.document_id
                break

        ref = EvidenceReference(
            analysis_id=new_analysis.id,
            chunk_id=matched_chunk_id,
            document_id=matched_doc_id,
            document_type="clinical_record",
            source_document_title=item.get("source", "Patient Record"),
            page_number=str(item.get("page", "1")),
            citation_text=item.get("citation", ""),
            extracted_text=item.get("citation", ""),
            relevance_score=float(item.get("relevance", 0.9)),
            is_supporting=True,
        )
        db.add(ref)

    # Update claim status
    claim.claim_status = ClaimStatus.ANALYSIS_COMPLETE
    claim.denial_code = denial_analysis.denial_code
    claim.denial_reason = comparison.denial_reason

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="CLAIM_ANALYZED",
        resource_type="claim_analysis",
        resource_id=new_analysis.id,
        details={"claim_id": claim.id, "strength": evidence_strength_val.value},
    )
    db.add(audit)
    await db.commit()

    # Return full response
    full_res = await db.execute(
        select(ClaimAnalysis)
        .where(ClaimAnalysis.id == new_analysis.id)
        .options(selectinload(ClaimAnalysis.evidence_references))
    )
    saved_analysis = full_res.scalars().first()

    return ClaimAnalysisResponse(
        id=saved_analysis.id,
        claim_id=saved_analysis.claim_id,
        organization_id=saved_analysis.organization_id,
        status=saved_analysis.status,
        denial_reason=saved_analysis.denial_reason,
        denial_code=saved_analysis.denial_code,
        payer_explanation=saved_analysis.payer_explanation,
        policy_section=saved_analysis.policy_section,
        policy_requirements_summary=saved_analysis.policy_requirements_summary,
        clinical_findings_summary=saved_analysis.clinical_findings_summary,
        evidence_strength=saved_analysis.evidence_strength,
        missing_evidence=saved_analysis.missing_evidence or [],
        conflicting_information=saved_analysis.conflicting_information or [],
        potential_appeal_arguments=saved_analysis.potential_appeal_arguments or [],
        recommended_next_steps=saved_analysis.recommended_next_steps or [],
        risk_indicators=saved_analysis.risk_indicators or [],
        evidence_references=[
            EvidenceReferenceSchema.model_validate(er) for er in saved_analysis.evidence_references
        ],
        created_at=saved_analysis.created_at,
        updated_at=saved_analysis.updated_at,
    )


@router.get("/{claim_id}/analysis", response_model=ClaimAnalysisResponse)
async def get_claim_analysis(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClaimAnalysis)
        .where(ClaimAnalysis.claim_id == claim_id, ClaimAnalysis.organization_id == current_user.organization_id)
        .options(selectinload(ClaimAnalysis.evidence_references))
        .order_by(desc(ClaimAnalysis.created_at))
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI analysis found for this claim. Run analysis first.",
        )

    return ClaimAnalysisResponse(
        id=analysis.id,
        claim_id=analysis.claim_id,
        organization_id=analysis.organization_id,
        status=analysis.status,
        denial_reason=analysis.denial_reason,
        denial_code=analysis.denial_code,
        payer_explanation=analysis.payer_explanation,
        policy_section=analysis.policy_section,
        policy_requirements_summary=analysis.policy_requirements_summary,
        clinical_findings_summary=analysis.clinical_findings_summary,
        evidence_strength=analysis.evidence_strength,
        missing_evidence=analysis.missing_evidence or [],
        conflicting_information=analysis.conflicting_information or [],
        potential_appeal_arguments=analysis.potential_appeal_arguments or [],
        recommended_next_steps=analysis.recommended_next_steps or [],
        risk_indicators=analysis.risk_indicators or [],
        evidence_references=[
            EvidenceReferenceSchema.model_validate(er) for er in analysis.evidence_references
        ],
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )

