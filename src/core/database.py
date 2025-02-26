import os
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.models.user import User, PhysicalData
from src.models.category import Category
from src.models.sessions import UserCategorySession, DayPlan

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
