from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.claims import router as claims_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.appeals import router as appeals_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.demo import router as demo_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(claims_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)
api_router.include_router(appeals_router)
api_router.include_router(analytics_router)
api_router.include_router(demo_router)
