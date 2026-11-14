import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.audit import AuditLog
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing_user_result = await db.execute(select(User).where(User.email == user_in.email))
    if existing_user_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Create or find organization
    org_slug = slugify(user_in.organization_name)
    existing_org_res = await db.execute(select(Organization).where(Organization.slug == org_slug))
    org = existing_org_res.scalars().first()
    
    if not org:
        org = Organization(
            name=user_in.organization_name,
            slug=org_slug,
        )
        db.add(org)
        await db.flush()
        # First user in newly created org is Admin
        role = UserRole.ADMIN
    else:
        role = user_in.role or UserRole.SPECIALIST

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        organization_id=org.id,
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=role,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    # Audit log
    audit = AuditLog(
        organization_id=org.id,
        user_id=new_user.id,
        action="USER_REGISTERED",
        resource_type="user",
        resource_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role.value},
    )
    db.add(audit)
    await db.commit()

    token = create_access_token(
        subject=new_user.id,
        organization_id=org.id,
        role=new_user.role.value,
    )

    user_resp = UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        organization_id=org.id,
        organization_name=org.name,
        is_active=new_user.is_active,
    )

    return Token(access_token=token, token_type="bearer", user=user_resp)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    org_result = await db.execute(select(Organization).where(Organization.id == user.organization_id))
    org = org_result.scalars().first()

    token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
    )

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org.name if org else "Healthcare Organization",
        is_active=user.is_active,
    )

    return Token(access_token=token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = org_result.scalars().first()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        organization_id=current_user.organization_id,
        organization_name=org.name if org else None,
        is_active=current_user.is_active,
    )

