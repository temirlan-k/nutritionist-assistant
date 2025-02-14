from datetime import datetime
from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException
from typing import List, Dict, Any, Optional
from logging import getLogger
from src.models.category import Category
from src.models.sessions import DayPlan, DayStatus, SessionStatus, UserCategorySession
from src.models.user import PhysicalData, User
from src.helpers.ai_schedule import AIScheduleGenerator
from src.schemas.req.sessions import DayPlanUpdate, SessionCreateReq

logger = getLogger(__name__)

class UserCategorySessionService:
    def __init__(self):
        self.schedule_generator = AIScheduleGenerator()

    async def _update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update session status and timestamps."""
        try:
            session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
            if session:
                session.status = status
                session.last_updated = datetime.utcnow()
                
                if status == SessionStatus.ACTIVE:
                    session.session_end = datetime.utcnow()
                
                if error_message:
                    session.error_message = error_message
                    
                await session.save()
                logger.info(f"Session {session_id} status updated to: {status}")
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            raise

    async def process_weekly_schedule(
        self,
        week_data: Dict[str, Any],
        session_id: str
    ) -> List[DayPlan]:
        """Process weekly schedule data into DayPlan objects."""
        day_plans = []
        
        try:
            print("Processing week data...")
            week = week_data["week"]
            month = week_data["month"]
            for day in week_data["days"]:
                day_plan = DayPlan(
                    month=month,
                    week=week,
                    day_number=day["day_number"],
                    day_of_week=day["day_of_week"],
                    date=datetime.strptime(day["date"], "%Y-%m-%d"),
                    meals=day["meals"],
                    workout=day["workout"],
                    total_calories=day["total_calories"],
                    total_calories_burned=day.get("total_calories_burned", 0),
                    status=DayStatus.NOT_DONE
                )
                print("Inserting day plan...")
                await day_plan.insert()
                day_plans.append(day_plan)
                print("Day plan inserted.")
                
            return day_plans
            
        except Exception as e:
            logger.error(f"Error processing week data for session {session_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing schedule data: {str(e)}"
            )

    async def generate_full_schedule(
        self,
        user: User,
        category: Category,
        goal: str,
        comments: str,
        duration: int,
        session_id: str
    ) -> None:
        """Generate and save the complete training schedule."""
        try:
            await self._update_session_status(session_id, SessionStatus.PROCESSING)
            physical_data = await PhysicalData.find_one({"_id": ObjectId(user.physical_data_id)})
            print("Generating full schedule...")
            schedules = await self.schedule_generator.generate_full_schedule(
                physical_data=physical_data,
                category=category.name,
                goal=goal,
                comments=comments,
                duration=duration
            )
            print("Schedule generated.")
            print(schedules)
            session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            for week_schedule in schedules:
                day_plans = await self.process_weekly_schedule(week_schedule, session_id)
                for day_plan in day_plans:
                    if str(day_plan.id) not in session.ai_generated_plan_table_ids:
                        session.ai_generated_plan_table_ids.append(str(day_plan.id))
                session.last_updated = datetime.utcnow()
                await session.save()
            
            await self._update_session_status(session_id, SessionStatus.ACTIVE)
            
        except Exception as e:
            error_msg = f"Schedule generation failed: {str(e)}"
            logger.error(f"Session {session_id}: {error_msg}")
            await self._update_session_status(
                session_id,
                SessionStatus.FAILED,
                error_message=error_msg
            )
            raise

    async def create_session(
        self,
        bg_tasks: BackgroundTasks,
        user_id: str,
        req: SessionCreateReq
    ) -> Dict[str, str]:
        """Create a new training session and start schedule generation."""
        logger.info("🛠 Creating new training session...")
        
        try:
            user = await User.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            category = await Category.find_one({"_id": ObjectId(req.category_id)})
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
            session = UserCategorySession(
                user_id=user_id,
                category_id=req.category_id,
                goal=req.goal,
                comments=req.comments,
                ai_generated_plan_table_ids=[],
            )
            await session.insert()
            bg_tasks.add_task(self.generate_full_schedule, user, category, req.goal, req.comments, req.duration, str(session.id))
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )
        
    async def get_sessions(self, user_id: str):
        sessions = await UserCategorySession.find({"user_id": user_id}).to_list()
        return sessions
    
    async def get_session_by_id(self, session_id: str,offset:int = 0,):
        session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        day_plans = await DayPlan.find({"_id": {"$in": [ObjectId(id) for id in session.ai_generated_plan_table_ids]}}).sort("date").skip(offset).limit(7).to_list()
        print(len(day_plans))
        return day_plans
    
    async def update_dayplan(self,session_id:str ,day_plan_id: str, data: DayPlanUpdate):
        session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        day_plan = await DayPlan.get(day_plan_id)
        if not day_plan:
            raise HTTPException(status_code=404, detail="DayPlan not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(day_plan, field, value)
        await day_plan.save()
        return day_plan

    async def complete_session(self, session_id: str, user_id:str,weight_after:float,) -> Dict[str, Any]:
        session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        day_plans = await DayPlan.find({"_id": {"$in": [ObjectId(id) for id in session.ai_generated_plan_table_ids]}}).sort("date").to_list()
        user = await User.find_one({"_id": ObjectId(user_id)})
        physical_data = await PhysicalData.find_one({"_id": ObjectId(user.physical_data_id)})
        category = await Category.find_one({"_id": ObjectId(session.category_id)})

        if not user or not physical_data or not category:
            raise HTTPException(status_code=404, detail="User, physical data, or category not found")

        progress_analysis = await self.schedule_generator.analyze_progress(user, session, category, physical_data, weight_after,day_plans)
        session.status = SessionStatus.COMPLETED
        session.result = progress_analysis
        session.last_updated = datetime.utcnow()
        physical_data.weight = weight_after
        await session.save()
        return progress_analysis

    