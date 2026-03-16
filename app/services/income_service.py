from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models.income_model import IncomeType, Income, IncomeGrowth
from app.models.audit_model import AuditModel
from dotenv import load_dotenv
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class IncomeTypeService:

    async def add_income_type(db, data, user_id):
        income_type = await IncomeType.get_by_name(db, data.name, data.property_id)
        if income_type:
            logger.error("IncomeTypeService: income type is already exist with this name and property_id")
            raise HTTPException(500, "IncomeTypeService: income type is already exist with this name and property_id")
        
        new_income_type = IncomeType(
            property_id = data.property_id,
            name = data.name,
        )
        db.add(new_income_type)
        await db.flush() 
        logger.info("IncomeTypeService: New income type log added successfully.")
        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Income Type Management",
            object_id = str(new_income_type.id)
        )

        logger.info("IncomeTypeService: Audit log added successfully.")
        await db.commit()
        await db.refresh(new_income_type)

        return new_income_type
    

    async def update_income_type(db, id, data, user_id):
        income_type = await IncomeType.get_by_id(db, id, data.property_id)
        if not income_type:
            logger.info("IncomeTypeService: income type not found with this type id and property_id.")
            raise HTTPException(500, "IncomeTypeService: income type not found with this type id and property_id")
        old_data = IncomeType.model_to_dict(income_type)
        if income_type.name == data.name:
            logger.info("IncomeTypeService: Provided name is already exist for this property_id and type id.")
            raise HTTPException(500, "IncomeTypeService: Provided name is already exist for this property_id and type id")
        
        if data.name is not None:
            income_type.name = data.name

        if data.property_id is not None:
            income_type.property_id = data.property_id

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Income Type Management",
            object_id = id
        )

        logger.info("IncomeTypeService: Audit data is added for this update.")
        await db.commit()
        await db.refresh(income_type)
        logger.info("IncomeTypeService: Income type data is updated successfully.")
        return income_type
    

    async def delete_income_type(db, id, property_id, user_id):
        income_type = await IncomeType.get_by_id(db, id, property_id)
        if not income_type:
            logger.error("IncomeTypeService: income type is not found with this type id and property_id")
            raise HTTPException(500, "IncomeTypeService: income type not found with this type id and property_id")
        old_data = IncomeType.model_to_dict(income_type)
        income_type.is_deleted = True
        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": False},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Income Type Management",
            object_id = id
        )

        logger.info("IncomeTypeService: Audit data is added for this delete.")
        await db.commit()
        await db.refresh(income_type)
        logger.info("IncomeTypeService: income type data deleted successfully.")
        return {
            "message":"IncomeTypeService: Income type is deleted successfully with this type id and property_id"
        }
    

    async def get_income_type_by_id(db, id, property_id):
        income_type = await IncomeType.get_by_id(db, id, property_id)
        if not income_type:
            logger.warning("IncomeTypeService: income type is not fund with this type_id and property_id")
            raise HTTPException(500, "IncomeTypeService: income type not found with this type id and property_id")
        return income_type

    async def get_all_income_type(db, property_id):
        all_types = await IncomeType.get_all_income_types(db, property_id)
        logger.info("IncomeTypeService: Income type data fetch successfully.")
        return all_types
    

    async def get_property_all_income_details(db, property_id):
        return await IncomeType.get_property_income_details(db, property_id)


