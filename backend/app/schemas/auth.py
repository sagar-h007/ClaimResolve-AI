from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    role: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str
    role: Optional[UserRole] = UserRole.SPECIALIST


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    organization_id: str
    organization_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

