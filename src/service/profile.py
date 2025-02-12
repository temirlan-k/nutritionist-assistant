

from beanie import Link
from bson import ObjectId
from fastapi import HTTPException
from src.schemas.req.profile import UserProfileUpdateReq, PhysicalDataUpdateReq
from src.schemas.req.user import UserCreateReq, UserLoginReq
from src.models.user import User, PhysicalData
from src.helpers.jwt_handler import JWT
from src.helpers.password import PasswordHandler

from fastapi.encoders import jsonable_encoder
class ProfileService:

    async def get_user_by_id(self, user_id: str):
        user = await User.find_one({"_id": ObjectId(user_id)})
        return user
    async def update_profile(self,user_id:str, profile_data: UserProfileUpdateReq):
        user = await User.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if profile_data.first_name is not None:
            user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            user.last_name = profile_data.last_name
        if profile_data.email is not None:
            user.email = profile_data.email
        if profile_data.password is not None:
            user.password = PasswordHandler.hash(profile_data.password)  

        if profile_data.physical_data:
            physical_data = user.physical_data or PhysicalData() 
            if profile_data.physical_data.weight is not None:
                physical_data.weight = profile_data.physical_data.weight
            if profile_data.physical_data.height is not None:
                physical_data.height = profile_data.physical_data.height
            if profile_data.physical_data.age is not None:
                physical_data.age = profile_data.physical_data.age
            if profile_data.physical_data.blood_sugar is not None:
                physical_data.blood_sugar = profile_data.physical_data.blood_sugar

            await physical_data.save()
            user.physical_data = physical_data  

        await user.save()

        return user  