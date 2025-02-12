

import datetime
import json
from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException
from src.models.category import Category
from src.schemas.req.category import CategoryCreateReq
from src.models.sessions import DayPlan, DayStatus, UserCategorySession
from src.schemas.req.sessions import SessionCreateReq

from src.models.user import User, PhysicalData
from src.helpers.jwt_handler import JWT
from src.helpers.password import PasswordHandler
from src.helpers.ai import AI
from src.helpers.prompts.ai_schedule import get_ai_schedule_prompts

from fastapi.encoders import jsonable_encoder
from bson import ObjectId

from t import generate_full_schedule



class UserCategorySessionService:
    
    async def get_sessions(self,user_id:str):
        user = await User.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        sessions = await UserCategorySession.find({"user_id": ObjectId(user_id)}).to_list()
        return sessions
    

    async def handle_ai_response(self, user_id: str, req: SessionCreateReq):
        print("Creating session")

        # Проверяем пользователя
        user = await User.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверяем категорию
        category = await Category.find_one({"_id": ObjectId(req.category_id)})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Запрашиваем AI генерацию
        plan_data = await generate_full_schedule(
            user, category.name, req.goal, req.comments, req.duration
        )

        # Создаем день за днем
        day_plans = []
        for month in plan_data["months"]:
            for week in month["weeks"]:
                for day in week["days"]:
                    day_plan = DayPlan(
                        date=datetime.datetime.strptime(day["date"], "%Y-%m-%d"),
                        meals=day["meals"],
                        workout=day["workout"],
                        total_calories=day["total_calories"],
                        status=DayStatus.NOT_DONE,
                    )
                    await day_plan.insert()
                    day_plans.append(day_plan)

        # Создаем сессию пользователя
        session = UserCategorySession(
            user=user,
            category=category,
            goal=req.goal,
            progress=0.0,
            comments=req.comments,
            ai_generated_plan_table=day_plans,
            status="active",
        )

        await session.insert()
        print("✅ План сохранен в БД!")

    

    
    async def create_session(self,bg_task:BackgroundTasks, user_id: str, req: SessionCreateReq):
        bg_task.add_task(self.handle_ai_response, user_id, req)
        return {"message": "Session creation in progress"}
