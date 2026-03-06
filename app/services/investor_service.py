from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.services.user_service import UserServices
from dotenv import load_dotenv
from app.models.investor_model import Investors
from app.models.address_model import Address
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.schemas.investor import InvestorCreate, InvestorUpdate
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


UPLOAD_DIR = "uploads"


class InvestorService:
    
    @staticmethod
    async def create_investor(db: Session, user_id: str, data: InvestorCreate):

        # Check admin existence FIRST
        existing_investor = await Investors.by_email(db, data.email)
        if existing_investor:
            logger.error("InvestorService: Investor email already exist in database please try with another email.")
            raise HTTPException(
                status_code=400,
                detail="InvestorService: Investor email already exists."
            )

        try:
            user = await UserServices.add_new_user(
                db,
                data.role,
                data.email,
                "default_password"
            )

            new_investor = Investors(
                investor_id=generate_id(data.fname),
                user_id=user.user_id,
                added_by = user_id,
                sirname=data.sirname,
                fname=data.fname,
                mname=data.mname,
                lname=data.lname,
                email=data.email,
                phone=data.phone,
                role=data.role,
            )
            logger.info("InvestorService: new investor is added but not commited yet")
            address = Address(
                user_id=new_investor.investor_id,  
                address_line_1=data.address.address_line_1,
                address_line_2=data.address.address_line_2,
                city=data.address.city,
                province=data.address.province,
                country=data.address.country,
                postal_code=data.address.postal_code,
            )
            db.add(new_investor)
            db.add(address)
            logger.info("InvestorService: investor Addresses are added")
            await db.commit()
            logger.info("InvestorService: All info commited successfully :)")
            await db.refresh(new_investor, ["address"])
            # MonitorAsync.deferred(
            #     MailTemplatesService.send_credentials_template,
            #     new_investor.email,
            #     new_investor.fname,
            #     "investor-assistant",
            #     "default_password",
            # )
            return new_investor

        except IntegrityError as e:
            await db.rollback()
            logger.error("IntegrityError creating investor assistant: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error while creating investor assistant"
            )

        except Exception as e:
            await db.rollback()
            logger.exception("Unexpected error creating investor assistant")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


    @staticmethod
    async def update_investor(db, user_id: str, data: InvestorUpdate):
        investor = await Investors.get_by_investor_user_id(db, user_id)

        if not investor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="InvestorService: investor not found"
            )

        try:
            if hasattr(data, "email") and data.email is not None:
                investor.user.email = data.email
                investor.email = data.email

            if hasattr(data, "role") and data.role is not None:
                investor.user.role = data.role
                investor.role = data.role

            admin_data = data.model_dump(
                exclude_unset=True,
                exclude={"address", "email", "role"}
            )

            for field, value in admin_data.items():
                setattr(investor, field, value)

            if data.address:
                address_data = data.address.model_dump(exclude_unset=True)

                if investor.address:
                    for field, value in address_data.items():
                        setattr(investor.address, field, value)
                else:
                    investor.address = Address(
                        user_id=investor.investor_id,
                        **address_data
                    )

            await db.commit()
            await db.refresh(investor, ["address"])
            logger.info("InvestorService: investor data updated successfully")
            return investor

        except Exception:
            await db.rollback()
            logger.error("InvestorService: Error updating investor detials")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating investor details"
            )
        

    async def get_my_info(db, user_id):
        return await Investors.get_by_investor_user_id(db, user_id)

    async def get_all_investor_info(db, added_by):
        return await Investors.get_by_added_by_id(db, added_by)
    
    async def get_all_investor(db, skip: int, limit: int, deleted: bool):
        return await Investors.get_all_info_investors(db, skip=skip, limit=limit, deleted = deleted)


    async def get_info_and_delete(db, user_id):
        investor = await Investors.get_by_investor_user_id(db, user_id)
        investor.is_delete = True
        investor.user.is_delete = True
        await db.commit()
        await db.refresh(investor)
        return {
            "message" : "Investor info data deleted successfully."
        }
    
    
    async def get_info_and_deactivate(db, user_id):
        investor = await Investors.get_by_investor_user_id(db, user_id)
        investor.is_active = True
        investor.user.is_active = True
        await db.commit()
        await db.refresh(investor)
        return {
            "message" : "Investor info data deactivated successfully."
        }
    

    async def get_info_and_activate(db, user_id):
        investor = await Investors.get_by_investor_user_id(db, user_id)
        investor.is_active = True
        investor.user.is_active = True
        await db.commit()
        await db.refresh(investor)
        return {
            "message" : "Investor info data activated successfully."
        }
  
    

    