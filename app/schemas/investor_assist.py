from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.schemas.investor import InvestorResponse

class AddressBase(BaseModel):
    address_line_1: str
    address_line_2: str
    city: str
    province: str
    country: str
    postal_code: str

    class Config:
        from_attributes = True

class InvestorAssistCreate(BaseModel):
    sirname: Optional[str] = None,
    fname: str
    mname: Optional[str] = None,
    lname: Optional[str] = None,
    email: str
    phone: str
    role: str | None = "investor-assistant"
    address: AddressBase

    class Config:
        from_attributes = True

class InvestorAssistResponse(BaseModel):
    investor_assistant_id: str
    user_id: str
    sirname: Optional[str] = None
    fname: str
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: str
    phone: str
    is_active:bool
    role: str | None = "investor-assistant"
    profile_image: str | None = None
    address: Optional[AddressBase] = None

    class Config:
        from_attributes = True

class InvestorAssistPaginationResponse(BaseModel):
    items: List[InvestorAssistResponse]
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

class InvestorAssistUpdate(BaseModel):
    sirname: str | None = None
    fname: str | None = None
    mname: str | None = None
    lname: str | None = None
    phone: str | None = None
    profile_image: str | None = None
    is_active: bool | None = None
    address: AddressUpdate | None = None




class AssignNewAssist(BaseModel):
    investor_id: str
    investor_assistant_id: str

    class Config:
        from_attributes = True



class AssignAssistResponse(AssignNewAssist):
    id: int
    is_deleted: bool | None = None
    assigned_at: datetime |None = None
    created_at: datetime | None = None
    investor_assistant : InvestorAssistResponse | None = None
    investor : InvestorResponse | None = None

    class Config:
        from_attributes = True