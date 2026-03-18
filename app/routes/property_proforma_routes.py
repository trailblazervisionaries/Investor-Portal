"""
Routes for Property Pro-forma Calculations based on Excel Model
Implements: 10-Year Projections, Rent Roll, Growth Assumptions
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.property_proforma_service import PropertyPerformaService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.property import PropertyResponse
import logging 

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/get-info/{property_id}")
async def get_all_info(property_id: str, db: Session = Depends(get_db)):
    return await PropertyPerformaService.get_all_property_info(db, property_id)


@router.get("/get-revenue/{property_id}")
async def get_all_revenue_detials(property_id: str, db: Session = Depends(get_db)):
    return await PropertyPerformaService.get_all_revenue(db, property_id)

@router.get("/get-expense/{property_id}")
async def get_all_expense_detials(property_id: str, db: Session = Depends(get_db)):
    return await PropertyPerformaService.calculate_all_expenses(db, property_id)


@router.get("/get-performa-summary/{property_id}")
async def get_all_performa_summary_detials(property_id: str, db: Session = Depends(get_db)):
    return await PropertyPerformaService.get_noi_opex_and_other_detials(db, property_id)

@router.get("/get-rent-summary/{property_id}")
async def get_all_rent_detials(property_id: str, db: Session = Depends(get_db)):
    return await PropertyPerformaService.get_performa_rent_per_year(db, property_id)


@router.get("/get-cashflow/{property_id}")
async def get_all_cashflow(property_id: str, db:Session = Depends(get_db)):
    return await PropertyPerformaService.get_year_wise_cashflow(db, property_id)


@router.get("/get-overall-summary/{property_id}")
async def get_all_summary_detials(property_id: str, db: Session = Depends(get_db)):
    return await PropertyPerformaService.get_overall_performa_sumary(db, property_id)







