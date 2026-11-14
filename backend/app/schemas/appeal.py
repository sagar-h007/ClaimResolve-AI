from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.appeal import AppealStatus


class AppealVersionResponse(BaseModel):
    id: str
    version_number: int
    full_letter_text: str
    change_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AppealLetterResponse(BaseModel):
    id: str
    claim_id: str
    organization_id: str
    analysis_id: Optional[str] = None
    title: str
    status: AppealStatus
    current_version: int
    provider_info: Dict[str, Any] = {}
    patient_info: Dict[str, Any] = {}
    claim_info: Dict[str, Any] = {}
    original_denial_details: Dict[str, Any] = {}
    clinical_justification: str
    policy_references: str
    supporting_evidence: str
    request_for_reconsideration: str
    supporting_document_references: List[Dict[str, Any]] = []
    full_letter_text: str
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    versions: List[AppealVersionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateAppealRequest(BaseModel):
    title: Optional[str] = None
    full_letter_text: Optional[str] = None
    clinical_justification: Optional[str] = None
    policy_references: Optional[str] = None
    supporting_evidence: Optional[str] = None
    request_for_reconsideration: Optional[str] = None
    status: Optional[AppealStatus] = None
    change_summary: Optional[str] = "Manual user revision"


class GenerateAppealRequest(BaseModel):
    tone: Optional[str] = "formal_assertive"  # "formal_assertive", "clinical_collaborative"
    include_statutory_citations: bool = True
    provider_contact_name: Optional[str] = None
    provider_department: Optional[str] = "Department of Patient Financial Services & Utilization Review"


class RegenerateSectionRequest(BaseModel):
    section_name: str  # "clinical_justification", "policy_references", "supporting_evidence", "request_for_reconsideration"
    instructions: Optional[str] = None

