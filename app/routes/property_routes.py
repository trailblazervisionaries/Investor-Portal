from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.property_service import PropertyService, PropertyUnitTypeServices, PropertyUnitServices
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.property import createProperty, updateProperty, investmentRequired, PropertyResponse
from typing import List
import logging 
logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/add")
async def add_new_property(data: createProperty, request: Request, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    property = await PropertyService.add_new_property(db, user_id, data)
    # return createProperty.model_validate(property)
    return property


@router.put("/update/{property_id}")
async def update_the_property(data: updateProperty, property_id: str, request: Request, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    property = await PropertyService.update_property(db, user_id, property_id, data)
    # return createProperty.model_validate(property)
    return property


@router.delete("/delete/{property_id}")
async def delete_the_property(property_id: str, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await PropertyService.delete_property(db, property_id)
    return resp


@router.put("/update-risk/{property_id}/{risk_status}")
async def update_the_property_risk(property_id: str, risk_status: str, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await PropertyService.update_property_risk(db, property_id, risk_status)
    return resp


@router.put("/available-investment/{property_id}")
async def update_the_property_investment_available(property_id: str, data: investmentRequired, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await PropertyService.update_property_available_required_for_investment(db, property_id, data.amount)
    return resp


@router.put("/approval/{property_id}")
async def update_the_property_approval(property_id: str, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await PropertyService.update_property_approval(db, property_id)
    return resp


@router.put("/open-for-investment/{property_id}")
async def update_the_property_open_for_investment(property_id: str, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await PropertyService.update_property_open_for_the_investment(db, property_id)
    return resp


@router.get("/getall", response_model=List[PropertyResponse])
async def get_all_property(request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    properties = await PropertyService.get_all_properties(db)
    return [PropertyResponse.model_validate(property) for property in properties]


@router.get("/get/{property_id}", response_model = PropertyResponse)
async def get_by_property_id(request: Request, property_id:str, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    property = await PropertyService.get_by_id_of_property(db, property_id)
    return PropertyResponse.model_validate(property)


@router.get("/getall/{risk_status}",  response_model=List[PropertyResponse])
async def get_all_property_filter_by_risk(request: Request,risk_status: str, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role not in ["admin","fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    properties = await PropertyService.get_all_property_by_risk(db, risk_status)
    return [PropertyResponse.model_validate(property) for property in properties]


@router.get("/getall-rent-info/{property_id}")
async def get_all_rent_info(property_id: str, db: Session = Depends(get_db)):
    return await PropertyService.get_all_info_related_rent(db, property_id)



@router.get("/getall-rentroll-summary/{property_id}")
async def get_all_rentroll_summary(property_id: str, db: Session = Depends(get_db)):
    return await PropertyService.calculate_rent_roll_summary(db, property_id)