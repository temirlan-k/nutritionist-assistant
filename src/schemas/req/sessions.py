from typing import Dict, List, Optional

from pydantic import BaseModel

from src.models.sessions import DayStatus


class SessionCreateReq(BaseModel):
    category_id: str
    goal: str
    duration: int
    comments: str


class DayPlanUpdate(BaseModel):
    meals: Optional[List[Dict]] = None
    workout: Optional[List[Dict]] = None
    total_calories: Optional[int] = None
    total_calories_burned: Optional[int] = None
    status: Optional[DayStatus] = None

    class Config:
        orm_mode = True
