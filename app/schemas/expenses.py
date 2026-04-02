from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime



class CreateExpenseType(BaseModel):
    property_id: str
    name: str

    class Config:
        from_attributes = True

class UpdateExpenseType(BaseModel):
    property_id: str | None = None
    name: str | None = None
    

class ExpenseTypeResponse(CreateExpenseType):
    id: int
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True





class CreateExpense(BaseModel):
    name: str | None = None
    current_expense: float


    class Config:
        from_attributes = True


class UpdateExpense(BaseModel):
    current_expense: float | None = None
    name: str | None = None


class ExpenseResponse(CreateExpense):
    expense_id: str
    property_id: str
    expense_type_id: int
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool

    class Config:
        from_attributes = True






class CreateExpenseGrowth(BaseModel):
    year: int
    is_same: bool |None = None
    growth_percentage: float

    class Config:
        from_attributes = True


class UpdateExpenseGrowth(BaseModel):
    year: int | None = None
    growth_percentage: float | None = None


class ExpenseGrowthResponse(CreateExpenseGrowth):
    id: int
    expense_id: str
    created_at: datetime
    update_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True



class ExpenseGrowthResponse(BaseModel):
    id: int
    year: int
    growth_percentage: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }

class ExpenseDetailResponse(BaseModel):
    expense_id: str
    current_expense: float
    pro_forma_expense: float
    created_at: datetime
    updated_at: datetime | None = None
    expense_growth: List[ExpenseGrowthResponse] = []

    model_config = {
        "from_attributes": True
    }


class ExpenseAllTypeResponseInDetials(BaseModel):
    expense_type_id: int
    expense_type_name: str
    expenses: List[ExpenseDetailResponse] = []

    model_config = {
        "from_attributes": True
    }
