from pydantic import BaseModel


class CategoryCreateReq(BaseModel):
    name: str
    description: str
