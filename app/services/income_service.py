from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models.income_model import IncomeType, Income, IncomeGrowth
from dotenv import load_dotenv
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class IncomeTypeService:

    async def add_income_type(db, data):
        income_type = await IncomeType.get_by_name(db, data.name, data.property_id)
        if income_type:
            raise HTTPException(500, "IncomeTypeService: income type is already exist with this name and property_id")
        
        new_income_type = IncomeType(
            property_id = data.property_id,
            name = data.name,
        )
        db.add(new_income_type)
        await db.commit()
        await db.refresh(new_income_type)

        return new_income_type
    

    async def update_income_type(db, id, data):
        income_type = await IncomeType.get_by_id(db, id, data.property_id)
        if not income_type:
            raise HTTPException(500, "IncomeTypeService: income type not found with this type id and property_id")
        
        if income_type.name == data.name:
            raise HTTPException(500, "IncomeTypeService: Provided name is already exist for this property_id and type id")
        
        if data.name is not None:
            income_type.name = data.name

        if data.property_id is not None:
            income_type.property_id = data.property_id

        await db.commit()
        await db.refresh(income_type)
        return income_type
    

    async def delete_income_type(db, id, property_id):
        income_type = await IncomeType.get_by_id(db, id, property_id)
        if not income_type:
            raise HTTPException(500, "IncomeTypeService: income type not found with this type id and property_id")
        income_type.is_deleted = True
        await db.commit()
        await db.refresh(income_type)
        return {
            "message":"IncomeTypeService: Income type is deleted successfully with this type id and property_id"
        }
    

    async def get_income_type_by_id(db, id, property_id):
        income_type = await IncomeType.get_by_id(db, id, property_id)
        if not income_type:
            raise HTTPException(500, "IncomeTypeService: income type not found with this type id and property_id")
        return income_type

    async def get_all_income_type(db, property_id):
        all_types = await IncomeType.get_all_income_types(db, property_id)
        return all_types
    

    async def get_property_all_income_details(db, property_id):
        return await IncomeType.get_property_income_details(db, property_id)


class IncomeService:

    async def add_new_income(db, type_id, property_id, data):
        income = await Income.get_income_data_by_property_id_and_income_type_id(db, type_id, property_id)
        if income:
            raise HTTPException(500, "IncomeService: Income data already exist for this property so you can't create new one without deleting the previous one.")
        new_income = Income(
            income_id = generate_id("income"),
            property_id = property_id,
            income_type_id = type_id,
            current_income = data.current_income,
            pro_forma_income = data.pro_forma_income,
        )
        db.add(new_income)
        await db.commit()
        await db.refresh(new_income)

        return new_income
    
    async def update_income(db, income_id, type_id, property_id, data):
        income = await Income.get_by_id(db, income_id, type_id, property_id)
        if not income:
            raise HTTPException(500, "IncomeService: Income data not found for the provided income_id, type_id, property_id")

        if data.current_income is not None:
            income.current_income = data.current_income

        if data.pro_forma_income is not None:
            income.pro_forma_income = data.pro_forma_income

        await db.commit()
        await db.refresh(income)

        return income


    async def delete_income(db, income_id, type_id, property_id):
        income = await Income.get_by_id(db, income_id, type_id, property_id)
        if not income:
            raise HTTPException(500, "IncomeService: Income data not found for the provided income_id, type_id, property_id")
        
        income.is_deleted = True

        await db.commit()
        await db.refresh(income)

        return{
            "message" : "IncomeService: Income data is deleted for this income_id, type_id, property_id."
        }
    
    
    async def get_income_data(db, income_id, type_id, property_id):
        income = await Income.get_by_id(db, income_id, type_id, property_id)
        if not income:
            raise HTTPException(500, "IncomeService: Income data not found for the provided income_id, type_id, property_id")
        
        return income
    
    async def get_all_income_by_property_id(db, property_id):
        return await Income.get_income_data_by_property_id(db, property_id)
    

class IncomeGrowthService:

    async def add_income_growth(db, income_id, data):

        growth_objects = []

        if data.is_same:
            for year in range(1, 12):
                growth = IncomeGrowth(
                    income_id=income_id,
                    year=year,
                    growth_percentage=data.growth_percentage
                )
                db.add(growth)
                growth_objects.append(growth)
        else:
            growth = IncomeGrowth(
                income_id=income_id,
                year=data.year,
                growth_percentage=data.growth_percentage
            )
            db.add(growth)
            growth_objects.append(growth)

        await db.commit()

        for growth in growth_objects:
            await db.refresh(growth)

        logger.info("IncomeGrowthService: Income growth data added successfully")

        return growth_objects
    

    async def update_income_growth(db, id, income_id, data):
        growth = await IncomeGrowth.get_by_id(db, id, income_id)
        if not growth:
            raise HTTPException(500, f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")
        
        if data.year is not None:
            growth.year = data.year

        if data.growth_percentage is not None:
            growth.growth_percentage = data.growth_percentage

        await db.commit()
        await db.refresh(growth)
        logger.info("IncomeGrowthService: Income growth data is updated successfully")
        return growth
    

    async def delete_income_growth(db, id, income_id):
        growth = await IncomeGrowth.get_by_id(db, id, income_id)
        if not growth:
            raise HTTPException(500, f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")
        growth.is_deleted = True

        await db.commit()
        await db.refresh(growth)
        return growth
    
    async def get_income_growth_by_id(db, id, income_id):
        growth = await IncomeGrowth.get_by_id(db, id, income_id)
        if not growth:
            raise HTTPException(500, f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")

        return growth


    async def get_all_the_income_growth_by_income_id(db, income_id):
        growth_all = await IncomeGrowth.get_all_income_growth(db, income_id)
        return growth_all
    






