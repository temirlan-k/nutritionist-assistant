from fastapi import APIRouter, BackgroundTasks, Depends

from src.models.sessions import SessionStatus
from src.core.auth_middleware import get_current_user
from src.schemas.req.sessions import DayPlanUpdate, SessionCreateReq
from src.service.sessions import UserCategorySessionService

user_session_router = APIRouter()


@user_session_router.get("/get")
async def get_sessions(
    status: SessionStatus,
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.get_sessions(token.get("sub"), status.value)


@user_session_router.post("/create")
async def create_session(
    req: SessionCreateReq,
    bg_tasks: BackgroundTasks,
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.create_session(bg_tasks, token.get("sub"), req)


@user_session_router.get("/{session_id}")
async def get_session_by_id(
    session_id: str,
    offset: int = 0,
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.get_session_by_id(session_id, offset)


@user_session_router.patch("/sessions/{session_id}/day-plan/{day_plan_id}")
async def update_session_day_plan(
    session_id: str,
    day_plan_id: str,
    req: DayPlanUpdate,
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.update_dayplan(session_id, day_plan_id, req)


@user_session_router.get("/compete/{session_id}")
async def compete_session(
    session_id: str,
    weight_after: float,
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.complete_session(
        session_id, token.get("sub"), weight_after
    )

@user_session_router.get("/result/{session_id}")
async def get_result_session(
    session_id: str,
    token: dict = Depends(get_current_user),
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.get_result_session(
        session_id, token.get("sub"), 
    )




@user_session_router.get("/generate-pdf/{session_id}")
async def generate_pdf(
    session_id: str,
    session_service: UserCategorySessionService = Depends(
        UserCategorySessionService),
):
    return await session_service.generate_pdf(session_id)
