

from fastapi import HTTPException
from src.schemas.req.user import UserCreateReq, UserLoginReq
from src.models.user import User, PhysicalData
from src.helpers.jwt_handler import JWT
from src.helpers.password import PasswordHandler


class AuthService:


    async def create_user(self, user: UserCreateReq):
        physical_data_db = PhysicalData(**user.physical_data.model_dump())
        await physical_data_db.save()

        user_db = User(
            email=user.email,
            password=PasswordHandler.hash(user.password),
            first_name=user.first_name,
            last_name=user.last_name,
            physical_data=physical_data_db
        )
        await user_db.save()
        
        return user_db

    async def login(self, req: UserLoginReq):
        user = await User.find_one({"email": req.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not PasswordHandler.verify(user.password, req.password):
            raise HTTPException(status_code=400, detail="Invalid password")
        user_id = str(user.id)  
        return {
            'access_token': JWT.encode_access_token({"sub": user_id}),
            'refresh_token': JWT.encode_refresh_token({"sub": user_id}),
        }
    
    async def get_user_by_id(self, user_id: str):
        user = await User.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
