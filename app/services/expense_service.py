from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models.expenses_model import ExpenseTypes, Expense, ExpenseGrowth
from app.models.audit_model import AuditModel
from dotenv import load_dotenv
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class ExpenseTypeService:

    async def add_expense_type(db, data, user_id):
        expense_type = await ExpenseTypes.get_by_name(db, data.name, data.property_id)
        if expense_type:
            logger.info("ExpenseTypesService: Expense type is already exist with this name and property_id")
            raise HTTPException(500, "ExpenseTypesService: Expense type is already exist with this name and property_id")
        
        new_expense_type = ExpenseTypes(
            property_id = data.property_id,
            name = data.name,
        )
        db.add(new_expense_type)
        await db.flush() 

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Expense Type Management",
            object_id = new_expense_type.id
        )

        logger.info("ExpenseTypeService: Audit log recorded for new expense type.")
        await db.commit()
        await db.refresh(new_expense_type)
        logger.info("ExpenseTypeService: new expense type is added successfully.")
        return new_expense_type
    

    async def update_expense_type(db, id, data, user_id):
        expense_type = await ExpenseTypes.get_by_id(db, id, data.property_id)
        if not expense_type:
            logger.info("ExpenseTypesService: Expense type not found with this type id and property_id")
            raise HTTPException(500, "ExpenseTypesService: Expense type not found with this type id and property_id")
        old_data = ExpenseTypes.model_to_dict(expense_type)
        if expense_type.name == data.name:
            logger.info("ExpenseTypesService: Provided name is already exist for this property_id and type id")
            raise HTTPException(500, "ExpenseTypesService: Provided name is already exist for this property_id and type id")
        
        if data.name is not None:
            expense_type.name = data.name

        if data.property_id is not None:
            expense_type.property_id = data.property_id

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Expense Type Management",
            object_id = id
        )

        logger.info("ExpenseTypesService: Audit data is stored for the current updation")
        await db.commit()
        await db.refresh(expense_type)
        logger.info("ExpenseTypeServices: Expense type data is updated successfully.")
        return expense_type
    

    async def delete_expense_type(db, id, property_id, user_id):
        expense_type = await ExpenseTypes.get_by_id(db, id, property_id)
        if not expense_type:
            raise HTTPException(500, "ExpenseTypesService: Expense type not found with this type id and property_id")
        old_data = ExpenseTypes.model_to_dict(expense_type)
        expense_type.is_deleted = True
        
        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Expense Type Management",
            object_id = id
        )

        logger.info("ExpenseTypeService: Audit data is added successfully for this delete")
        await db.commit()
        await db.refresh(expense_type)
        logger.info("ExpenseTypeService: Expense type deleted successfully.")
        return {
            "message":"ExpenseTypesService: Expense type is deleted successfully with this type id and property_id"
        }
    

    async def get_expense_type_by_id(db, id, property_id):
        expense_type = await ExpenseTypes.get_by_id(db, id, property_id)
        if not expense_type:
            raise HTTPException(500, "ExpenseTypesService: Expense type not found with this type id and property_id")
        return expense_type


    async def get_all_expense_type(db, property_id):
        all_types = await ExpenseTypes.get_all_expense_types(db, property_id)
        if not all_types:
            raise HTTPException(404, "ExpenseTypesService: ExpenseTypes not available till now for this property")
        return all_types
    

    async def get_property_all_expense_details(db, property_id):
        return await ExpenseTypes.get_property_expense_details(db, property_id)


class ExpenseService:

    async def add_new_expense(db, type_id, property_id, data, user_id):
        expense = await Expense.get_expense_data_by_property_id_and_expense_type_id(db, type_id, property_id)
        if expense:
            raise HTTPException(500, "ExpenseService: Expense data already exist for this property so you can't create new one without deleting the previous one.")
        new_expense = Expense(
            expense_id = generate_id("expense"),
            property_id = property_id,
            expense_type_id = type_id,
            current_expense = data.current_expense,
            pro_forma_expense = data.pro_forma_expense
        )
        db.add(new_expense)
        await db.flush() 
        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Expense Management",
            object_id = new_expense.expense_id
        )


        logger.info("ExpenseService: Audit log added for the new expense.")
        await db.commit()
        await db.refresh(new_expense)
        logger.info("ExpenseService: Expense data added successfully.")
        return new_expense
    

    async def update_expense(db, expense_id, type_id, property_id, data, user_id):
        expense = await Expense.get_by_id(db, expense_id, type_id, property_id)
        if not expense:
            logger.info("ExpenseService: Expense data not found for the provided ids")
            raise HTTPException(500, "ExpenseService: Expense data not found for the provided Expense_id, type_id, property_id")
        old_data = Expense.model_to_dict(expense)
        if data.current_expense is not None:
            expense.current_expense = data.current_expense

        if data.pro_forma_expense is not None:
            expense.pro_forma_expense = data.pro_forma_expense

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Expense Management",
            object_id = expense_id
        )

        logger.info("ExpenseService: Audit log recorded for this update successfully.")
        await db.commit()
        await db.refresh(expense)
        logger.info("ExpenseService: Expense data updated successfully.")
        return expense


    async def delete_expense(db, expense_id, type_id, property_id, user_id):
        expense = await Expense.get_by_id(db, expense_id, type_id, property_id)
        if not expense:
            raise HTTPException(500, "ExpenseService: Expense data not found for the provided Expense_id, type_id, property_id")
        old_data = Expense.model_to_dict(expense)
        expense.is_deleted = True

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Expense Management",
            object_id = expense_id
        )

        logger.info("ExpenseService: AuditLog is recorded for this delete operation")
        await db.commit()
        logger.info("ExpenseService: Expense data deleted successfully.")
        await db.refresh(expense)

        return{
            "message" : "ExpenseService: Expense data is deleted for this Expense_id, type_id, property_id."
        }
    

    async def get_expense_data(db, expense_id, type_id, property_id):
        expense = await Expense.get_by_id(db, expense_id, type_id, property_id)
        if not expense:
            raise HTTPException(500, "ExpenseService: Expense data not found for the provided Expense_id, type_id, property_id")
        
        return expense
    

    async def get_all_expense_by_property_id(db, property_id):
        return await Expense.get_expense_data_by_property_id(db, property_id)
    

