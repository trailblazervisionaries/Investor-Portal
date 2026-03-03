from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.expense_service import ExpenseService, ExpenseTypeService, ExpenseGrowthService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.expenses import (CreateExpenseType, UpdateExpenseType, ExpenseTypeResponse, CreateExpense, 
                                UpdateExpense, ExpenseResponse, CreateExpenseGrowth, UpdateExpenseGrowth, ExpenseGrowthResponse,ExpenseAllTypeResponseInDetials)
import logging 
from typing import List
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add-exp-type", response_model = ExpenseTypeResponse)
async def add_new_expense_type(data: CreateExpenseType, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    type = await ExpenseTypeService.add_expense_type(db, data)
    return ExpenseTypeResponse.model_validate(type)



@router.put("/update-exp-type/{id}", response_model = ExpenseTypeResponse)
async def update_expense_type_by_id(id: int, data: UpdateExpenseType, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    updated_type = await ExpenseTypeService.update_expense_type(db, id, data)
    return ExpenseTypeResponse.model_validate(updated_type)


@router.delete("/del-exp-type/{property_id}/{id}")
async def delete_expense_type_by_id(property_id: str, id: int, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    return await ExpenseTypeService.delete_expense_type(db, id, property_id)

@router.get("/get-exp-type/{property_id}/{id}", response_model = ExpenseTypeResponse)
async def get_type_by_id(id: int, property_id: str, db: Session = Depends(get_db)):
    type = await ExpenseTypeService.get_expense_type_by_id(db, id, property_id)
    return ExpenseTypeResponse.model_validate(type)

@router.get("/getall-exp-type/{property_id}", response_model = List[ExpenseTypeResponse])
async def get_all_types_by_property_id(property_id: str, db: Session = Depends(get_db)):
    types = await ExpenseTypeService.get_all_expense_type(db, property_id)
    if not types:
        return []
    return [ExpenseTypeResponse.model_validate(type) for type in types]


#  most importent route
@router.get("/getall/{property_id}", response_model = List[ExpenseAllTypeResponseInDetials])
async def get_property_all_type_expense_details(property_id: str, db: Session = Depends(get_db)):
    return await ExpenseTypeService.get_property_all_expense_details(db, property_id)



#  below are the expenses routes ======================
@router.post("/add/{property_id}/{type_id}", response_model = ExpenseResponse)
async def add_new_expense(property_id: str, type_id: int, request: Request, data: CreateExpense, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    expense = await ExpenseService.add_new_expense(db, type_id, property_id, data)
    return ExpenseResponse.model_validate(expense)


@router.put("/update/{property_id}/{type_id}/{income_id}", response_model = ExpenseResponse)
async def update_expense(property_id: str, type_id: int, income_id: str, request: Request, data: UpdateExpense, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    expense = await ExpenseService.update_expense(db, income_id, type_id, property_id, data)
    return ExpenseResponse.model_validate(expense)


@router.delete("/delete/{property_id}/{type_id}/{expense_id}")
async def delete_expense_by_id(property_id: str, type_id: int, request: Request, expense_id: str, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    return await ExpenseService.delete_expense(db, expense_id, type_id, property_id)


@router.get("/get/{property_id}/{type_id}/{expense_id}", response_model = ExpenseResponse)
async def get_expense_by_id(property_id: str, type_id: int, expense_id: str, db: Session = Depends(get_db)):
    expense = await ExpenseService.get_expense_data(db, expense_id, type_id, property_id)
    return ExpenseResponse.model_validate(expense)

@router.get("/getallexpense/{property_id}", response_model = List[ExpenseResponse])
async def get_all_income_for_the_property(property_id: str, db: Session = Depends(get_db)):
    expenses = await ExpenseService.get_all_expense_by_property_id(db, property_id)
    if not expenses:
        return []
    return [ExpenseResponse.model_validate(expense) for expense in expenses]




#  below route belongs to the Expense growth ==================================


@router.post("/addgrowth/{expense_id}", response_model = List[ExpenseGrowthResponse])
async def add_new_expense_growth(expense_id: str, request: Request, data: CreateExpenseGrowth, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    growths = await ExpenseGrowthService.add_expense_growth(db, expense_id, data)
    return [ExpenseGrowthResponse.model_validate(growth) for growth in growths]


@router.put("/updategrowth/{expense_id}/{id}", response_model = ExpenseGrowthResponse)
async def update_the_expense_growth(id: int, expense_id: str, request: Request, data: UpdateExpenseGrowth, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    growth = await ExpenseGrowthService.update_expense_growth(db, id, expense_id, data)
    return ExpenseGrowthResponse.model_validate(growth)


@router.delete("/deletegrowth/{expense_id}/{id}")
async def delete_the_expense_growth(id: int, expense_id: str, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    return await ExpenseGrowthService.delete_expense_growth(db, id, expense_id)


@router.get("/getgrowth/{expense_id}/{id}", response_model = ExpenseGrowthResponse)
async def get_the_expense_growth(id: int, expense_id: str, db: Session = Depends(get_db)):
    growth = await ExpenseGrowthService.get_expense_growth_by_id(db, id, expense_id)
    return ExpenseGrowthResponse.model_validate(growth)


@router.get("/getallgrowth/{expense_id}", response_model = List[ExpenseGrowthResponse])
async def get_the_all_expense_growth(expense_id: str, db: Session = Depends(get_db)):
    all_growth = await ExpenseGrowthService.get_all_the_expense_growth_by_expense_id(db, expense_id)
    if not all_growth:
        return []
    return [ExpenseGrowthResponse.model_validate(growth) for growth in all_growth]


