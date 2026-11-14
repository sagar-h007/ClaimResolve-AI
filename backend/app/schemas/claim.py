from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.claim import ClaimStatus
from app.schemas.patient import PatientResponse


class ClaimBase(BaseModel):
    payer_name: str
    policy_number_masked: str
    procedure_codes: List[str] = Field(default_factory=list)
    diagnosis_codes: List[str] = Field(default_factory=list)
    claim_amount: float = 0.0
    denied_amount: float = 0.0
    denial_date: Optional[str] = None
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = None
    notes: Optional[str] = None


class ClaimCreate(ClaimBase):
    patient_id: Optional[str] = None
    # Or create a quick synthetic patient reference inline:
    external_patient_id: Optional[str] = None
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None
    patient_dob: Optional[str] = None


class ClaimUpdate(BaseModel):
    payer_name: Optional[str] = None
    policy_number_masked: Optional[str] = None
    procedure_codes: Optional[List[str]] = None
    diagnosis_codes: Optional[List[str]] = None
    claim_amount: Optional[float] = None
    denied_amount: Optional[float] = None
    denial_date: Optional[str] = None
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = None
    claim_status: Optional[ClaimStatus] = None
    notes: Optional[str] = None


class ClaimResponse(ClaimBase):
    id: str
    organization_id: str
    patient_id: str
    claim_number: str
    claim_status: ClaimStatus
    created_at: datetime
    updated_at: datetime
    patient: Optional[PatientResponse] = None
    document_count: Optional[int] = 0
    has_analysis: Optional[bool] = False
    has_appeal: Optional[bool] = False

    class Config:
        from_attributes = True


class ClaimListResponse(BaseModel):
    total: int
    items: List[ClaimResponse]

