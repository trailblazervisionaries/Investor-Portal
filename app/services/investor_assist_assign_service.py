from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy import select
from dotenv import load_dotenv
from app.models.audit_model import AuditModel
from app.models.investor_assist_model import InvestorAssistant, InvestorAssignments
from app.models.investor_model import Investors
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class InvestorassistantAssignmentService:

    async def assign_new_assistant_to_investor(db, data, user_id):

        previous_assignment = await InvestorAssignments.get_active_assignment_by_investor(
            db, data.investor_id, data.investor_assistant_id
        )

        if previous_assignment:
            previous_assignment.is_deleted = True

        new_assignment = InvestorAssignments(
            investor_id=data.investor_id,
            investor_assistant_id=data.investor_assistant_id,
        )

        db.add(new_assignment)
        await db.flush()

        await AuditModel.add_new_logs(
            db=db,
            added_by=user_id,
            new_data=data.model_dump(),
            old_data=None,
            audit_type="ADD",
            entity_type="Investor Assistant Assignment Management",
            object_id=str(new_assignment.id)
        )

        await db.commit()

        result = await db.execute(
            select(InvestorAssignments)
            .options(
                selectinload(InvestorAssignments.investor).selectinload(Investors.assistant_assignment),
                selectinload(InvestorAssignments.investor_assistant)
            )
            .where(InvestorAssignments.id == new_assignment.id)
        )

        return result.scalar_one()
    
    async def delete_the_assignment(db, data, user_id):
        previous_assignment = await InvestorAssignments.get_active_assignment_by_investor(
            db, data.investor_id, data.investor_assistant_id
        )

        if previous_assignment:
            logger.warning(
                f"InvestorAssistantAssignmentService: "
                f"Deleting investor {data.investor_id} from assistant "
                f"{previous_assignment.investor_assistant.fname} "
                f"({previous_assignment.investor_assistant.investor_assistant_id})"
            )
            previous_assignment.is_deleted = True
        old_data = InvestorAssignments.model_to_dict(previous_assignment)
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Investor Assistant Assignment Management",
            object_id = str(previous_assignment.id)
        )
        await db.commit()
        await db.refresh(previous_assignment)
        return{
            "message ":'InvestorAssistantAssignmentService: assignment deleted successfully'
        }
    
    async def get_all_assignment_by_investor_id(db, investor_id):
        data = await InvestorAssignments.get_all_assignment_data_by_investor_id(db, investor_id)
        if not data:
            return []
            # raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_id")
        return data

    async def get_all_assign_investor_by_investor_assistant_id(db, investor_assistant_id):
        data = await InvestorAssignments.get_all_assignment_data_by_investor_assistant_id(db, investor_assistant_id)
        if not data:
            return []
            # raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_assistant_id")
        return data
    

    async def get_current_assign_by_investor_id(db, investor_id):
        data = await InvestorAssignments.get_active_assign_assist_by_investor_id(db, investor_id)
        if not data:
            return []
            # raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_id")
        return data

    async def get_current_assign_by_investor_assistant_id(db, investor_assistant_id):
        data = await InvestorAssignments.get_active_assign_investor_by_investor_assistant_id(db, investor_assistant_id)
        if not data:
            return []
            # raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_assistant_id")
        return data
    