class IncomeService:

    async def add_new_income(db, type_id, property_id, data, user_id):
        income = await Income.get_income_data_by_property_id_and_income_type_id(db, type_id, property_id)
        if income:
            logger.info("IncomeService: Income data already exist for this property so you can't create new one without deleting the previous one.")
            raise HTTPException(500, "IncomeService: Income data already exist for this property so you can't create new one without deleting the previous one.")
        new_income = Income(
            income_id = generate_id("income"),
            property_id = property_id,
            income_type_id = type_id,
            current_income = data.current_income,
            pro_forma_income = data.pro_forma_income,
        )
        db.add(new_income)
        await db.flush() 
        logger.info("IncomeService: Income data is added successfully.")
        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Income Management",
            object_id = new_income.income_id
        )

        logger.info("IncomeService: Audit log for the add income data is added successfully.")
        await db.commit()
        await db.refresh(new_income)

        return new_income
    
    async def update_income(db, income_id, type_id, property_id, data, user_id):
        income = await Income.get_by_id(db, income_id, type_id, property_id)
        if not income:
            logger.info("IncomeService: Income data is not found for the provided income_id, type_id, property_id.")
            raise HTTPException(500, "IncomeService: Income data not found for the provided income_id, type_id, property_id")
        old_data = IncomeType.model_to_dict(income)
        if data.current_income is not None:
            income.current_income = data.current_income

        if data.pro_forma_income is not None:
            income.pro_forma_income = data.pro_forma_income

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Income Management",
            object_id = income_id
        )

        logger.info("IncomeService: Audit data is recorded successfully for this update")
        await db.commit()
        await db.refresh(income)
        logger.info("IncomeService: income data is updated successfully.")
        return income


    async def delete_income(db, income_id, type_id, property_id, user_id):
        income = await Income.get_by_id(db, income_id, type_id, property_id)
        if not income:
            logger.info("IncomeService: Income data not found for the provided income_id, type_id, property_id")
            raise HTTPException(500, "IncomeService: Income data not found for the provided income_id, type_id, property_id")
        old_data = IncomeType.model_to_dict(income)
        income.is_deleted = True

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": False},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Income Management",
            object_id = income_id
        )

        logger.info("IncomeService: Audit data is recordded successfully for this delete")
        await db.commit()
        await db.refresh(income)
        logger.info("IncomeService: Income data is deleted for this income_id, type_id, property_id.")
        return{
            "message" : "IncomeService: Income data is deleted for this income_id, type_id, property_id."
        }
    
    
    async def get_income_data(db, income_id, type_id, property_id):
        income = await Income.get_by_id(db, income_id, type_id, property_id)
        if not income:
            logger.info("IncomeService: Income data not found for the provided income_id, type_id, property_id")
            raise HTTPException(500, "IncomeService: Income data not found for the provided income_id, type_id, property_id")
        return income
    
    async def get_all_income_by_property_id(db, property_id):
        logger.info("IncomeService: income data fetch successfully.")
        return await Income.get_income_data_by_property_id(db, property_id)
    

