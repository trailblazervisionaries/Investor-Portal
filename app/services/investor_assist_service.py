from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from app.core.utils_functions import generate_id, generate_alphanumeric_password
from sqlalchemy import select, func
from app.services.user_service import UserServices
from dotenv import load_dotenv
from app.models.investor_assist_model import InvestorAssistant, InvestorAssignments
from app.models.address_model import Address
from app.models.leads import Leads
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.schemas.investor_assist import InvestorAssistCreate, InvestorAssistUpdate
from app.services.property_service import PropertyService
from app.models.audit_model import  AuditModel
import logging

load_dotenv()
logger = logging.getLogger(__name__)


UPLOAD_DIR = "uploads"


class InvestorAssistService:
    
    @staticmethod
    async def create_investor_assistant(db: Session, data: InvestorAssistCreate, user_id):

        # Check admin existence FIRST
        existing_investor_assistant = await InvestorAssistant.by_email(db, data.email)
        if existing_investor_assistant:
            logger.error("InvestorAssistService: Investor Assistant email already exist in database please try with another email.")
            raise HTTPException(
                status_code=400,
                detail="InvestorAssistService: Investor Assistant email already exists."
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
            #     temp_password,
            # )
            await AuditModel.add_new_logs(
                db = db,
                added_by = user_id,
                new_data = data.model_dump(),
                old_data = None,
                audit_type = "ADD",
                entity_type = "Investor Assistant Management",
                object_id = new_investor_assist.investor_assistant_id
            )
            
            logger.info("InvestorAssistService: Audit log recorded for new Investor Assistant.")
            await db.commit()
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
        old_data = InvestorAssistant.model_to_dict(investor_assistant)
        try:
            if hasattr(data, "email") and data.email is not None:
                investor_assistant.user.email = data.email
                investor_assistant.email = data.email
                db.add(investor_assistant.user)

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
                    new_address = Address(
                        user_id=investor_assistant.investor_assistant_id,
                        **address_data
                    )
                    db.add(new_address)
                    investor_assistant.address = new_address
            await AuditModel.add_new_logs(
                db=db,
                added_by = user_id,
                new_data = data.model_dump(),
                old_data = old_data,
                audit_type = "UPDATE",
                entity_type = "Investor Assistant Management",
                object_id = investor_assistant.investor_assistant_id
            )
            
            logger.info("InvestorAssistantService: Audit log recorded for this update.")
            
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

    @staticmethod
    async def get_total_count(db):

        stmt = (
            select(func.count(InvestorAssistant.investor_assistant_id))
            .where(InvestorAssistant.is_deleted == False)
        )
        result = await db.execute(stmt)
        return result.scalar()

    async def get_all_investor_info(db, skip: int, limit: int, deleted: bool):
        return await InvestorAssistant.get_info_all_investor_assistant(db, skip=skip, limit=limit, deleted = deleted)
    
    # async def get_deleted_investor_info(db, skip: int, limit: int, deleted: bool):
    #     return await InvestorAssistant.get_info_all_investor_assistant(db, skip=skip, limit=limit, deleted = deleted)


    async def get_info_and_delete(db, user_id):
        investor_assist = await InvestorAssistant.get_by_investor_assistant_user_id(db, user_id)
        investor_assist.is_deleted = True
        investor_assist.user.is_deleted = True
        old_data = InvestorAssistant.model_to_dict(investor_assist)
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted" : True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Investor Assistant Management",
            object_id = investor_assist.investor_assistant_id
        )
        
        logger.info("InvestorAssistantService: Audit log recorded for this deleted.")
        await db.commit()
        await db.refresh(investor_assist)
        return {
            "message" : "investor_assist info data deleted successfully."
        }
    
    
    async def get_info_and_deactivate(db, user_id):
        investor_assist = await InvestorAssistant.get_by_investor_assistant_user_id(db, user_id)
        investor_assist.is_active = False
        investor_assist.user.is_active = False
        old_data = InvestorAssistant.model_to_dict(investor_assist)
        await AuditModel.add_new_logs(
            db=db,
            added_by = user_id,
            new_data = {"is_active" : False},
            old_data = old_data,
            audit_type = "DEACTIVATE",
            entity_type = "Investor Assistant Management",
            object_id = investor_assist.investor_assistant_id
        )
        
        logger.info("InvestorAssistantService: Audit log recorded for this deactivate.")
        await db.commit()
        await db.refresh(investor_assist)
        return {
            "message" : "investor_assist info data deactivated successfully."
        }
    

    async def get_info_and_activate(db, user_id):
        investor_assist = await InvestorAssistant.get_by_investor_assistant_user_id(db, user_id)
        investor_assist.is_active = True
        investor_assist.user.is_active = True
        old_data = InvestorAssistant.model_to_dict(investor_assist)
        await AuditModel.add_new_logs(
            db =db,
            added_by = user_id,
            new_data = {"is_active" : True},
            old_data = old_data,
            audit_type = "ACTIVATE",
            entity_type = "Investor Assistant Management",
            object_id = investor_assist.investor_assistant_id
        )
        
        logger.info("InvestorAssistantService: Audit log recorded for this activate.")
        await db.commit()
        await db.refresh(investor_assist)
        return {
            "message" : "investor_assist info data activated successfully."
        }
  
    
    async def get_assistant_name_id(db):
        stmt = select(
            InvestorAssistant.investor_assistant_id,
            InvestorAssistant.user_id,
            InvestorAssistant.fname,
            InvestorAssistant.mname,
            InvestorAssistant.lname
        ).where(
            InvestorAssistant.is_deleted.is_(False),
            InvestorAssistant.is_active.is_(True)
        )

        result = await db.execute(stmt)

        return [
            {
                "investor_assistant_id": row.investor_assistant_id,
                "user_id": row.user_id,
                "fname": row.fname,
                "mname": row.mname,
                "lname": row.lname,
            }
            for row in result.all()
        ] 
    

    async def get_total_leads_investor_data(db, assistant_id):
        properties = await PropertyService.get_property_statistics(db)
        lead = await Leads.get_lead_count_by_assistant(db, assistant_id)
        investor =  await InvestorAssignments.get_investor_count_by_assistant(db, assistant_id)
        return {
            "total_leads": lead,
            "total_investor": investor,
            "properties": properties
        }