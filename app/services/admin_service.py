from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from app.core.utils_functions import generate_id, generate_alphanumeric_password
from sqlalchemy import select
from datetime import datetime, timedelta
from app.core.auth import create_auth_token
from app.services.user_service import UserServices
from dotenv import load_dotenv
from app.models.admin_model import AdminModel
from app.models.address_model import Address
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.schemas.admin import AdminCreate, AdminUpdate
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


UPLOAD_DIR = "uploads"


class AdminService:
    
    @staticmethod
    async def create_admin(db: Session, data: AdminCreate, request: Request):

        # Check admin existence FIRST
        existing_admin = await AdminModel.by_email(db, data.email)
        if existing_admin:
            logger.error("AdminService: Admin email already exist in database please try with another email")
            raise HTTPException(
                status_code=400,
                detail="AdminService: Admin email already exists"
            )

        try:
            # temp_password = generate_alphanumeric_password()
            temp_password = "default_password"
            user = await UserServices.add_new_user(
                db,
                data.role,
                data.email,
                temp_password
            )

            new_admin = AdminModel(
                admin_id=generate_id(data.fname),
                user_id=user.user_id,
                sirname=data.sirname,
                fname=data.fname,
                mname=data.mname,
                lname=data.lname,
                email=data.email,
                phone=data.phone,
                role=data.role,
            )
            logger.info("AdminService: new admin is added but not commited yet")
            new_admin.address = Address(
                user_id=new_admin.admin_id,  
                address_line_1=data.address.address_line_1,
                address_line_2=data.address.address_line_2,
                city=data.address.city,
                province=data.address.province,
                country=data.address.country,
                postal_code=data.address.postal_code,
            )
            db.add(new_admin)
            logger.info("AdminService: Admin Addresses are added")
            await db.commit()
            logger.info("AdminService: All info commited successfully :)")
            await db.refresh(new_admin, ["address"])

            # MonitorAsync.deferred(
            #     MailTemplatesService.send_credentials_template,
            #     new_admin.email,
            #     new_admin.fname,
            #     "admin",
            #     temp_password,
            # )
            return new_admin

        except IntegrityError as e:
            await db.rollback()
            logger.error("IntegrityError creating admin: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error while creating admin"
            )

        except Exception as e:
            await db.rollback()
            logger.exception("Unexpected error creating admin")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


    @staticmethod
    async def update_admin(db, user_id: str, data: AdminUpdate, request: Request):
        admin = await AdminModel.get_by_admin_user_id(db, user_id)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdminService: Admin not found"
            )

        try:
            if hasattr(data, "email") and data.email is not None:
                admin.user.email = data.email
                admin.email = data.email

            if hasattr(data, "role") and data.role is not None:
                admin.user.role = data.role
                admin.role = data.role

            admin_data = data.model_dump(
                exclude_unset=True,
                exclude={"address", "email", "role"}
            )

            for field, value in admin_data.items():
                setattr(admin, field, value)

            if data.address:
                address_data = data.address.model_dump(exclude_unset=True)

                if admin.address:
                    for field, value in address_data.items():
                        setattr(admin.address, field, value)
                else:
                    admin.address = Address(
                        user_id=admin.admin_id,
                        **address_data
                    )

            await db.commit()
            await db.refresh(admin, ["address"])
            logger.info("AdminService: Admin data updated successfully")
            return admin

        except Exception:
            await db.rollback()
            logger.error("AdminService: Error updating admin detials")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating admin details"
            )
        
    @staticmethod
    async def get_my_info(db, user_id):
        return await AdminModel.get_by_admin_user_id(db, user_id)





    