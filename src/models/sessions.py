import datetime
from enum import Enum
from beanie import Document, Link
from typing import Dict, List, Optional


class DayStatus(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NOT_DONE = "not_done"


class DayPlan(Document):
    date: datetime.datetime
    meals: List[Dict] 
    workout: List[Dict]  
    total_calories: int
    status: DayStatus 

    class Settings:
        collection = "day_plans"

class UserCategorySession(Document):
    user: Link["User"]
    category: Link["Category"]
    goal: str  
    progress: float  
    comments: str
    ai_generated_plan_table: List[Link[DayPlan]]  
    session_start: datetime.datetime = datetime.datetime.utcnow()
    session_end: Optional[datetime.datetime] = None
    status: str 

    class Settings:
        collection = "user_category_sessions"
