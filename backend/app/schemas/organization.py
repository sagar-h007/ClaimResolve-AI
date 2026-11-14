from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    domain: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

