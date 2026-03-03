from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class createLeads(BaseModel):
    name: str
    email: EmailStr
    description: str
    phone: str

    class Config:
        from_attributes = True

class updateLeads(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    description: Optional[str]
    phone: Optional[str]
    status: str
    remarks: str


class addRemarksLeads(BaseModel):
    remarks: str


class LeadRemarkResponse(BaseModel):
    id: int
    remark: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    description: Optional[str]
    phone: Optional[str]
    assisted_by: Optional[str]
    status: str
    updated_by: Optional[str]
    is_deleted: bool

    created_at: datetime
    updated_at: Optional[datetime]

    remarks: List[LeadRemarkResponse] = []

    class Config:
        from_attributes = True

class LeadListResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    assisted_by: Optional[str]
    status: str

    latest_remark: Optional[str]
    latest_remark_by: Optional[str]
    latest_remark_at: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True
