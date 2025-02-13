

from beanie import Link, PydanticObjectId
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
        user = await User.find_one(User.id == PydanticObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        ph_data = await PhysicalData.find_one(PhysicalData.id == PydanticObjectId(user.physical_data_id))
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "physical_data": {
                "weight": ph_data.weight,
                "height": ph_data.height,
                "age": ph_data.age
            }
        }


    async def update_profile(self, user_id: str, profile_data: UserProfileUpdateReq):
        user = await User.find_one(User.id == PydanticObjectId(user_id))
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
            if user.physical_data_id:
                physical_data = await PhysicalData.find_one(PhysicalData.id == PydanticObjectId(user.physical_data_id))
                if not physical_data:
                    raise HTTPException(status_code=404, detail="Physical data not found")
            else:
                physical_data = PhysicalData()
            
            if profile_data.physical_data.weight is not None:
                physical_data.weight = profile_data.physical_data.weight
            if profile_data.physical_data.height is not None:
                physical_data.height = profile_data.physical_data.height
            if profile_data.physical_data.age is not None:
                physical_data.age = profile_data.physical_data.age

            await physical_data.save()
            user.physical_data_id = str(physical_data.id)  

        await user.save()
        return user
