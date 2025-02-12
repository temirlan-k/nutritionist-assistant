import os
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.models.user import User,PhysicalData
from src.models.category import Category
from src.models.sessions import UserCategorySession,DayPlan

async def init_db():
    client = AsyncIOMotorClient('mongodb://mongodb:27017/nutrition')
    
    await init_beanie(database=client.nutrition, document_models=[User,PhysicalData,Category,UserCategorySession,DayPlan])