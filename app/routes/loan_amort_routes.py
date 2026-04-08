from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.loan_amortz_service import PropertyLoanService, AmortizationScheduleService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.property import (createPropertyLoan, updatePropertyLoan, PropertyLoanResponse, 
                                  createAmortzSechedule, updateAmortzSechedule, AmortzSecheduleResponse, updateMarkAmortzSchedulePayment)
import logging 
from typing import List
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/add/{property_id}", response_model = PropertyLoanResponse)
async def create_property_loan(request: Request, property_id: str, data: createPropertyLoan, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(401, "you are not authorise to perform this operation.")
    property_loan = await PropertyLoanService.add_new_loan_details(db, property_id, data, user_id)
    return PropertyLoanResponse.model_validate(property_loan)


@router.put("/update/{property_id}/{loan_id}", response_model = PropertyLoanResponse)
async def update_property_loan(request: Request, loan_id: str, property_id: str, data: updatePropertyLoan, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(401, "you are not authorise to perform this operation.")
    property_loan = await PropertyLoanService.update_loan_detials(db, loan_id, property_id, data, user_id)
    return PropertyLoanResponse.model_validate(property_loan)

@router.delete("/delete/{property_id}/{loan_id}")
async def delete_property_loan(request: Request, loan_id: str, property_id: str, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(401, "you are not authorise to perform this operation.")
    return await PropertyLoanService.delete_loan_data(db, loan_id, property_id, user_id)

@router.get("/get/{property_id}/{loan_id}", response_model = PropertyLoanResponse)
async def get_property_loan_data(request: Request, loan_id: str, property_id: str, db: Session = Depends(get_db)):
    property_loan = await PropertyLoanService.get_loan_detials_for_property(db, loan_id, property_id)
    if not property_loan:
        raise HTTPException(404, "Loan_amortz_routes: property-loan data not found for the given loan_id and property_id.")
    return PropertyLoanResponse.model_validate(property_loan)

@router.get("/getall", response_model = List[PropertyLoanResponse])
async def get_all_loans_data(request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(401, "you are not authorise to perform this operation.")
    property_loan = await PropertyLoanService.get_all_loans_details(db)
    if not property_loan:
        # raise HTTPException(404, "Loan_amortz_routes: property-loan data not found.")
        return []
    return [PropertyLoanResponse.model_validate(loan) for loan in property_loan]


@router.put("/activate-deactivate/{property_id}/{loan_id}")
async def activate_deactivate_property_loan(request: Request, loan_id: str, property_id: str, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(401, "you are not authorise to perform this operation.")
    return await PropertyLoanService.activate_deactivate_loan_data(db, loan_id, property_id, user_id)



#  routes for the loan amortization schedule --------------------------------------------------------------------------

@router.get('/amortz/getall/{property_id}/{loan_id}')
async def delete_the_amortz_schedule(request: Request, loan_id: str, property_id: str, db: Session = Depends(get_db)):
    amortz_schedules = await AmortizationScheduleService.get_all(db, loan_id, property_id)
    return amortz_schedules


@router.get('/amortz/exportall/{property_id}/{loan_id}')
async def delete_the_amortz_schedule(request: Request, loan_id: str, property_id: str, db: Session = Depends(get_db)):
    amortz_schedules = await AmortizationScheduleService.export_to_sheet(db, loan_id, property_id)
    return amortz_schedules



