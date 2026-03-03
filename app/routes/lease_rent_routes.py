from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.lease_rent_service import PropertyLeaseService, PropertyRentCollectionService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.lease_rent import (createLease, updatePropertyLease, PropertyLeaseResponse, 
                                  createPropertyRentCollection, updatePropertyRentCollection, PropertyRentCollectionResponse)
import logging 
logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/add/lease/{property_id}/{unit_id}", response_model = PropertyLeaseResponse)
async def add_new_lease(property_id: str, unit_id: str, data: createLease, db: Session = Depends(get_db)):
    new_lease = await PropertyLeaseService.add_new_unit_lease(db, unit_id, property_id, data)
    return PropertyLeaseResponse.model_validate(new_lease)


@router.put("/update/lease/{property_id}/{unit_id}/{lease_id}", response_model = PropertyLeaseResponse)
async def add_new_lease(property_id: str, unit_id: str, lease_id: str, data: updatePropertyLease, db: Session = Depends(get_db)):
    updated_lease = await PropertyLeaseService.update_lease_unit(db, lease_id, unit_id, property_id, data)
    return PropertyLeaseResponse.model_validate(updated_lease)


@router.put("/activate-deactivate/lease/{property_id}/{unit_id}/{lease_id}")
async def activate_deactivate_lease(property_id: str, unit_id: str, lease_id: str, db: Session = Depends(get_db)):
    return await PropertyLeaseService.active_deactive_lease_unit(db, lease_id, unit_id, property_id)


@router.put("/delete/lease/{property_id}/{unit_id}/{lease_id}")
async def delete_lease(property_id: str, unit_id: str, lease_id: str, db: Session = Depends(get_db)):
    return await PropertyLeaseService.delete_lease_unit(db, lease_id, unit_id, property_id)


@router.get("/get/lease/{property_id}/{unit_id}/{lease_id}", response_model = PropertyLeaseResponse)
async def get_lease_data(property_id: str, unit_id: str, lease_id: str, db: Session = Depends(get_db)):
    lease_info = await PropertyLeaseService.get_lease_info(db, lease_id, unit_id, property_id)
    return PropertyLeaseResponse.model_validate(lease_info)


@router.get("/getall/lease/{property_id}/{unit_id}/{lease_id}/{status}", response_model = PropertyLeaseResponse)
async def get_lease_data(property_id: str, unit_id: str, lease_id: str, status: str, db: Session = Depends(get_db)):
    all_lease_info = await PropertyLeaseService.get_all_lease_info(db, lease_id, unit_id, property_id, status)
    return [PropertyLeaseResponse.model_validate(lease_info) for lease_info in all_lease_info]


#  add route for the rent collection against the proprty unit and as per lease


@router.post("/add/rent/{property_id}/{lease_id}", response_model = PropertyRentCollectionResponse)
async def add_new_lease_rent_info(property_id: str, lease_id: str, data: createPropertyRentCollection, db: Session = Depends(get_db)):
    new_rent = await PropertyRentCollectionService.add_property_unit_rent_collection(db, lease_id, property_id, data)
    return PropertyRentCollectionResponse.model_validate(new_rent)


@router.post("/update/rent/{property_id}/{lease_id}/{id}", response_model = PropertyRentCollectionResponse)
async def update_lease_rent_info(property_id: str, lease_id: str, id: int, data: createPropertyRentCollection, db: Session = Depends(get_db)):
    updated_rent = await PropertyRentCollectionService.update_property_unit_rent_collection(db, id, lease_id, property_id, data)
    return PropertyRentCollectionResponse.model_validate(updated_rent)



@router.put("/delete/rent/{property_id}/{lease_id}/{id}")
async def delete_lease_rent(property_id: str, lease_id: str, id: int, db: Session = Depends(get_db)):
    return await PropertyRentCollectionService.delete_property_unit_rent_collection(db, id, lease_id, property_id)


@router.put("/get/rent/{property_id}/{lease_id}/{id}", response_model = PropertyRentCollectionResponse)
async def get_lease_rent(property_id: str, lease_id: str, id: int, db: Session = Depends(get_db)):
    rent = await PropertyRentCollectionService.get_rent_for_lease_and_rent_id(db, id, lease_id, property_id)
    return PropertyRentCollectionResponse.model_validate(rent)



@router.put("/getall/rent/{property_id}/{lease_id}", response_model = PropertyRentCollectionResponse)
async def get_lease_rent(property_id: str, lease_id: str, db: Session = Depends(get_db)):
    all_rent = await PropertyRentCollectionService.get_all_rent_for_lease(db, lease_id, property_id)
    return all_rent





