from bson import ObjectId
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from src.helpers.jwt_handler import JWT
from src.helpers.password import PasswordHandler
from src.models.category import Category
from src.models.user import PhysicalData, User
from src.schemas.req.category import CategoryCreateReq


class CategoryService:

    async def get_all_categories(
        self,
    ):
        categories = await Category.find().to_list()
        return categories

    async def create_category(self, category_data: CategoryCreateReq):
        category = Category(**category_data.model_dump())
        await category.save()
        return category
