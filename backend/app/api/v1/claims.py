import random
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.claim import Claim, ClaimStatus
from app.models.patient import Patient
from app.models.document import Document
from app.models.analysis import ClaimAnalysis
from app.models.appeal import AppealLetter
from app.models.audit import AuditLog
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse, ClaimListResponse
from app.schemas.patient import PatientResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/claims", tags=["Claims"])


def generate_claim_number() -> str:
    return f"CLM-2025-{random.randint(100000, 999999)}"


@router.get("", response_model=ClaimListResponse)
async def list_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ClaimStatus] = None,
    payer: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Claim)
        .where(Claim.organization_id == current_user.organization_id)
        .options(selectinload(Claim.patient), selectinload(Claim.documents), selectinload(Claim.analyses), selectinload(Claim.appeals))
        .order_by(desc(Claim.created_at))
    )

    if status:
        query = query.where(Claim.claim_status == status)
    if payer:
        query = query.where(Claim.payer_name.ilike(f"%{payer}%"))
    if search:
        search_filter = or_(
            Claim.claim_number.ilike(f"%{search}%"),
            Claim.payer_name.ilike(f"%{search}%"),
            Claim.denial_code.ilike(f"%{search}%"),
            Claim.denial_reason.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    # Count total
    count_query = select(func.count(Claim.id)).where(Claim.organization_id == current_user.organization_id)
    if status:
        count_query = count_query.where(Claim.claim_status == status)
    if payer:
        count_query = count_query.where(Claim.payer_name.ilike(f"%{payer}%"))
    if search:
        count_query = count_query.where(search_filter)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    results = await db.execute(query.offset(skip).limit(limit))
    claims = results.scalars().all()

    items = []
    for c in claims:
        patient_resp = PatientResponse.model_validate(c.patient) if c.patient else None
        items.append(
            ClaimResponse(
                id=c.id,
                organization_id=c.organization_id,
                patient_id=c.patient_id,
                claim_number=c.claim_number,
                payer_name=c.payer_name,
                policy_number_masked=c.policy_number_masked,
                procedure_codes=c.procedure_codes or [],
                diagnosis_codes=c.diagnosis_codes or [],
                claim_amount=c.claim_amount,
                denied_amount=c.denied_amount,
                denial_date=c.denial_date,
                denial_reason=c.denial_reason,
                denial_code=c.denial_code,
                claim_status=c.claim_status,
                notes=c.notes,
                created_at=c.created_at,
                updated_at=c.updated_at,
                patient=patient_resp,
                document_count=len(c.documents) if c.documents else 0,
                has_analysis=bool(c.analyses and len(c.analyses) > 0),
                has_appeal=bool(c.appeals and len(c.appeals) > 0),
            )
        )

    return ClaimListResponse(total=total, items=items)


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_in: ClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient_id = claim_in.patient_id

    # If patient_id is not provided, create a synthetic patient
    if not patient_id:
        ext_id = claim_in.external_patient_id or f"PT-{random.randint(10000, 99999)}"
        first_name = claim_in.patient_first_name or "Jane"
        last_name = claim_in.patient_last_name or "Doe"
        dob = claim_in.patient_dob or "1980-05-15"

        new_patient = Patient(
            organization_id=current_user.organization_id,
            external_patient_id=ext_id,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            insurance_policy_number=claim_in.policy_number_masked,
            payer_name=claim_in.payer_name,
        )
        db.add(new_patient)
        await db.flush()
        patient_id = new_patient.id
    else:
        # Validate patient exists in user's org
        pat_res = await db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.organization_id == current_user.organization_id
            )
        )
        if not pat_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found in your organization",
            )

    new_claim = Claim(
        organization_id=current_user.organization_id,
        patient_id=patient_id,
        claim_number=generate_claim_number(),
        payer_name=claim_in.payer_name,
        policy_number_masked=claim_in.policy_number_masked,
        procedure_codes=claim_in.procedure_codes or [],
        diagnosis_codes=claim_in.diagnosis_codes or [],
        claim_amount=claim_in.claim_amount,
        denied_amount=claim_in.denied_amount,
        denial_date=claim_in.denial_date,
        denial_reason=claim_in.denial_reason,
        denial_code=claim_in.denial_code,
        claim_status=ClaimStatus.UPLOADED,
        notes=claim_in.notes,
    )
    db.add(new_claim)
    await db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="CLAIM_CREATED",
        resource_type="claim",
        resource_id=new_claim.id,
        details={"claim_number": new_claim.claim_number, "amount": new_claim.denied_amount},
    )
    db.add(audit)
    await db.commit()

    # Re-fetch with patient relation
    res = await db.execute(
        select(Claim)
        .where(Claim.id == new_claim.id)
        .options(selectinload(Claim.patient), selectinload(Claim.documents))
    )
    saved_claim = res.scalars().first()

    return ClaimResponse(
        id=saved_claim.id,
        organization_id=saved_claim.organization_id,
        patient_id=saved_claim.patient_id,
        claim_number=saved_claim.claim_number,
        payer_name=saved_claim.payer_name,
        policy_number_masked=saved_claim.policy_number_masked,
        procedure_codes=saved_claim.procedure_codes or [],
        diagnosis_codes=saved_claim.diagnosis_codes or [],
        claim_amount=saved_claim.claim_amount,
        denied_amount=saved_claim.denied_amount,
        denial_date=saved_claim.denial_date,
        denial_reason=saved_claim.denial_reason,
        denial_code=saved_claim.denial_code,
        claim_status=saved_claim.claim_status,
        notes=saved_claim.notes,
        created_at=saved_claim.created_at,
        updated_at=saved_claim.updated_at,
        patient=PatientResponse.model_validate(saved_claim.patient) if saved_claim.patient else None,
        document_count=0,
        has_analysis=False,
        has_appeal=False,
    )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id, Claim.organization_id == current_user.organization_id)
        .options(selectinload(Claim.patient), selectinload(Claim.documents), selectinload(Claim.analyses), selectinload(Claim.appeals))
    )
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    return ClaimResponse(
        id=claim.id,
        organization_id=claim.organization_id,
        patient_id=claim.patient_id,
        claim_number=claim.claim_number,
        payer_name=claim.payer_name,
        policy_number_masked=claim.policy_number_masked,
        procedure_codes=claim.procedure_codes or [],
        diagnosis_codes=claim.diagnosis_codes or [],
        claim_amount=claim.claim_amount,
        denied_amount=claim.denied_amount,
        denial_date=claim.denial_date,
        denial_reason=claim.denial_reason,
        denial_code=claim.denial_code,
        claim_status=claim.claim_status,
        notes=claim.notes,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        patient=PatientResponse.model_validate(claim.patient) if claim.patient else None,
        document_count=len(claim.documents) if claim.documents else 0,
        has_analysis=bool(claim.analyses and len(claim.analyses) > 0),
        has_appeal=bool(claim.appeals and len(claim.appeals) > 0),
    )


