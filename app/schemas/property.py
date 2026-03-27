from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


class AddressCreate(BaseModel):
    address_line_1: str
    address_line_2: str
    city: str
    province: str
    country: str
    postal_code: str

    class Config:
        from_attributes = True



class AddressUpdate(BaseModel):
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    postal_code: str | None = None



class createProperty(BaseModel):
    name: str
    description: str
    risk_status: str
    purchase_price: float
    closing_cost: float
    loan_amount: float
    market_cap_rate: float
    cap_rate_flactuation: float
    property_type: str
    total_area: float
    total_investment_required: float
    available_required_for_investment: float
    gp_equity_stake: float
    hurdle: float
    go_promote_at_hurdle: float
    go_promote_above_hurdle: float
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    postal_code: str | None = None


    class Config:
        from_attributes = True

class PropertyResponse(createProperty):
    property_id: str
    added_by: str
    updated_by: str | None = None
    is_approved: bool
    is_open_for_investment: bool
    is_deleted: bool
    property_sheet: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class PropertyPaginationResponse(BaseModel):
    items: List[PropertyResponse]
    total_count: int
    page: int
    size: int
    total_pages: int

    class Config:
        from_attributes = True

class updateProperty(BaseModel):
    name: str | None = None
    description: str | None = None
    risk_status: str | None = None
    purchase_price: float | None = None
    closing_cost: float | None = None
    loan_amount: float | None = None
    market_cap_rate: float | None = None
    cap_rate_flactuation: float | None = None
    property_type: str | None = None
    total_area: float | None = None
    total_investment_required: float | None = None
    available_required_for_investment: float | None = None
    gp_equity_stake: float  | None = None
    hurdle: float | None = None
    go_promote_at_hurdle: float | None = None
    go_promote_above_hurdle: float | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    postal_code: str | None = None


class investmentRequired(BaseModel):
    amount: float




class createPropertyType(BaseModel):
    name: str
    unit_type: str
    total_units: int
    occupied_units: int

    class Config:
        from_attributes = True


class updatePropertyType(BaseModel):
    name: str | None = None
    unit_type: str | None = None
    total_units: int | None = None
    occupied_units: int | None = None


class PropertyTypeResponse(createPropertyType):
    id: int
    property_id: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class createPropertyUnit(BaseModel):
    property_id: str
    unit_type_id: int
    unit_status: str
    area_sqft: float
    market_lease_rent: float
    actual_lease_rent: float
    lease_start_date: date
    lease_end_date: date

    class Config:
        from_attributes = True


class updatePropertyUnit(BaseModel):
    property_id: str
    unit_type_id: int
    unit_status: str | None = None
    area_sqft: float | None = None
    market_lease_rent: float | None = None
    actual_lease_rent: float | None = None
    lease_start_date: date | None = None
    lease_end_date: date | None = None

class UpdateOccupiedStatus(BaseModel):
    property_id: str
    unit_type_id: int
    occupied_units: int
    unit_status: str | None = None

class PropertyUnitResponse(createPropertyUnit):
    unit_id: str
    unit_status: str
    is_deleted: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class createPropertyLoan(BaseModel):
    started_date : datetime
    end_date :datetime
    total_loan_amount : float
    interest_rate : float
    spread_intrest_rate: float
    # interest_per_period : float
    ltv: float
    stabilized_cap_rate: float
    intrest_only_period: int
    term: int
    amortization_period : int
    origination_fee: float
    no_of_payments : int | None = None
    monthly_payments : float | None = None
    total_annual_payment : float | None = None

    class Config:
        from_attributes = True

class updatePropertyLoan(BaseModel):
    started_date: datetime | None = None
    end_date :datetime | None = None
    total_loan_amount : float | None = None
    interest_rate : float | None = None
    spread_intrest_rate: float| None = None
    amortization_period : int | None = None
    intrest_only_period: int | None = None
    ltv: float | None = None
    stabilized_cap_rate: float | None = None
    term: int | None = None

class PropertyName(BaseModel):
    name: str | None = "----"
    class Config:
        from_attributes = True

class PropertyLoanResponse(createPropertyLoan):
    loan_id: str
    property_id: str
    property: PropertyName 
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime| None = None

    class Config:
        from_attributes = True












class createAmortzSechedule(BaseModel):
    year : str
    month : str
    principal_amount : float
    PMT : float
    interest : float
    principal_paid : float
    loan_balance : float

    class Config:
        from_attributes = True

class updateAmortzSechedule(BaseModel):
    year : str | None = None
    month : str | None = None
    principal_amount : float | None = None
    PMT : float | None = None
    interest : float | None = None
    principal_paid : float | None = None
    loan_balance : float | None = None


class AmortzSecheduleResponse(createAmortzSechedule):
    amortization_id: str
    property_id: str
    loan_id: str
    is_paid: bool
    paid_date: datetime| None = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime| None = None


    class Config:
        from_attributes = True


class updateMarkAmortzSchedulePayment(BaseModel):
    is_paid: bool
    paid_date: datetime





