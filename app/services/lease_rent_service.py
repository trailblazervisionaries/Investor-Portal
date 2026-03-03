from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc, extract
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.models.property_model import Property, PropertyUnitType, PropertyUnit
import traceback
import os
import logging


logger = logging.getLogger(__name__)

class PropertyLeaseService:

    async def add_new_unit_lease(db, unit_id, property_id, data):
        new_lease = PropertyUnitLease(
            lease_id = generate_id("lease"),
            property_id = property_id,
            unit_id = unit_id,
            tenant_name = data.tenant_name,
            lease_start_date = data.lease_start_date,
            lease_end_date = data.lease_end_date,
            agreed_rent = data.agreed_rent
        )
        db.add(new_lease)
        await db.commit()
        await db.refresh(new_lease)
        logger.info("PropertyLeaseService: Lease data is stored in the database")

        return new_lease
    

    async def update_lease_unit(db, lease_id, unit_id, property_id, data):
        lease_data = await PropertyUnitLease.get_by_id(db, lease_id, unit_id, property_id)
        if not lease_data:
            raise HTTPException(404, "PropertyLeaseService: lease data not found with provided lease_id, unit_id.")
        
        if data.tenant_name is not None:
            lease_data.tenant_name = data.tenant_name
        
        if data.lease_start_date is not None:
            lease_data.lease_start_date = data.lease_start_date

        if data.lease_end_date is not None:
            lease_data.lease_end_date = data.lease_end_date

        if data.agreed_rent is not None:
            lease_data.agreed_rent = data.agreed_rent

        await db.commit()
        await db.refresh(lease_data)
        logger.info("PropertyLeaseService: property lease data is updated successfully.")

        return lease_data



    async def active_deactive_lease_unit(db, lease_id, unit_id, property_id):
        lease_data = await PropertyUnitLease.get_by_id(db, lease_id, unit_id, property_id)
        if not lease_data:
            raise HTTPException(404, "PropertyLeaseService: lease data not found with provided lease_id, unit_id.")
        
        if lease_data.is_active:
            lease_data.is_active = False
        else:
            lease_data.is_active = True

        await db.commit()
        await db.refresh(lease_data)

        return {
            'message': f'PropertyLeaseService: property lease is activated = {lease_data.is_active} successfully.'
        }
    


    async def delete_lease_unit(db, lease_id, unit_id, property_id):
        lease_data = await PropertyUnitLease.get_by_id(db, lease_id, unit_id, property_id)
        if not lease_data:
            raise HTTPException(404, "PropertyLeaseService: lease data not found with provided lease_id, unit_id.")
        
        lease_data.is_active = True

        await db.commit()
        await db.refresh(lease_data)

        return {
            'message': 'PropertyLeaseService: property lease is deleted successfully.'
        }
    


    async def get_lease_info(db, lease_id, unit_id, property_id):
        lease_data = await PropertyUnitLease.get_by_id(db, lease_id, unit_id, property_id)
        if not lease_data:
            raise HTTPException(404, "PropertyLeaseService: lease data not found with provided lease_id, unit_id.")
        return lease_data
    

    async def get_all_lease_info(db, unit_id, property_id, status):
        stmt = (select(PropertyUnitLease).where(PropertyUnitLease.unit_id == unit_id, 
                                                PropertyUnitLease.property_id == property_id, 
                                                PropertyUnitLease.is_active.is_(status), PropertyUnitLease.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()
    



# for the rent collection class and their member functions -------------------------------------------------

class PropertyRentCollectionService:

    async def add_property_unit_rent_collection(db, lease_id, property_id, data):
        paid = await PropertyUnitRentCollection.is_rent_paid_for_month(db, lease_id, property_id, data.rent_month)
        if paid:
            raise HTTPException(500, "PropertyRentCollectionService: You have already paid the rent for this month")
        new_collection = PropertyUnitRentCollection(
            lease_id = lease_id,
            property_id =property_id,
            rent_month = data.rent_month,
            rent_amount = data.rent_amount,
            is_paid = data.is_paid,
            paid_on = data.paid_on,
        )

        db.add(new_collection)
        await db.commit()
        await db.refresh(new_collection)

        logger.info("PropertyRentCollectionService: rent collection added successfully")

        return new_collection
        
    

    async def update_property_unit_rent_collection(db, id, lease_id, property_id, data):
        rent_collection = PropertyUnitRentCollection.get_by_id(db, id, lease_id, property_id)
        if not rent_collection:
            raise HTTPException(404, "PropertyRentCollectionService: rent collection not found for the provided id, lease_id, property_id")
        
        if data.rent_month is not None:
            rent_collection.rent_collection = data.rent_collection

        if data.rent_amount is not None:
            rent_collection.rent_amount = data.rent_amount

        if data.is_paid is not None:
            rent_collection.is_paid = data.is_paid

        if data.paid_on is not None:
            rent_collection.paid_on = data.paid_on

        await db.commit()
        await db.refresh(rent_collection)

        logger.info("PropertyRentCollectionService: rent collection updated successfully")
        return rent_collection
    

    
    async def delete_property_unit_rent_collection(db, id, lease_id, property_id):
        rent_collection = PropertyUnitRentCollection.get_by_id(db, id, lease_id, property_id)
        if not rent_collection:
            raise HTTPException(404, "PropertyRentCollectionService: rent collection not found for the provided id, lease_id, property_id")
    
        rent_collection.is_deleted = True

        await db.commit()
        await db.refresh(rent_collection)

        return{
            "message" : "PropertyRentCollectionService: rent collection data is deleted for the provided id"
        }
    

    async def get_rent_for_lease_and_rent_id(db, id, lease_id, property_id):
        rent_collection = PropertyUnitRentCollection.get_by_id(db, id, lease_id, property_id)
        if not rent_collection:
            raise HTTPException(404, "PropertyRentCollectionService: rent collection not found for the provided id, lease_id, property_id")
        return rent_collection
    


    async def get_all_rent_for_lease(db, lease_id, property_id):
        stmt = (
            select(PropertyUnitRentCollection)
            .where(
                PropertyUnitRentCollection.lease_id == lease_id,
                PropertyUnitRentCollection.property_id == property_id,
                PropertyUnitRentCollection.is_deleted.is_(False)
            )
            .order_by(
                extract("year", PropertyUnitRentCollection.paid_on).desc(),
                PropertyUnitRentCollection.paid_on.desc()
            )
        )


        rows = (await db.execute(stmt)).scalars().all()

        grouped = defaultdict(list)
        for row in rows:
            grouped[row.paid_on.year].append(row)

        return grouped

    
