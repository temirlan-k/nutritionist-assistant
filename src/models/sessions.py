import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from beanie import Document, before_event
from bson import ObjectId


class DayStatus(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NOT_DONE = "not_done"


class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ACTIVE = "active"
    FAILED = "failed"


class DayPlan(Document):
    month: Optional[str | int | None] = None
    week: Optional[str | int | None] = None
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
    user_id: str  
    category_id: str 
    goal: str
    progress: float = 0.0
    comments: str
    ai_generated_plan_table_ids: List[str] 
    session_start: datetime.datetime = datetime.datetime.utcnow()
    session_end: Optional[datetime.datetime] = None
    status: SessionStatus = SessionStatus.PENDING
    error_message: Optional[str] = None
    last_updated: datetime.datetime = datetime.datetime.utcnow()
    result: Optional[Any] = None

    class Settings:
        collection = "user_category_sessions"