class IncomeGrowthService:

    # async def add_income_growth(db, income_id, data, user_id):

    #     growth_objects = []
    #     audit_objects = []
    #     if data.is_same:
    #         for year in range(1, 12):
    #             growth = IncomeGrowth(
    #                 income_id=income_id,
    #                 year=year,
    #                 growth_percentage=data.growth_percentage
    #             )
    #             db.add(growth)
    #             await db.flush() 
    #             growth_objects.append(growth)
    #             audit_log = await AuditModel.add_new_logs(
    #                 db = db,
    #                 added_by = user_id,
    #                 new_data = data.model_dump(),
    #                 old_data = None,
    #                 audit_type = "ADD",
    #                 entity_type = "Income Growth Management",
    #                 object_id = growth.id
    #             )

    #             audit_objects.append(audit_log)
    #     else:
    #         growth = IncomeGrowth(
    #             income_id=income_id,
    #             year=data.year,
    #             growth_percentage=data.growth_percentage
    #         )
    #         db.add(growth)
    #         await db.flush() 
    #         growth_objects.append(growth)
    #         audit_log = await AuditModel.add_new_logs(
    #             db = db,
    #             added_by = user_id,
    #             new_data = data.model_dump(),
    #             old_data = None,
    #             audit_type = "ADD",
    #             entity_type = "Income Growth Management",
    #             object_id = growth.id
    #         )

    #         audit_objects.append(audit_log)
    #     await db.commit()

    #     for growth in growth_objects:
    #         await db.refresh(growth)
        
    #     for audit in audit_objects:
    #         await db.refresh(audit)

    #     logger.info("IncomeGrowthService: Income growth data added successfully.")
    #     logger.info("IncomeGrowthService: Audit log info added successfully for this new income growth.")
    #     return growth_objects
    

    async def add_income_growth(db, income_id, data, user_id):

        growth_objects = []
        audit_objects = []

        try:

            # decide years
            years = range(1, 12) if data.is_same else [data.year]

            for year in years:

                # check existing
                existing = await db.execute(
                    select(IncomeGrowth).where(
                        IncomeGrowth.income_id == income_id,
                        IncomeGrowth.year == year,
                        IncomeGrowth.is_deleted == False
                    )
                )

                if existing.scalar_one_or_none():
                    continue   # skip duplicate

                growth = IncomeGrowth(
                    income_id=income_id,
                    year=year,
                    growth_percentage=data.growth_percentage
                )

                db.add(growth)
                await db.flush()  # get ID without commit
                growth_objects.append(growth)

                # create audit log
                audit_log = await AuditModel.add_new_logs(
                    db=db,
                    added_by=user_id,
                    new_data={
                        "income_id": income_id,
                        "year": year,
                        "growth_percentage": data.growth_percentage
                    },
                    old_data=None,
                    audit_type="ADD",
                    entity_type="Income Growth Management",
                    object_id=str(growth.id)
                )

                # append only if object returned
                if audit_log:
                    audit_objects.append(audit_log)

            await db.commit()

            # refresh growth records
            for growth in growth_objects:
                await db.refresh(growth)

            # refresh audit logs safely
            for audit in audit_objects:
                if audit:
                    await db.refresh(audit)

            logger.info("IncomeGrowthService: Audit data recorded for this new income data")
            logger.info("IncomeGrowthService: Income growth data added successfully")

            return growth_objects

        except Exception as e:
            await db.rollback()
            logger.error(f"IncomeGrowthService: Failed to add income growth -> {str(e)}")
            raise


    async def update_income_growth(db, id, income_id, data, user_id):
        growth = await IncomeGrowth.get_by_id(db, id, income_id)
        if not growth:
            logger.info(f"IncomeGrowthService: IncomeGrowth data is not found with id:{id}, income_id:{income_id}")
            raise HTTPException(500, f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")
        old_data = IncomeType.model_to_dict(growth)
        if data.year is not None:
            growth.year = data.year

        if data.growth_percentage is not None:
            growth.growth_percentage = data.growth_percentage

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Income Growth Management",
            object_id = str(id)
        )


        logger.info("IncomeGrowthService: Audit data added for this update in income growth.")
        await db.commit()
        await db.refresh(growth)
        logger.info("IncomeGrowthService: Income growth data is updated successfully")
        return growth
    

    async def delete_income_growth(db, id, income_id, user_id):
        growth = await IncomeGrowth.get_by_id(db, id, income_id)
        if not growth:
            logger.info(f"IncomeGrowthService: income Growth data is not found with id: {id} and income_id: {income_id}")
            raise HTTPException(500, f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")
        old_data = IncomeType.model_to_dict(growth)
        growth.is_deleted = True

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": False},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Income Growth Management",
            object_id = str(id)
        )


        logger.info("IncomeGrowthService: Audit data is successfully recorded for this delete")
        await db.commit()
        await db.refresh(growth)
        logger.info("IncomeGrowthService: Income growth data is recorded successfully.")
        return growth
    
    async def get_income_growth_by_id(db, id, income_id):
        growth = await IncomeGrowth.get_by_id(db, id, income_id)
        if not growth:
            logger.info(f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")
            raise HTTPException(500, f"IncomeGrowthService: IncomeGrowth data is not found with id: {id}, income_id: {income_id}")
        return growth


    async def get_all_the_income_growth_by_income_id(db, income_id):
        growth_all = await IncomeGrowth.get_all_income_growth(db, income_id)
        logger.info("IncomeGrowthService: IncomeGrowth data fetched successfully.")
        return growth_all
    




