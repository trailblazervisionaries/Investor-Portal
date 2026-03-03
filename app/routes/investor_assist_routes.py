from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.investor_assist_service import InvestorAssistService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.investor_assist import InvestorAssistCreate, InvestorAssistUpdate, InvestorAssistResponse
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model = InvestorAssistResponse)
async def add_admin(data: InvestorAssistCreate, db: Session = Depends(get_db)):
    investor_assistant = await InvestorAssistService.create_investor_assistant(db, data)
    return InvestorAssistResponse.model_validate(investor_assistant)


@router.put("/update", response_model = InvestorAssistResponse)
async def add_admin(data: InvestorAssistUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor_assistant = await InvestorAssistService.update_investor_assistant(db, user_id, data)
    return InvestorAssistResponse.model_validate(investor_assistant)


@router.get("/me", response_model = InvestorAssistResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor_assist = await InvestorAssistService.get_my_info(db, user_id)
    if not investor_assist:
        raise HTTPException(404, "investor_assist data not found")
    return InvestorAssistResponse.model_validate(investor_assist)


