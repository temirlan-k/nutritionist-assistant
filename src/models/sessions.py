from beanie import Document, before_event
from typing import List, Dict, Optional
from enum import Enum
import datetime
from bson import ObjectId


class DayStatus(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NOT_DONE = "not_done"

class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ACTIVE = "active"
    FAILED = "failed"

class DayPlan(Document):
    week:str|None = None
    day_number: int
    day_of_week: str
    date: datetime.datetime
    meals: List[Dict]
    workout: List[Dict]
    total_calories: int
    total_calories_burned: Optional[int] = 0
    status: DayStatus = DayStatus.NOT_DONE

    class Settings:
        collection = "day_plans"



class UserCategorySession(Document):
    user_id: str  # Просто храним ObjectId пользователя
    category_id: str  # Храним ObjectId категории
    goal: str
    progress: float = 0.0
    comments: str
    ai_generated_plan_table_ids: List[str]  # Список ObjectId для DayPlan
    session_start: datetime.datetime = datetime.datetime.utcnow()
    session_end: Optional[datetime.datetime] = None
    status: SessionStatus = SessionStatus.PENDING
    error_message: Optional[str] = None
    last_updated: datetime.datetime = datetime.datetime.utcnow()

    class Settings:
        collection = "user_category_sessions"
