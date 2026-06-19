from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class createLeads(BaseModel):
    fname: str
    lname: str
    email: EmailStr
    i_am_type: str
    description: str
    phone: str
    consent_check: bool

    class Config:
        from_attributes = True

class updateLeads(BaseModel):
    fname: Optional[str]
    lname: Optional[str]
    email: Optional[EmailStr]
    i_am_type: Optional[str]
    description: Optional[str]
    phone: Optional[str]
    status: str
    remarks: str
    consent_check: Optional[bool]


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
    fname: str
    lname: str
    email: str
    description: Optional[str]
    i_am_type: str
    phone: Optional[str]
    assisted_by: Optional[str]
    status: str
    consent_check: bool
    updated_by: Optional[str]
    is_deleted: bool

    created_at: datetime
    updated_at: Optional[datetime]

    remarks: List[LeadRemarkResponse] = []

    class Config:
        from_attributes = True

class LeadListResponse(BaseModel):
    id: int
    fname: str
    lname: str
    email: str
    i_am_type: str
    phone: Optional[str]
    assisted_by: Optional[str]
    status: str
    consent_check: bool
    latest_remark: Optional[str]
    latest_remark_by: Optional[str]
    latest_remark_at: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedLeadResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CreateRemarks(BaseModel):
    remark: str


class RemarkResponse(BaseModel):
    id : int
    remark: str
    lead_id : str
    created_by : str
    created_at : datetime