from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class createLease(BaseModel):
    tenant_name : str
    lease_start_date : datetime
    lease_end_date : datetime
    agreed_rent: float

    class Config:
        from_attributes = True


class updatePropertyLease(BaseModel):
    tenant_name : str | None = None
    lease_start_date : datetime | None = None
    lease_end_date : datetime | None = None
    agreed_rent: float | None = None



class PropertyLeaseResponse(createLease):
    lease_id: str
    unit_id: str
    property_id: str
    is_active: bool
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class createPropertyRentCollection(BaseModel):
    rent_month : datetime
    rent_amount : float
    is_paid: bool
    paid_on: datetime

    class Config:
        from_attributes = True

class updatePropertyRentCollection(BaseModel):
    rent_month : datetime | None = None
    rent_amount : float | None = None
    is_paid: bool | None = None
    paid_on: datetime | None = None



class PropertyRentCollectionResponse(createPropertyRentCollection):
    id: int
    lease_id: str
    property_id: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True



