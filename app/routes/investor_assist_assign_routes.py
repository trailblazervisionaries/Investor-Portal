from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.investor_assist_assign_service import InvestorassistantAssignmentService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.investor_assist import AssignNewAssist, AssignAssistResponse
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()



@router.post("/add-assign", response_model = AssignAssistResponse)
async def add_new_assignment(data: AssignNewAssist, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    new_assign = await InvestorassistantAssignmentService.assign_new_assistant_to_investor(db, data, user_id)
    return AssignAssistResponse.model_validate(new_assign)


@router.delete("/delete}")
async def delete(data: AssignNewAssist, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await InvestorassistantAssignmentService.delete_the_assignment(db, data, user_id)


@router.get("/getall/assign/{investor_id}", response_model = list[AssignAssistResponse])
async def get_all_the_assistant(investor_id: str, db: Session = Depends(get_db)):
    all_assistant = await InvestorassistantAssignmentService.get_all_assignment_by_investor_id(db, investor_id)
    return [AssignAssistResponse.model_validate(assistant) for assistant in all_assistant]

@router.get("/getall/assignment/{investor_assistant_id}", response_model = list[AssignAssistResponse])
async def get_all_the_investor(investor_assistant_id: str, db: Session = Depends(get_db)):
    all_investor = await InvestorassistantAssignmentService.get_all_assign_investor_by_investor_assistant_id(db, investor_assistant_id)
    return [AssignAssistResponse.model_validate(assistant) for assistant in all_investor]



@router.get("/get/active-assign/{investor_id}", response_model = AssignAssistResponse)
async def get_all_the_assistant(investor_id: str, db: Session = Depends(get_db)):
    assistant = await InvestorassistantAssignmentService.get_current_assign_by_investor_id(db, investor_id)
    return AssignAssistResponse.model_validate(assistant)

@router.get("/getall/current-assign/{investor_assistant_id}", response_model = list[AssignAssistResponse])
async def get_all_the_investor(investor_assistant_id: str, db: Session = Depends(get_db)):
    all_investor = await InvestorassistantAssignmentService.get_current_assign_by_investor_assistant_id(db, investor_assistant_id)
    return [AssignAssistResponse.model_validate(assistant) for assistant in all_investor]








