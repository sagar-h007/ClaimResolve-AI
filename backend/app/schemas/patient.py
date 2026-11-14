from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PatientCreate(BaseModel):
    external_patient_id: str
    first_name: str
    last_name: str
    dob: str
    gender: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    payer_name: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    organization_id: str
    external_patient_id: str
    first_name: str
    last_name: str
    dob: str
    gender: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    payer_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

