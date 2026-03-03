from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.property_service import PropertyService, PropertyUnitTypeServices, PropertyUnitServices
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.property import createPropertyUnit, updatePropertyUnit, PropertyUnitResponse, UpdateOccupiedStatus
from typing import List
import logging 
logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/add", response_model = PropertyUnitResponse)
async def add_new_property_Unit(data: createPropertyUnit, db: Session = Depends(get_db)):
    property_unit = await PropertyUnitServices.add_new_property_unit(db, data)
    return PropertyUnitResponse.model_validate(property_unit)


@router.put("/update/{unit_id}", response_model = PropertyUnitResponse)
async def update_property_Unit( unit_id : str, data: updatePropertyUnit, db: Session = Depends(get_db)):
    property_unit = await PropertyUnitServices.update_property_unit(db, unit_id, data)
    return PropertyUnitResponse.model_validate(property_unit)



@router.delete("/delete/{property_id}/{unit_type_id}/{unit_id}")
async def delete_property_Unit(unit_id: str, unit_type_id: int, property_id: str, db: Session = Depends(get_db)):
    return await PropertyUnitServices.delete_property_unit(db, unit_id, unit_type_id, property_id)



@router.get("/get/{property_id}/{unit_type_id}", response_model = List [PropertyUnitResponse])
async def get_all_unit(unit_type_id: int, property_id: str, db: Session = Depends(get_db)):
    property_units = await PropertyUnitServices.get_all_unit_for_property_id(db, unit_type_id, property_id)
    if not property_units:
            raise HTTPException(404, "property unit not found or already deleted for this property_id or not available till now.")
    return [PropertyUnitResponse.model_validate(property_unit) for property_unit in property_units]



@router.get("/get/{property_id}/{unit_type_id}/{unit_id}", response_model = PropertyUnitResponse)
async def get_unit_by_id(unit_id: str, unit_type_id: int, property_id: str, db: Session = Depends(get_db)):
    property_unit = await PropertyUnitServices.get_unit_by_property_id_and_id(db, unit_id, unit_type_id, property_id)
    if not property_unit:
            raise HTTPException(404, "property unit not found or already deleted for this property_id and id.")
    return PropertyUnitResponse.model_validate(property_unit)


@router.put("/occupied-status/{unit_id}/unit", response_model = PropertyUnitResponse)
async def update_the_status_occupied_and_units(unit_id: str, data: UpdateOccupiedStatus, db: Session = Depends(get_db)):
    unit = await PropertyUnitServices.update_occupied_property_unit_status(db, unit_id, data)
    return PropertyUnitResponse.model_validate(unit)

     





