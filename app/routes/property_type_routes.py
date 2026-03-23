from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.property_service import PropertyService, PropertyUnitTypeServices, PropertyUnitServices
from app.services.expense_service import ExpenseTypeService
from app.services.income_service import IncomeTypeService
from app.services.growth_service import IncomeExpanseGrowthService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.property import createPropertyType, updatePropertyType, PropertyTypeResponse
from typing import List
import logging 
logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/add/{property_id}", response_model = PropertyTypeResponse)
async def add_new_property_type(property_id: str, data: createPropertyType, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    property_type = await PropertyUnitTypeServices.add_new_property_unit_type(db, property_id, data, user_id)
    return PropertyTypeResponse.model_validate(property_type)


@router.put("/update/{property_id}/{id}", response_model = PropertyTypeResponse)
async def update_property_type( id : int, property_id: str, data: updatePropertyType, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    property_type = await PropertyUnitTypeServices.update_property_unit_type(db, id, property_id, data, user_id)
    return PropertyTypeResponse.model_validate(property_type)



@router.delete("/delete/{property_id}/{id}")
async def delete_property_type(id: int, property_id: str, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await PropertyUnitTypeServices.delete_property_unit_type(db, id, property_id, user_id)

@router.get("/get/{property_id}",  response_model = List[PropertyTypeResponse])
async def get_all_unit_type(property_id: str, db: Session = Depends(get_db)):
    property_types = await PropertyUnitTypeServices.get_all_unit_type_for_property_id(db, property_id)
    if not property_types:
            raise HTTPException(404, "property unit type not found or already deleted for this property_id or not available till now.")
    return [PropertyTypeResponse.model_validate(property_type) for property_type in property_types]


@router.get("/get/{property_id}/{id}", response_model = PropertyTypeResponse)
async def get_unit_type_by_id(id: int, property_id: str, db: Session = Depends(get_db)):
    property_type = await PropertyUnitTypeServices.get_unit_type_by_property_id_and_id(db, id, property_id)
    if not property_type:
            raise HTTPException(404, "property unit type not found or already deleted for this property_id and id.")
    return PropertyTypeResponse.model_validate(property_type)



@router.get("/get-type-summary/{property_id}")
async def get_property_income_expense(property_id: str, db: Session = Depends(get_db)):
    rent_summary = await PropertyUnitTypeServices.get_property_rent_summary(db, property_id)
    exp_summary = await ExpenseTypeService.get_expense_summary_by_property(db, property_id)
    inc_summary = await IncomeTypeService.get_income_summary_by_property(db, property_id)
    return{
        "rent_summary" : rent_summary,
        "exp_summary": exp_summary,
        "inc_summary": inc_summary
    }
    

@router.get("/income-expense-summary/export/{property_id}")
async def export_property_summary(property_id: str, db: Session = Depends(get_db)):
    rent_summary = await PropertyUnitTypeServices.get_property_rent_summary(db, property_id)
    exp_summary = await ExpenseTypeService.get_expense_summary_by_property(db, property_id)
    inc_summary = await IncomeTypeService.get_income_summary_by_property(db, property_id)

    return IncomeExpanseGrowthService.export_income_expense_to_excel(
        rent_summary=rent_summary,
        inc_summary=inc_summary,
        exp_summary=exp_summary,
    )


