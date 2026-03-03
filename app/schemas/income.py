from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class CreateIncomeType(BaseModel):
    property_id: str
    name: str

    class Config:
        from_attributes = True

class UpdateIncomeType(BaseModel):
    property_id: str | None = None
    name: str | None = None
    

class IncomeTypeResponse(CreateIncomeType):
    id: int
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True





class CreateIncome(BaseModel):
    current_income: float
    pro_forma_income: float

    class Config:
        from_attributes = True


class UpdateIncome(BaseModel):
    current_income: float | None = None
    pro_forma_income: float | None = None


class IncomeResponse(CreateIncome):
    income_id: str
    property_id: str
    income_type_id: int
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool

    class Config:
        from_attributes = True





class CreateIncomeGrowth(BaseModel):
    year: int
    is_same: bool |None = None
    growth_percentage: float

    class Config:
        from_attributes = True


class UpdateIncomeGrowth(BaseModel):
    year: int | None = None
    growth_percentage: float | None = None


class IncomeGrowthResponse(CreateIncomeGrowth):
    id: int
    income_id: str
    created_at: datetime
    update_at: datetime | None = None
    is_deleted: bool

    class Config:
        from_attributes = True




