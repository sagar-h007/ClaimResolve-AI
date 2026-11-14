from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.analysis import AnalysisStatus, EvidenceStrength


class EvidenceReferenceSchema(BaseModel):
    id: str
    document_type: str
    source_document_title: str
    page_number: str
    citation_text: str
    extracted_text: str
    relevance_score: float
    is_supporting: bool

    class Config:
        from_attributes = True


class ClaimAnalysisResponse(BaseModel):
    id: str
    claim_id: str
    organization_id: str
    status: AnalysisStatus
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = None
    payer_explanation: Optional[str] = None
    policy_section: Optional[str] = None
    policy_requirements_summary: Optional[str] = None
    clinical_findings_summary: Optional[str] = None
    evidence_strength: EvidenceStrength
    missing_evidence: List[str] = []
    conflicting_information: List[str] = []
    potential_appeal_arguments: List[str] = []
    recommended_next_steps: List[str] = []
    risk_indicators: List[str] = []
    evidence_references: List[EvidenceReferenceSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyzeClaimRequest(BaseModel):
    force_reanalyze: bool = False
    focus_areas: Optional[List[str]] = None

