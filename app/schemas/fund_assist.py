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

class FundAssistCreate(BaseModel):
    sirname: Optional[str] = None
    fname: str
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: str
    phone: str
    role: str | None = "fund-assistant"
    address: AddressBase

    class Config:
        from_attributes = True

class FundAssistResponse(BaseModel):
    fund_assist_id: str
    user_id: str
    sirname: Optional[str] = None
    fname: str
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: str
    phone: str
    role: str | None = "fund-assistant"
    profile_image: str | None = None
    is_active: bool
    address: Optional[AddressBase] = None

    class Config:
        from_attributes = True

class FundAssistPaginationResponse(BaseModel):
    items: List[FundAssistResponse]
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

class FundAssistUpdate(BaseModel):
    sirname: str | None = None
    fname: str | None = None
    mname: str | None = None
    lname: str | None = None
    phone: str | None = None
    profile_image: str | None = None
    is_active: bool | None = None
    address: AddressUpdate | None = None

