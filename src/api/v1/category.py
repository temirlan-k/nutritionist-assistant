from fastapi import APIRouter, Depends

from src.core.auth_middleware import get_current_user
from src.schemas.req.category import CategoryCreateReq
from src.service.category import CategoryService

category_router = APIRouter()


@category_router.get("/categories")
async def get_categories(category_service: CategoryService = Depends(CategoryService)):
    return await category_service.get_all_categories()


@category_router.post("/create")
async def create_category(
    category_data: CategoryCreateReq,
    category_service: CategoryService = Depends(CategoryService),
):
    return await category_service.create_category(category_data)
