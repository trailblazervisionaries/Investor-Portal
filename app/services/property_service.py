from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.audit_model import AuditModel
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from io import BytesIO
from fastapi.responses import StreamingResponse
from openpyxl.utils import get_column_letter
from decimal import Decimal, ROUND_HALF_UP
from app.models.property_model import Property, PropertyUnitType, PropertyUnit
import traceback
import time
import os
import logging


logger = logging.getLogger(__name__)
timestamp_ms = int(time.time() * 1000)

class PropertyService:

    async def add_new_property(db, user_id, data):

        new_property = Property(
            property_id = generate_id(data.name),
            added_by = user_id,
            name = data.name,
            description = data.description,
            purchase_price = data.purchase_price,
            loan_amount = data.loan_amount,
            property_type= data.property_type,
            total_area = data.total_area,
            going_cap_rate = data.going_cap_rate,
            total_investment_required = data.total_investment_required,
            available_required_for_investment = data.available_required_for_investment,
            address_line_1 = data.address_line_1,
            address_line_2 = data.address_line_2,
            city = data.city,
            province = data.province,
            country = data.country,
            postal_code = data.postal_code
        )

        db.add(new_property)
        await db.flush()
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(mode='json'),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Property Management",
            object_id = new_property.property_id
        )
        await db.commit()
        await db.refresh(new_property)
        logger.info("PropertyServices: property data is stored successfully")
        return new_property
    
    async def update_property(db, user_id, property_id, data):

        property_obj = await Property.get_by_id(db, property_id)
        if not property_obj:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property_obj)
        allowed_fields = {
            "name", "description", "purchase_price",
            "loan_amount", "going_cap_rate",
            "property_type", "total_area", "total_investment_required",
            "available_required_for_investment", "address_line_1",
            "address_line_2", "city", "province", "country", "postal_code"
        }

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(property_obj, field, value)

        property_obj.updated_by = user_id

        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(mode='json'),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property_obj.property_id
        )

        await db.commit()
        await db.refresh(property_obj)

        logger.info("PropertyServices: property data is updated successfully")

        return property_obj

    

    async def delete_property(db, property_id, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        property.is_deleted = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property deleted successfully")
        return {"message ": "PropertyServices: property deleted successfully"}


    
    # async def update_property_risk(db, property_id, risk_status, user_id):
    #     property = await Property.get_by_id(db, property_id)
    #     if not property:
    #         raise HTTPException(404, "property with this property_id is not found or already deleted")
    #     old_data = Property.model_to_dict(property)
    #     property.risk_status = risk_status
    #     await AuditModel.add_new_logs(
    #         db = db,
    #         added_by = user_id,
    #         new_data = {"risk_status": risk_status},
    #         old_data = old_data,
    #         audit_type = "UPDATE",
    #         entity_type = "Property Management",
    #         object_id = property.property_id
    #     )
    #     await db.commit()
    #     await db.refresh(property)
    #     logger.info("PropertyServices: property risk updated successfully")
    #     return {"message ": "PropertyServices: property risk updated successfully"}

    async def update_property_available_required_for_investment(db, property_id, available_required_for_investment, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        if property.is_approved == False:
            raise HTTPException(500, "property with this property_id is not not approved now")
        old_data = Property.model_to_dict(property)
        property.available_required_for_investment = available_required_for_investment
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"available_required_for_investment": available_required_for_investment},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property available_required_for_investment value updated successfully")
        return {
            "message ": "PropertyServices: property available_required_for_investment value updated successfully"
        }


    async def update_property_approval(db, property_id, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        if property.is_approved:
            property.is_approved = False
        else:
            property.is_approved = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_approved": property.is_approved},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property approval updated successfully")
        return {
            "message ": "PropertyServices: property approval updated successfully"
        }

    
    async def update_property_open_for_the_investment(db, property_id, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        if property.is_open_for_investment:
            property.is_open_for_investment = False
        else:
            property.is_open_for_investment = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_open_for_investment": property.is_open_for_investment},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property approval updated successfully")
        return {
            "message ": "PropertyServices: property approval updated successfully"
        }

    
    async def get_all_properties(db):
        stmt = (select(Property).where(Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_info_all_properties(db, skip: int = 0, limit: int = 10, deleted: bool = False):
        stmt = (
            select(Property)
            .where(Property.is_deleted == deleted)
            .offset(skip)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(Property)
            .where(Property.is_deleted == deleted)
        )
        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        return result.scalars().all(), total_res.scalar() or 0

    @staticmethod
    async def get_all_properties_info_by_risk(db, risk_status, skip: int = 0, limit: int = 10, deleted: bool = False):
        stmt = (
            select(Property)
            .where(Property.is_deleted == deleted, Property.risk_status == risk_status)
            .offset(skip)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(Property)
            .where(Property.is_deleted == deleted, Property.risk_status == risk_status)
        )
        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        return result.scalars().all(), total_res.scalar() or 0
    
    
    async def get_all_property_by_risk(db, risk_status):
        stmt = (select(Property).where(Property.is_deleted.is_(False), Property.risk_status == risk_status))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_total_count(db):

        stmt = (
            select(func.count(Property.property_id))
            .where(Property.is_deleted == False)
        )
        result = await db.execute(stmt)
        val =  result.scalar()
        print(f"DEBUG: DB returned {val}")
        return val

    
    async def get_by_id_of_property(db, property_id):
        stmt = (select(Property).where(Property.property_id == property_id, Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_all_property_name_id(db):
        stmt = (select(Property.name, Property.property_id).where(Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        rows = result.all()
        return [
                {"property_name": row.name, "property_id": row.property_id} 
                for row in rows
            ]

# not in used ===================================================================


    def round_half_up(value):
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)




class PropertyUnitTypeServices:

    async def add_new_property_unit_type(db, property_id, data, user_id):
        new_property_type = PropertyUnitType(
            property_id = property_id,
            name = data.name,
            unit_type = data.unit_type,
            total_units = data.total_units,
            max_rent_per_unit = data.max_rent_per_unit,
            min_rent_per_unit = data.min_rent_per_unit
        )

        db.add(new_property_type)
        await db.flush()
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Property Unit Type Management",
            object_id = str(new_property_type.id)
        )
        await db.commit()
        await db.refresh(new_property_type)
        logger.info("PropertyUnitService: Property unit type added successfully for the property")
        return new_property_type
    

    async def update_property_unit_type(db, id, property_id, data, user_id):
        unit_type = await PropertyUnitType.get_by_id(db, id, property_id)
        if not unit_type:
            raise HTTPException(404, "property unit type not found or already deleted for this id and property_id")
        old_data = PropertyUnitType.model_to_dict(unit_type)
        if data.name is not None:
            unit_type.name = data.name

        if data.unit_type is not None:
            unit_type.unit_type = data.unit_type

        if data.total_units is not None:
            unit_type.total_units = data.total_units

        if data.max_rent_per_unit is not None:
            unit_type.max_rent_per_unit = data.max_rent_per_unit

        if data.min_rent_per_unit is not None:
            unit_type.min_rent_per_unit = data.min_rent_per_unit

        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Unit Type Management",
            object_id = str(id)
        )
        await db.commit()
        await db.refresh(unit_type)
        logger.info("PropertyUnitType: property unit type data updated successfully")

        return unit_type
    

    async def delete_property_unit_type(db, id, property_id, user_id):
        unit_type = await PropertyUnitType.get_by_id(db, id, property_id)
        if not unit_type:
            raise HTTPException(404, "property unit type not found or already deleted for this id and property_id")
        old_data = PropertyUnitType.model_to_dict(unit_type)
        unit_type.is_deleted = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"id_deleted":True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Property Unit Type Management",
            object_id = str(id)
        )
        await db.commit()
        await db.refresh(unit_type)
        logger.info("PropertyUnitType: property unit type data deleted successfully")
        return {
            "message": "PropertyUnitType: property unit type deleted successfully"
        }
    

    async def get_all_unit_type_for_property_id(db, property_id):
        stmt = (select(PropertyUnitType).where(PropertyUnitType.property_id == property_id, PropertyUnitType.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_unit_type_by_property_id_and_id(db, id, property_id):
        return await PropertyUnitType.get_by_id(db, id, property_id)

