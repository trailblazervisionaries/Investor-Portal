from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.investor_investment_service import InvestorInvestmentServices
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.investor import InvestorInvestmentCreate, InvestorInvestmentsUpdate, InvestorInvestmentsResponse
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/allocate/{investor_id}", response_model = InvestorInvestmentsResponse)
async def allocate_the_new_investment_to_investor(investor_id: str, data: InvestorInvestmentCreate, db: Session = Depends(get_db)):
    new_alloc_investment = await InvestorInvestmentServices.add_new_investment(db, investor_id, data)
    return InvestorInvestmentsResponse.model_validate(new_alloc_investment)


@router.put("/update/{investor_id}/{id}", response_model = InvestorInvestmentsResponse)
async def allocate_the_new_investment_to_investor(id: int, investor_id: str, data: InvestorInvestmentsUpdate, db: Session = Depends(get_db)):
    new_alloc_investment = await InvestorInvestmentServices.update_investment(db, id, investor_id, data)
    return InvestorInvestmentsResponse.model_validate(new_alloc_investment)


@router.put("status/{investor_id}/{id}/{status}")
async def update_the_status_of_investemnt(id: int, investor_id: str, status: str, db: Session = Depends(get_db)):
    return await InvestorInvestmentServices.update_the_investment_status(db, id, investor_id, status)

@router.get("get/{investor_id}/{id}", response_model = InvestorInvestmentsResponse)
async def get_info_of_investemnt(id: int, investor_id: str, db: Session = Depends(get_db)):
    investment_info =  await InvestorInvestmentServices.get_the_investment_info(db, id, investor_id)
    return InvestorInvestmentsResponse.model_validate(investment_info)


@router.get("getall/{investor_id}", response_model = InvestorInvestmentsResponse)
async def get_info_of_all_investemnts(investor_id: str, db: Session = Depends(get_db)):
    all_investment_info =  await InvestorInvestmentServices.get_all_investment_info_for_by_investor_id(db, investor_id)
    return [InvestorInvestmentsResponse.model_validate(investment_info) for investment_info in all_investment_info]



