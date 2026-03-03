from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.services.user_service import UserServices
from dotenv import load_dotenv
from app.models.investor_assist_model import InvestorAssistant
from app.models.address_model import Address
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.schemas.investor_assist import InvestorAssistCreate, InvestorAssistUpdate
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


UPLOAD_DIR = "uploads"


class InvestorAssistService:
    
    @staticmethod
    async def create_investor_assistant(db: Session, data: InvestorAssistCreate):

        # Check admin existence FIRST
        existing_investor_assistant = await InvestorAssistant.by_email(db, data.email)
        if existing_investor_assistant:
            logger.error("InvestorAssistService: Investor Assistant email already exist in database please try with another email.")
            raise HTTPException(
                status_code=400,
                detail="InvestorAssistService: Investor Assistant email already exists."
            )

        try:
            user = await UserServices.add_new_user(
                db,
                data.role,
                data.email,
                "default_password"
            )

            new_investor_assist = InvestorAssistant(
                investor_assistant_id=generate_id(data.fname),
                user_id=user.user_id,
                sirname=data.sirname,
                fname=data.fname,
                mname=data.mname,
                lname=data.lname,
                email=data.email,
                phone=data.phone,
                role=data.role,
            )
            logger.info("InvestorAssistService: new investor assistant is added but not commited yet")
            address = Address(
                user_id=new_investor_assist.investor_assistant_id,  
                address_line_1=data.address.address_line_1,
                address_line_2=data.address.address_line_2,
                city=data.address.city,
                province=data.address.province,
                country=data.address.country,
                postal_code=data.address.postal_code,
            )
            db.add(new_investor_assist)
            db.add(address)
            logger.info("InvestorAssistService: investor assistant Addresses are added")
            await db.commit()
            logger.info("InvestorAssistService: All info commited successfully :)")
            await db.refresh(new_investor_assist, ["address"])
            # MonitorAsync.deferred(
            #     MailTemplatesService.send_credentials_template,
            #     new_investor_assist.email,
            #     new_investor_assist.fname,
            #     "investor-assistant",
            #     "default_password",
            # )
            return new_investor_assist

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
    async def update_investor_assistant(db, user_id: str, data: InvestorAssistUpdate):
        investor_assistant = await InvestorAssistant.get_by_investor_assistant_user_id(db, user_id)

        if not investor_assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="InvestorAssistService: investor_assistant not found"
            )

        try:
            if hasattr(data, "email") and data.email is not None:
                investor_assistant.user.email = data.email
                investor_assistant.email = data.email

            if hasattr(data, "role") and data.role is not None:
                investor_assistant.user.role = data.role
                investor_assistant.role = data.role

            admin_data = data.model_dump(
                exclude_unset=True,
                exclude={"address", "email", "role"}
            )

            for field, value in admin_data.items():
                setattr(investor_assistant, field, value)

            if data.address:
                address_data = data.address.model_dump(exclude_unset=True)

                if investor_assistant.address:
                    for field, value in address_data.items():
                        setattr(investor_assistant.address, field, value)
                else:
                    investor_assistant.address = Address(
                        user_id=investor_assistant.investor_assistant_id,
                        **address_data
                    )

            await db.commit()
            await db.refresh(investor_assistant, ["address"])
            logger.info("InvestorAssistService: investor_assistant data updated successfully")
            return investor_assistant

        except Exception:
            await db.rollback()
            logger.error("InvestorAssistService: Error updating investor_assistant detials")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating investor_assistant details"
            )
        


    async def get_my_info(db, user_id):
        return await InvestorAssistant.get_by_investor_assistant_user_id(db, user_id)




  
    