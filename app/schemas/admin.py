from pydantic import BaseModel, EmailStr
from typing import Optional
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

class AdminCreate(BaseModel):
    sirname: Optional[str] = None
    fname: str
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: str
    phone: str
    role: str | None = "admin"
    address: AddressBase

    class Config:
        from_attributes = True

class AdminResponse(BaseModel):
    admin_id: str
    user_id: str
    sirname: Optional[str] = None
    fname: str
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: str
    phone: str
    role: str | None = "admin"
    address: Optional[AddressBase] = None

    class Config:
        from_attributes = True

class AddressUpdate(BaseModel):
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    postal_code: str | None = None

class AdminUpdate(BaseModel):
    sirname: str | None = None
    fname: str | None = None
    mname: str | None = None
    lname: str | None = None
    phone: str | None = None
    profile_image: str | None = None
    is_active: bool | None = None
    address: AddressUpdate | None = None

