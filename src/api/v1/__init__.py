from src.api.v1.auth import auth_router
from src.api.v1.profile import profile_router
from src.api.v1.category import category_router
from src.api.v1.sessions import user_session_router
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(category_router, prefix="/category", tags=["category"])
api_router.include_router(user_session_router, prefix="/session", tags=["session"])