@router.patch("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: str,
    claim_update: ClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id, Claim.organization_id == current_user.organization_id)
        .options(selectinload(Claim.patient), selectinload(Claim.documents), selectinload(Claim.analyses), selectinload(Claim.appeals))
    )
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    update_data = claim_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(claim, field, val)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="CLAIM_UPDATED",
        resource_type="claim",
        resource_id=claim.id,
        details={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(claim)

    return ClaimResponse(
        id=claim.id,
        organization_id=claim.organization_id,
        patient_id=claim.patient_id,
        claim_number=claim.claim_number,
        payer_name=claim.payer_name,
        policy_number_masked=claim.policy_number_masked,
        procedure_codes=claim.procedure_codes or [],
        diagnosis_codes=claim.diagnosis_codes or [],
        claim_amount=claim.claim_amount,
        denied_amount=claim.denied_amount,
        denial_date=claim.denial_date,
        denial_reason=claim.denial_reason,
        denial_code=claim.denial_code,
        claim_status=claim.claim_status,
        notes=claim.notes,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        patient=PatientResponse.model_validate(claim.patient) if claim.patient else None,
        document_count=len(claim.documents) if claim.documents else 0,
        has_analysis=bool(claim.analyses and len(claim.analyses) > 0),
        has_appeal=bool(claim.appeals and len(claim.appeals) > 0),
    )


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Claim).where(Claim.id == claim_id, Claim.organization_id == current_user.organization_id)
    )
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    await db.delete(claim)
    await db.commit()
    return None

