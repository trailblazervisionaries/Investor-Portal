from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.fund_assist_service import FundAssistService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.fund_assist import FundAssistCreate, FundAssistUpdate, FundAssistResponse
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model = FundAssistResponse)
async def add_admin(data: FundAssistCreate, db: Session = Depends(get_db)):
    fund_assistant = await FundAssistService.create_fund_assistant(db, data)
    return FundAssistResponse.model_validate(fund_assistant)


@router.put("/update", response_model = FundAssistResponse)
async def add_admin(data: FundAssistUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    fund_assistant = await FundAssistService.update_fund_assistant(db, user_id, data)
    return FundAssistResponse.model_validate(fund_assistant)



@router.get("/me", response_model = FundAssistResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    fund_assist = await FundAssistService.get_my_info(db, user_id)
    if not fund_assist:
        raise HTTPException(404, "investor_assist data not found")
    return FundAssistResponse.model_validate(fund_assist)