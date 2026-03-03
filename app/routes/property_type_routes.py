from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.property_service import PropertyService, PropertyUnitTypeServices, PropertyUnitServices
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.property import createPropertyType, updatePropertyType, PropertyTypeResponse
from typing import List
import logging 
logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/add/{property_id}", response_model = PropertyTypeResponse)
async def add_new_property_type(property_id: str, data: createPropertyType, db: Session = Depends(get_db)):
    property_type = await PropertyUnitTypeServices.add_new_property_unit_type(db, property_id, data)
    return PropertyTypeResponse.model_validate(property_type)


@router.put("/update/{property_id}/{id}", response_model = PropertyTypeResponse)
async def update_property_type( id : int, property_id: str, data: updatePropertyType, db: Session = Depends(get_db)):
    property_type = await PropertyUnitTypeServices.update_property_unit_type(db, id, property_id, data)
    return PropertyTypeResponse.model_validate(property_type)



@router.delete("/delete/{property_id}/{id}")
async def delete_property_type(id: int, property_id: str, db: Session = Depends(get_db)):
    return await PropertyUnitTypeServices.delete_property_unit_type(db, id, property_id)

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










