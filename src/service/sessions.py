from datetime import datetime
from io import BytesIO
from logging import getLogger
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from src.helpers.ai_schedule import AIScheduleGenerator
from src.models.category import Category
from src.models.sessions import (DayPlan, DayStatus, SessionStatus,
                                 UserCategorySession)
from src.models.user import PhysicalData, User
from src.schemas.req.sessions import DayPlanUpdate, SessionCreateReq

logger = getLogger(__name__)


class UserCategorySessionService:
    def __init__(self):
        self.schedule_generator = AIScheduleGenerator()

    async def _update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        error_message: Optional[str] = None,
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
                logger.info(
                    f"Session {session_id} status updated to: {status}")
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            raise

    async def process_weekly_schedule(
        self, week_data: Dict[str, Any], session_id: str
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
                    status=DayStatus.NOT_DONE,
                )
                print("Inserting day plan...")
                await day_plan.insert()
                day_plans.append(day_plan)
                print("Day plan inserted.")

            return day_plans

        except Exception as e:
            logger.error(
                f"Error processing week data for session {session_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error processing schedule data: {str(e)}"
            )

    async def generate_full_schedule(
        self,
        user: User,
        category: Category,
        goal: str,
        comments: str,
        duration: int,
        session_id: str,
    ) -> None:
        """Generate and save the complete training schedule."""
        try:
            await self._update_session_status(session_id, SessionStatus.PROCESSING)
            physical_data = await PhysicalData.find_one(
                {"_id": ObjectId(user.physical_data_id)}
            )
            print("Generating full schedule...")
            schedules = await self.schedule_generator.generate_full_schedule(
                physical_data=physical_data,
                category=category.name,
                goal=goal,
                comments=comments,
                duration=duration,
            )
            print("Schedule generated.")
            print(schedules)
            session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
            if not session:
                raise HTTPException(
                    status_code=404, detail="Session not found")

            for week_schedule in schedules:
                day_plans = await self.process_weekly_schedule(
                    week_schedule, session_id
                )
                for day_plan in day_plans:
                    if str(day_plan.id) not in session.ai_generated_plan_table_ids:
                        session.ai_generated_plan_table_ids.append(
                            str(day_plan.id))
                session.last_updated = datetime.utcnow()
                await session.save()

            await self._update_session_status(session_id, SessionStatus.ACTIVE)

        except Exception as e:
            error_msg = f"Schedule generation failed: {str(e)}"
            logger.error(f"Session {session_id}: {error_msg}")
            await self._update_session_status(
                session_id, SessionStatus.FAILED, error_message=error_msg
            )
            raise

    async def create_session(
        self, bg_tasks: BackgroundTasks, user_id: str, req: SessionCreateReq
    ) -> Dict[str, str]:
        """Create a new training session and start schedule generation."""
        logger.info("🛠 Creating new training session...")

        try:
            user = await User.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            category = await Category.find_one({"_id": ObjectId(req.category_id)})
            if not category:
                raise HTTPException(
                    status_code=404, detail="Category not found")
            session = UserCategorySession(
                user_id=user_id,
                category_id=req.category_id,
                goal=req.goal,
                comments=req.comments,
                ai_generated_plan_table_ids=[],
            )
            await session.insert()
            bg_tasks.add_task(
                self.generate_full_schedule,
                user,
                category,
                req.goal,
                req.comments,
                req.duration,
                str(session.id),
            )
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create session: {str(e)}"
            )

    async def get_sessions(self, user_id: str, status: str):
        sessions = await UserCategorySession.find({"user_id": user_id,'status':status}).to_list()
        return sessions

    async def get_session_by_id(
        self,
        session_id: str,
        offset: int = 0,
    ):
        session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        day_plans = (
            await DayPlan.find(
                {
                    "_id": {
                        "$in": [
                            ObjectId(id) for id in session.ai_generated_plan_table_ids
                        ]
                    }
                }
            )
            .sort("date")
            .skip(offset)
            .limit(7)
            .to_list()
        )
        print(len(day_plans))
        return day_plans

    async def update_dayplan(
        self, session_id: str, day_plan_id: str, data: DayPlanUpdate
    ):
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

    async def complete_session(
        self,
        session_id: str,
        user_id: str,
        weight_after: float,
    ) -> Dict[str, Any]:
        session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        day_plans = (
            await DayPlan.find(
                {
                    "_id": {
                        "$in": [
                            ObjectId(id) for id in session.ai_generated_plan_table_ids
                        ]
                    }
                }
            )
            .sort("date")
            .to_list()
        )
        user = await User.find_one({"_id": ObjectId(user_id)})
        physical_data = await PhysicalData.find_one(
            {"_id": ObjectId(user.physical_data_id)}
        )
        category = await Category.find_one({"_id": ObjectId(session.category_id)})

        if not user or not physical_data or not category:
            raise HTTPException(
                status_code=404, detail="User, physical data, or category not found"
            )

        progress_analysis = await self.schedule_generator.analyze_progress(
            user, session, category, physical_data, weight_after, day_plans
        )
        session.status = SessionStatus.COMPLETED
        session.result = progress_analysis
        session.last_updated = datetime.utcnow()
        physical_data.weight = weight_after
        await session.save()
        return progress_analysis
    

    async def get_result_session(self,session_id: str, user_id:str,):
        session = await UserCategorySession.find_one({"_id": ObjectId(session_id)})
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if user_id != session.user_id:
            raise HTTPException(status_code=403,detail='Permission denied')
        return session.result

    async def generate_pdf(self, session_id: str):
        session = await UserCategorySession.get(ObjectId(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        day_plans = await DayPlan.find(
            {
                "_id": {
                    "$in": [ObjectId(id) for id in session.ai_generated_plan_table_ids]
                }
            }
        ).to_list()
        if not day_plans:
            raise HTTPException(
                status_code=404, detail="No data found for this session"
            )

        grouped_data = {}
        for day in day_plans:
            key = (day.month, day.week)
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(day)

        # Create PDF with landscape orientation and larger page size
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )

        elements = []
        styles = getSampleStyleSheet()

        # Create a custom style for table cells
        styles.add(
            ParagraphStyle(
                name="TableCell",
                parent=styles["Normal"],
                fontSize=8,
                leading=10,
                wordWrap="CJK",  # Enable better word wrapping
            )
        )

        for (month, week), days in sorted(grouped_data.items()):
            elements.append(
                Paragraph(f"Month {month} - Week {week}", styles["Title"]))

            table_data = [
                [
                    "Day",
                    "Breakfast",
                    "Lunch",
                    "Dinner",
                    "Total\nCalories",
                    "Workout",
                    "Calories\nBurned",
                    "Status",
                ]
            ]

            for day in days:
                # Process meals with proper text wrapping
                def format_meal(meal_type):
                    meals = [m for m in day.meals if m["meal"] == meal_type]
                    if not meals:
                        return ""
                    foods = []
                    for m in meals:
                        if isinstance(m["food"], list):
                            foods.extend(m["food"])
                        else:
                            foods.append(str(m["food"]))
                    return Paragraph("\n".join(foods), styles["TableCell"])

                # Format workouts with proper text wrapping
                workouts = Paragraph(
                    "\n".join(
                        f"{w['exercise']} ({w['calories_burned']} kcal)"
                        for w in day.workout
                    ),
                    styles["TableCell"],
                )

                row = [
                    Paragraph(day.day_of_week, styles["TableCell"]),
                    format_meal("breakfast"),
                    format_meal("lunch"),
                    format_meal("dinner"),
                    Paragraph(str(day.total_calories), styles["TableCell"]),
                    workouts,
                    Paragraph(str(day.total_calories_burned),
                              styles["TableCell"]),
                    Paragraph(day.status.value, styles["TableCell"]),
                ]
                table_data.append(row)

            available_width = pdf.width
            col_widths = [
                available_width * 0.08,  # Day
                available_width * 0.17,  # Breakfast
                available_width * 0.17,  # Lunch
                available_width * 0.17,  # Dinner
                available_width * 0.08,  # Total Calories
                available_width * 0.20,  # Workout
                available_width * 0.08,  # Calories Burned
                available_width * 0.05,  # Status
            ]

            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Align text to top
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )

            elements.append(table)
            elements.append(Spacer(1, 12))

        if session.result:
            elements.append(Paragraph("Summary", styles["Title"]))
            elements.append(
                Paragraph(
                    session.result.get("summary", "No summary available"),
                    styles["Normal"],
                )
            )

        pdf.build(elements)
        buffer.seek(0)
        return Response(
            buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=meal_plan.pdf"},
        )
