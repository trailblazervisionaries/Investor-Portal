from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.income_service import IncomeService, IncomeTypeService, IncomeGrowthService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.income import (CreateIncomeType, UpdateIncomeType, IncomeTypeResponse, CreateIncome, 
                                UpdateIncome, IncomeResponse, CreateIncomeGrowth, UpdateIncomeGrowth, IncomeGrowthResponse)
import logging 
from typing import List
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add-inc-type", response_model = IncomeTypeResponse)
async def add_new_income_type(data: CreateIncomeType, db: Session = Depends(get_db)):
    type = await IncomeTypeService.add_income_type(db, data)
    return IncomeTypeResponse.model_validate(type)


@router.put("/update-inc-type/{id}", response_model = IncomeTypeResponse)
async def update_income_type_by_id(id: int, data: UpdateIncomeType, db: Session = Depends(get_db)):
    updated_type = await IncomeTypeService.update_income_type(db, id, data)
    return IncomeTypeResponse.model_validate(updated_type)


@router.delete("/del-inc-type/{property_id}/{id}")
async def delete_income_type_by_id(property_id: str, id: int, db: Session = Depends(get_db)):
    return await IncomeTypeService.delete_income_type(db, id, property_id)

@router.get("/get-inc-type/{property_id}/{id}", response_model = IncomeTypeResponse)
async def get_type_by_id(id: int, property_id: str, db: Session = Depends(get_db)):
    type = await IncomeTypeService.get_income_type_by_id(db, id, property_id)
    return IncomeTypeResponse.model_validate(type)

@router.get("/getall-inc-type/{property_id}", response_model = List[IncomeTypeResponse])
async def get_all_types_by_property_id(property_id: str, db: Session = Depends(get_db)):
    types = await IncomeTypeService.get_all_income_type(db, property_id)
    if not types:
        return []
    return [IncomeTypeResponse.model_validate(type) for type in types]


#  most importent route
@router.get("/getall/{property_id}")
async def get_property_all_type_income_details(property_id: str, db: Session = Depends(get_db)):
    return await IncomeTypeService.get_property_all_income_details(db, property_id)


#  below are the incomes routes ======================
@router.post("/add/{property_id}/{type_id}", response_model = IncomeResponse)
async def add_new_income(property_id: str, type_id: int, data: CreateIncome, db: Session = Depends(get_db)):
    income = await IncomeService.add_new_income(db, type_id, property_id, data)
    return IncomeResponse.model_validate(income)


@router.put("/update/{property_id}/{type_id}/{income_id}", response_model = IncomeResponse)
async def update_income(property_id: str, type_id: int, income_id: str, data: UpdateIncome, db: Session = Depends(get_db)):
    income = await IncomeService.update_income(db, income_id, type_id, property_id, data)
    return IncomeResponse.model_validate(income)


@router.delete("/delete/{property_id}/{type_id}/{income_id}")
async def delete_income_by_id(property_id: str, type_id: int, income_id: str, db: Session = Depends(get_db)):
    return await IncomeService.delete_income(db, income_id, type_id, property_id)


@router.get("/get/{property_id}/{type_id}/{income_id}", response_model = IncomeResponse)
async def get_income_by_id(property_id: str, type_id: int, income_id: str, db: Session = Depends(get_db)):
    income = await IncomeService.get_income_data(db, income_id, type_id, property_id)
    return IncomeResponse.model_validate(income)

@router.get("/getallincome/{property_id}", response_model = List[IncomeResponse])
async def get_all_income_for_the_property(property_id: str, db: Session = Depends(get_db)):
    incomes = await IncomeService.get_all_income_by_property_id(db, property_id)
    if not incomes:
        return []
    return [IncomeResponse.model_validate(income) for income in incomes]




#  below route belongs to the income growth ==================================


@router.post("/addgrowth/{income_id}", response_model = List[IncomeGrowthResponse])
async def add_new_income_growth(income_id: str, data: CreateIncomeGrowth, db: Session = Depends(get_db)):
    growths = await IncomeGrowthService.add_income_growth(db, income_id, data)
    return [IncomeGrowthResponse.model_validate(growth) for growth in growths]


@router.put("/updategrowth/{income_id}/{id}", response_model = IncomeGrowthResponse)
async def update_the_income_growth(id: int, income_id: str, data: UpdateIncomeGrowth, db: Session = Depends(get_db)):
    growth = await IncomeGrowthService.update_income_growth(db, id, income_id, data)
    return IncomeGrowthResponse.model_validate(growth)


@router.delete("/deletegrowth/{income_id}/{id}")
async def delete_the_income_growth(id: int, income_id: str, db: Session = Depends(get_db)):
    return await IncomeGrowthService.delete_income_growth(db, id, income_id)


@router.get("/getgrowth/{income_id}/{id}", response_model = IncomeGrowthResponse)
async def get_the_income_growth(id: int, income_id: str, db: Session = Depends(get_db)):
    growth = await IncomeGrowthService.get_income_growth_by_id(db, id, income_id)
    return IncomeGrowthResponse.model_validate(growth)


@router.get("/getallgrowth/{income_id}", response_model = List[IncomeGrowthResponse])
async def get_the_all_income_growth(income_id: str, db: Session = Depends(get_db)):
    all_growth = await IncomeGrowthService.get_all_the_income_growth_by_income_id(db, income_id)
    if not all_growth:
        return []
    return [IncomeGrowthResponse.model_validate(growth) for growth in all_growth]


