import datetime
from beanie import Document, Link
from typing import List, Optional

class User(Document):
    first_name: str
    last_name: str
    email: str
    password: str
    physical_data: Link["PhysicalData"]


    class Settings:
        collection = "users"

        
class PhysicalData(Document):
    weight: float
    height: float
    age: int
    created_at: datetime.datetime = datetime.datetime.utcnow()

    class Settings:
        collection = "physical_data"


User.model_rebuild()
PhysicalData.model_rebuild()
