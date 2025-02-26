import datetime
from typing import Optional

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel


class PhysicalData(Document):
    weight: float
    height: float
    age: int
    created_at: datetime.datetime = datetime.datetime.utcnow()

    class Settings:
        collection = "physical_data"


class User(Document):
    first_name: str
    last_name: str
    email: str
    password: str
    physical_data_id: Optional[str]

    class Settings:
        collection = "users"