class ExpenseGrowthService:

    async def add_expense_growth(db, expense_id, data, user_id):

        growth_objects = []
        audit_object = []

        if data.is_same:
            for year in range(1, 12):
                growth = ExpenseGrowth(
                    expense_id=expense_id,
                    year=year,
                    growth_percentage=data.growth_percentage
                )
                db.add(growth)
                await db.flush() 
                growth_objects.append(growth)

                audit_log = await AuditModel.add_new_logs(
                    db = db,
                    added_by = user_id,
                    new_data = { "expense_id": expense_id, "year":year, "growth_percentage":data.growth_percentage},
                    old_data = None,
                    audit_type = "ADD",
                    entity_type = "Expense Growth Management",
                    object_id = growth.id
                )

                audit_object.append(audit_log)
        else:
            growth = ExpenseGrowth(
                expense_id=expense_id,
                year=data.year,
                growth_percentage=data.growth_percentage
            )
            db.add(growth)
            await db.flush() 
            growth_objects.append(growth)
            
            audit_log = await AuditModel.add_new_logs(
                db = db,
                added_by = user_id,
                new_data = { "expense_id": expense_id, "year":data.year, "growth_percentage":data.growth_percentage},
                old_data = None,
                audit_type = "ADD",
                entity_type = "Expense Growth Management",
                object_id = growth.id
                )

            audit_object.append(audit_log)

        await db.commit()

        for growth in growth_objects:
            await db.refresh(growth)
        
        for audit in audit_object:
            await db.refresh(audit)
        logger.info("ExpenseGrowthService: Audit data recorded for this new expense data")
        logger.info("ExpenseGrowthService: Expense growth data added successfully")

        return growth_objects

    

    async def update_expense_growth(db, id, expense_id, data, user_id):
        growth = await ExpenseGrowth.get_by_id(db, id, expense_id)
        if not growth:
            logger.info(f"ExpenseGrowthService: ExpenseGrowth data is not found with id: {id}, Expense_id: {expense_id}")
            raise HTTPException(500, f"ExpenseGrowthService: ExpenseGrowth data is not found with id: {id}, Expense_id: {expense_id}")
        old_data = ExpenseGrowth.model_to_dict(growth)
        if data.year is not None:
            growth.year = data.year

        if data.growth_percentage is not None:
            growth.growth_percentage = data.growth_percentage

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = { "expense_id": expense_id, "year":data.year, "growth_percentage":data.growth_percentage},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Expense Growth Management",
            object_id = id
            )

        logger.info("ExpenseGrowthService: audit data added successfully for update")
        await db.commit()
        await db.refresh(growth)
        logger.info("ExpenseGrowthService: Expense growth data is updated successfully")
        return growth
    

    async def delete_expense_growth(db, id, expense_id, user_id):
        growth = await ExpenseGrowth.get_by_id(db, id, expense_id)
        if not growth:
            logger.info(f"ExpenseGrowthService: ExpenseGrowth data is not found with id: {id}, Expense_id: {expense_id}")
            raise HTTPException(500, f"ExpenseGrowthService: ExpenseGrowth data is not found with id: {id}, Expense_id: {expense_id}")
        old_data = ExpenseGrowth.model_to_dict(growth)
        growth.is_deleted = True

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted" : True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Expense Growth Management",
            object_id = id
        )

        logger.info("ExpenseGrowthService: Audit logs data stored successfully")
        await db.commit()
        await db.refresh(growth)
        logger.info("ExpenseGrowthService: Expense Growth data deleted successfully")
        return growth
    

    async def get_expense_growth_by_id(db, id, expense_id):
        growth = await ExpenseGrowth.get_by_id(db, id, expense_id)
        if not growth:
            raise HTTPException(500, f"ExpenseGrowthService: ExpenseGrowth data is not found with id: {id}, Expense_id: {expense_id}")

        return growth


    async def get_all_the_expense_growth_by_expense_id(db, expense_id):
        growth_all = await ExpenseGrowth.get_all_expense_growth(db, expense_id)
        return growth_all
    






