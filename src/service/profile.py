from beanie import Link, PydanticObjectId
from bson import ObjectId
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from src.models.sessions import SessionStatus, UserCategorySession
from src.helpers.jwt_handler import JWT
from src.helpers.password import PasswordHandler
from src.models.user import PhysicalData, User
from src.schemas.req.profile import PhysicalDataUpdateReq, UserProfileUpdateReq
from src.schemas.req.user import UserCreateReq, UserLoginReq


class ProfileService:

    async def get_user_by_id(self, user_id: str):
        user = await User.find_one(User.id == PydanticObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        ph_data = await PhysicalData.find_one(
            PhysicalData.id == PydanticObjectId(user.physical_data_id)
        )

        total_sessions = await UserCategorySession.find({"user_id": user_id}).count()
        active_sessions = await UserCategorySession.find({"user_id": user_id, "status": SessionStatus.ACTIVE}).count()
        completed_sessions = await UserCategorySession.find({"user_id": user_id, "status": SessionStatus.COMPLETED}).count()

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "physical_data": {
                "weight": ph_data.weight,
                "height": ph_data.height,
                "age": ph_data.age,
                "blood_sugar":ph_data.blood_sugar,
                "activity_level":ph_data.activity_level,
                "chronic_diseases":ph_data.chronic_diseases,
                "gender":ph_data.gender
            },
            "statistics": {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "completed_sessions": completed_sessions,
            },
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
                physical_data = await PhysicalData.find_one(
                    PhysicalData.id == PydanticObjectId(user.physical_data_id)
                )
                if not physical_data:
                    raise HTTPException(
                        status_code=404, detail="Physical data not found"
                    )
            else:
                physical_data = PhysicalData()

            if profile_data.physical_data.weight is not None:
                physical_data.weight = profile_data.physical_data.weight
            if profile_data.physical_data.height is not None:
                physical_data.height = profile_data.physical_data.height
            if profile_data.physical_data.age is not None:
                physical_data.age = profile_data.physical_data.age
            if profile_data.physical_data.gender is not None:
                physical_data.gender = profile_data.physical_data.gender
            if profile_data.physical_data.chronic_diseases is not None:
                physical_data.chronic_diseases = profile_data.physical_data.chronic_diseases
            if profile_data.physical_data.activity_level is not None:
                physical_data.activity_level = profile_data.physical_data.activity_level
                

            await physical_data.save()
            user.physical_data_id = str(physical_data.id)

        await user.save()
        return user
