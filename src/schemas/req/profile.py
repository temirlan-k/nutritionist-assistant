from typing import Optional

from pydantic import BaseModel, EmailStr, constr


class PhysicalDataUpdateReq(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    blood_sugar: Optional[float] = None


class UserProfileUpdateReq(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=6)] = None
    physical_data: Optional[PhysicalDataUpdateReq] = None
