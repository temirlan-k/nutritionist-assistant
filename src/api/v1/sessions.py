from fastapi import APIRouter, BackgroundTasks, Depends

from src.schemas.req.sessions import SessionCreateReq
from src.core.auth_middleware import get_current_user
from src.service.sessions import UserCategorySessionService

user_session_router = APIRouter()

@user_session_router.get("/sessions")
async def get_sessions(
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(UserCategorySessionService)

):
    return session_service.get_sessions(token.get("sub"))


@user_session_router.post("/sessions")
async def create_session(
    bg_task: BackgroundTasks,
    req: SessionCreateReq,
    token: dict = Depends(get_current_user),

    session_service: UserCategorySessionService = Depends(UserCategorySessionService)
):
    return await session_service.create_session(bg_task,token.get('sub'),req)