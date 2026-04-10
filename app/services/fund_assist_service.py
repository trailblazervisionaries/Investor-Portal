from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from app.core.utils_functions import generate_id, generate_alphanumeric_password
from sqlalchemy import select, func
from app.services.user_service import UserServices
from dotenv import load_dotenv
from app.models.fund_assist_model import FundAssistant
from app.models.address_model import Address
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.schemas.fund_assist import FundAssistCreate, FundAssistUpdate
from app.models.audit_model import AuditModel
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


UPLOAD_DIR = "uploads"


class FundAssistService:
    
    @staticmethod
    async def create_fund_assistant(db: Session,user_id: str, data: FundAssistCreate):

        # Check admin existence FIRST
        existing_fund_assistant = await FundAssistant.by_email(db, data.email)
        if existing_fund_assistant:
            logger.error("FundAssistService: Fund Assistant email already exist in database please try with another email.")
            raise HTTPException(
                status_code=400,
                detail="FundAssistService: fund assistant email already exists."
            )

        try:
            # temp_password = generate_alphanumeric_password()  # used in deployed version
            temp_password = "default_password"
            user = await UserServices.add_new_user(
                db,
                data.role,
                data.email,
                temp_password
            )

            new_fund_assist = FundAssistant(
                fund_assist_id=generate_id(data.fname),
                user_id=user.user_id,
                sirname=data.sirname,
                fname=data.fname,
                mname=data.mname,
                lname=data.lname,
                email=data.email,
                phone=data.phone,
                role=data.role,
            )
            logger.info("FundAssistService: new fund assistant is added but not commited yet")
            address = Address(
                user_id=new_fund_assist.fund_assist_id,  
                address_line_1=data.address.address_line_1,
                address_line_2=data.address.address_line_2,
                city=data.address.city,
                province=data.address.province,
                country=data.address.country,
                postal_code=data.address.postal_code,
            )
            db.add(new_fund_assist)
            await db.flush()
            db.add(address)
            await AuditModel.add_new_logs(
                db = db,
                added_by = user_id,
                new_data = data.model_dump(),
                old_data = None,
                audit_type = "ADD",
                entity_type = "Fund Growth Management",
                object_id = new_fund_assist.fund_assist_id
            )
            logger.info("FundAssistService: fund assistant Addresses are added")
            await db.commit()
            logger.info("FundAssistService: All info commited successfully :)")
            await db.refresh(new_fund_assist, ["address"])
            # MonitorAsync.deferred(
            #     MailTemplatesService.send_credentials_template,
            #     new_fund_assist.email,
            #     new_fund_assist.fname,
            #     "fund-assistant",
            #     temp_password,
            # )
            return new_fund_assist

        except IntegrityError as e:
            await db.rollback()
            logger.error("IntegrityError creating fund assistant: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error while creating fund assistant"
            )

        except Exception as e:
            await db.rollback()
            logger.exception("Unexpected error creating fund assistant")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


    @staticmethod
    async def update_fund_assistant(db, user_id: str, data: FundAssistUpdate):
        fund_assistant = await FundAssistant.get_by_fund_assist_user_id(db, user_id)

        if not fund_assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FundAssistService: fund_assistant not found"
            )
        old_data = FundAssistant.model_to_dict(fund_assistant)
        try:
            if hasattr(data, "email") and data.email is not None:
                fund_assistant.user.email = data.email
                fund_assistant.email = data.email
                db.add(fund_assistant.user)

            if hasattr(data, "role") and data.role is not None:
                fund_assistant.user.role = data.role
                fund_assistant.role = data.role

            admin_data = data.model_dump(
                exclude_unset=True,
                exclude={"address", "email", "role"}
            )

            for field, value in admin_data.items():
                setattr(fund_assistant, field, value)

            if data.address:
                address_data = data.address.model_dump(exclude_unset=True)

                if fund_assistant.address:
                    for field, value in address_data.items():
                        setattr(fund_assistant.address, field, value)
                else:
                    new_address = Address(
                        user_id=fund_assistant.fund_assist_id,
                        **address_data
                    )
                    db.add(new_address)
                    fund_assistant.address = new_address
            await AuditModel.add_new_logs(
                db = db,
                added_by = user_id,
                new_data = data.model_dump(),
                old_data = old_data,
                audit_type = "UPDATE",
                entity_type = "Fund Growth Management",
                object_id = fund_assistant.fund_assist_id
            )
            await db.commit()
            await db.refresh(fund_assistant, ["address"])
            logger.info("FundAssistService: fund_assistant data updated successfully")
            return fund_assistant

        except Exception:
            await db.rollback()
            logger.error("FundAssistService: Error updating fund_assistant detials")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating fund_assistant details"
            )
        
    @staticmethod
    async def get_my_info(db, user_id):
        return await FundAssistant.get_by_fund_assist_user_id(db, user_id)

    @staticmethod
    async def get_total_count(db):

        stmt = (
            select(func.count(FundAssistant.fund_assist_id))
            .where(FundAssistant.is_deleted == False)
        )
        result = await db.execute(stmt)
        return result.scalar()

    @staticmethod
    async def get_info_all_fund_assistant(db, skip: int = 0, limit: int = 10, deleted: bool = False):
        stmt = (
            select(FundAssistant)
            .options(joinedload(FundAssistant.address), joinedload(FundAssistant.user))
            .where(FundAssistant.is_deleted == deleted)
            .offset(skip)
            .limit(limit)
        )
        
        count_stmt = (
            select(func.count())
            .select_from(FundAssistant)
            .where(FundAssistant.is_deleted == deleted)
        )

        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        
        return result.scalars().all(), total_res.scalar() or 0



    async def get_info_and_delete(db, user_id):
        fund_assist = await FundAssistant.get_by_fund_assist_user_id(db, user_id, id)
        if not fund_assist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FundAssistService: fund_assist not found"
            )
        old_data = FundAssistant.model_to_dict(fund_assist)
        fund_assist.is_deleted = True
        fund_assist.user.is_deleted = True
        await AuditModel.add_new_logs(
                db = db,
                added_by = id,
                new_data = {"is_deleted" : True},
                old_data = old_data,
                audit_type = "DELETE",
                entity_type = "Fund Growth Management",
                object_id = fund_assist.fund_assist_id
            )
        await db.commit()
        await db.refresh(fund_assist)
        return {
            "message" : "fund_assist info data deleted successfully."
        }
    
    
    async def get_info_and_deactivate(db, user_id, id):
        fund_assist = await FundAssistant.get_by_fund_assist_user_id(db, user_id)
        if not fund_assist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FundAssistService: fund_assist not found"
            )
        old_data = FundAssistant.model_to_dict(fund_assist)
        fund_assist.is_active = False
        fund_assist.user.is_active = False

        await AuditModel.add_new_logs(
                db = db,
                added_by = id,
                new_data = {"is_active" : True},
                old_data = old_data,
                audit_type = "DEACTIVATE",
                entity_type = "Fund Growth Management",
                object_id = fund_assist.fund_assist_id
            )
        await db.commit()
        await db.refresh(fund_assist)
        return {
            "message" : "fund_assist info data deactivated successfully."
        }
    

    async def get_info_and_activate(db, user_id):
        fund_assist = await FundAssistant.get_by_fund_assist_user_id(db, user_id, id)
        if not fund_assist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FundAssistService: fund_assist not found"
            )
        old_data = FundAssistant.model_to_dict(fund_assist)
        fund_assist.is_active = True
        fund_assist.user.is_active = True
        await AuditModel.add_new_logs(
                db = db,
                added_by = id,
                new_data = {"is_active" : True},
                old_data = old_data,
                audit_type = "ACTIVATE",
                entity_type = "Fund Growth Management",
                object_id = fund_assist.fund_assist_id
            )
        await db.commit()
        await db.refresh(fund_assist)
        return {
            "message" : "fund_assist info data activated successfully."
        }
  
    

  
    
    