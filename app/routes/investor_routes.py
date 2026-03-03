from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.investor_service import InvestorService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.investor import InvestorCreate, InvestorUpdate, InvestorResponse
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model = InvestorResponse)
async def add_admin(data: InvestorCreate, db: Session = Depends(get_db)):
    investor = await InvestorService.create_investor(db, data)
    return InvestorResponse.model_validate(investor)


@router.put("/update", response_model = InvestorResponse)
async def add_admin(data: InvestorUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor = await InvestorService.update_investor(db, user_id, data)
    return InvestorResponse.model_validate(investor)


@router.get("/me", response_model = InvestorResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor = await InvestorService.get_my_info(db, user_id)
    if not investor:
        raise HTTPException(404, "Investor data not found")
    return InvestorResponse.model_validate(investor)