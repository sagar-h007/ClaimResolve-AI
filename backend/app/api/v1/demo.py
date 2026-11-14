from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.models.claim import Claim
from app.seeds.synthetic_data import seed_synthetic_data
from app.api.deps import get_current_user

router = APIRouter(prefix="/demo", tags=["Demo Simulation"])


@router.post("/seed")
async def trigger_seed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seed synthetic evaluation cohort into the current user's organization."""
    try:
        await seed_synthetic_data(
            db=db,
            organization_id=current_user.organization_id,
            admin_user_id=current_user.id,
        )
        return {
            "status": "success",
            "message": "Demo cohort successfully seeded: 20 patients, 30 claims, documents, RAG embeddings, and 4 clinical scenarios.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {str(e)}")

