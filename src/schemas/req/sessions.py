from pydantic import BaseModel

class SessionCreateReq(BaseModel):
    category_id: str
    goal: str
    duration: str
    comments: str
