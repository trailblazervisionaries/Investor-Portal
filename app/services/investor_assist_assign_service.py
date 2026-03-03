from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.services.user_service import UserServices
from dotenv import load_dotenv
from app.models.investor_assist_model import InvestorAssistant, InvestorAssignments
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class InvestorassistantAssignmentService:

    async def assign_new_assistant_to_investor(db, data):
        previous_assignment = await InvestorAssignments.get_active_assignment_by_investor(
            db, data.investor_id, data.investor_assistant_id
        )

        if previous_assignment:
            logger.warning(
                f"InvestorAssistantAssignmentService: "
                f"Reassigning investor {data.investor_id} from assistant "
                f"{previous_assignment.investor_assistant.fname} "
                f"({previous_assignment.investor_assistant.investor_assistant_id})"
            )
            previous_assignment.is_deleted = True

        new_assignment = InvestorAssignments(
            investor_id=data.investor_id,
            investor_assistant_id=data.investor_assistant_id,
        )

# TODO email sending functionality implemented later to send the ifo about the new assignment for the both user
        db.add(new_assignment)

        await db.commit()
        await db.refresh(new_assignment)

        return new_assignment
    
    async def delete_the_assignment(db, data):
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

        await db.commit()
        await db.refresh(previous_assignment)
        return{
            "message ":'InvestorAssistantAssignmentService: assignment deleted successfully'
        }
    
    async def get_all_assignment_by_investor_id(db, investor_id):
        data = await InvestorAssignments.get_all_assignment_data_by_investor_id(db, investor_id)
        if not data:
            raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_id")
        return data

    async def get_all_assign_investor_by_investor_assistant_id(db, investor_assistant_id):
        data = await InvestorAssignments.get_all_assignment_data_by_investor_assistant_id(db, investor_assistant_id)
        if not data:
            raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_assistant_id")
        return data
    

    async def get_current_assign_by_investor_id(db, investor_id):
        data = await InvestorAssignments.get_active_assign_assist_by_investor_id(db, investor_id)
        if not data:
            raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_id")
        return data

    async def get_current_assign_by_investor_assistant_id(db, investor_assistant_id):
        data = await InvestorAssignments.get_active_assign_investor_by_investor_assistant_id(db, investor_assistant_id)
        if not data:
            raise HTTPException("InvestorAssistantAssignmentService: No Any assisgnment found for the provided investor_assistant_id")
        return data