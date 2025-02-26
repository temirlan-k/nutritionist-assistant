import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.models.category import Category
from src.models.sessions import DayPlan, UserCategorySession
from src.models.user import PhysicalData, User

client = None
db = None


async def init_db():
    global client, db
    client = AsyncIOMotorClient("mongodb://mongodb:27017/nutrition")
    db = client.nutrition
    await init_beanie(
        database=db,
        document_models=[User, PhysicalData,
                         Category, UserCategorySession, DayPlan],
    )
