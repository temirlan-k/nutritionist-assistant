from fastapi import APIRouter, BackgroundTasks, Depends

from src.schemas.req.sessions import SessionCreateReq, DayPlanUpdate
from src.core.auth_middleware import get_current_user
from src.service.sessions import UserCategorySessionService

user_session_router = APIRouter()

@user_session_router.get("/sessions")
async def get_sessions(
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(UserCategorySessionService)

):
    return await session_service.get_sessions(token.get("sub"))


@user_session_router.post("/sessions")
async def create_session(
    req: SessionCreateReq,
    bg_tasks: BackgroundTasks,
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(UserCategorySessionService)
):
    return await session_service.create_session(bg_tasks,token.get('sub'),req)

@user_session_router.get("/sessions/{session_id}")
async def get_session_by_id(
    session_id: str,
    offset: int = 0,
    session_service: UserCategorySessionService = Depends(UserCategorySessionService)
):
    return await session_service.get_session_by_id(session_id,offset)

@user_session_router.patch("/sessions/{session_id}/day-plan/{day_plan_id}")
async def update_session_day_plan(
    session_id: str,
    day_plan_id: str,
    req: DayPlanUpdate,
    session_service: UserCategorySessionService = Depends(UserCategorySessionService)
):
    return await session_service.update_dayplan(session_id,day_plan_id,req)