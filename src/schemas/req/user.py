from pydantic import BaseModel


class PhysicalDataCreateReq(BaseModel):
    weight: float
    height: float
    age: int
    blood_sugar: float


class UserCreateReq(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    physical_data: PhysicalDataCreateReq | None = None


class UserLoginReq(BaseModel):
    email: str
    password: str
