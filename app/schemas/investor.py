from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class AddressBase(BaseModel):
    address_line_1: str
    address_line_2: str
    city: str
    province: str
    country: str
    postal_code: str

    class Config:
        from_attributes = True

class InvestorCreate(BaseModel):
    sirname: Optional[str] = None,
    fname: str
    mname: Optional[str] = None,
    lname: Optional[str] = None,
    email: str
    phone: str
    role: str | None = "investor"
    address: AddressBase

    class Config:
        from_attributes = True

class InvestorResponse(BaseModel):
    investor_id: str
    user_id: str
    added_by : str | None = None
    sirname: Optional[str] = None
    fname: str
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: str
    phone: str
    is_active:bool
    role: str | None = "investor"
    address: Optional[AddressBase] = None

    class Config:
        from_attributes = True

class InvestorPaginationResponse(BaseModel):
    items: List[InvestorResponse]
    total_count: int
    page: int
    size: int
    total_pages: int

    class Config:
        from_attributes = True

class AddressUpdate(BaseModel):
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    postal_code: str | None = None

class InvestorUpdate(BaseModel):
    sirname: str | None = None
    fname: str | None = None
    mname: str | None = None
    lname: str | None = None
    phone: str | None = None
    profile_image: str | None = None
    is_active: bool | None = None
    address: AddressUpdate | None = None





class InvestorInvestmentCreate(BaseModel):
    property_id: str
    invested_amount: float
    status: str | None = None

    class Config:
        from_attributes = True


class InvestorInvestmentsUpdate(BaseModel):
    property_id: str | None = None
    invested_amount: float | None = None
    status: str | None = None


class InvestorInvestmentsResponse(InvestorInvestmentCreate):
    id: int
    investor_id: str
    invested_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
        