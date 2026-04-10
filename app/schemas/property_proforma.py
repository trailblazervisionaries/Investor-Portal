from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Growth Assumptions Schemas
class GrowthYearDetail(BaseModel):
    """Growth rate for a specific year"""
    year: int = Field(..., description="Year number")
    growth_percentage: float = Field(..., description="Growth percentage for the year")


class IncomeGrowthAssumption(BaseModel):
    """Income with growth assumptions"""
    income_id: str = Field(..., description="Income ID")
    current_value: float = Field(..., description="Current income value")
    growth_by_year: List[GrowthYearDetail] = Field(default_factory=list)


class ExpenseGrowthAssumption(BaseModel):
    """Expense with growth assumptions"""
    expense_id: str = Field(..., description="Expense ID")
    current_value: float = Field(..., description="Current expense value")
    growth_by_year: List[GrowthYearDetail] = Field(default_factory=list)


class GrowthAssumptionsResponse(BaseModel):
    """All growth assumptions for a property"""
    income_growth: List[IncomeGrowthAssumption]
    expense_growth: List[ExpenseGrowthAssumption]


class IncomeGrowthRateResponse(BaseModel):
    """Income growth rates"""
    income_id: str
    current_income: float
    growth_rates: List[GrowthYearDetail]


class ExpenseGrowthRateResponse(BaseModel):
    """Expense growth rates"""
    expense_id: str
    current_expense: float
    growth_rates: List[GrowthYearDetail]


# Pro-forma Schemas
class YearProjection(BaseModel):
    """Annual projection for pro-forma"""
    year: int = Field(..., description="Year number (1-10)")
    date: datetime
    income: float = Field(..., description="Total projected income")
    expenses: float = Field(..., description="Total projected expenses")
    noi: float = Field(..., description="Net Operating Income")
    debt_service: float = Field(..., description="Debt service for the year")
    cash_flow: float = Field(..., description="Cash flow after debt service")


class ProformaResponse(BaseModel):
    """10-year pro-forma projection"""
    property_id: str
    property_name: str
    market_cap_rate: float
    purchase_price: float
    annual_projections: List[YearProjection]


class AnnualProjectionsResponse(BaseModel):
    """Year-by-year projections"""
    year_1: YearProjection
    year_2: YearProjection
    year_3: YearProjection
    year_4: YearProjection
    year_5: YearProjection
    year_6: Optional[YearProjection] = None
    year_7: Optional[YearProjection] = None
    year_8: Optional[YearProjection] = None
    year_9: Optional[YearProjection] = None
    year_10: Optional[YearProjection] = None


# Income & Expense Summary Schemas
class IncomeExpenseByUnitType(BaseModel):
    """Income and expense summary by unit type"""
    unit_type: str
    unit_count: int
    current_rent_per_unit: float
    potential_rent_per_unit: float
    current_monthly_income: float
    potential_monthly_income: float
    potential_increase: float


class IncomeExpenseSummaryResponse(BaseModel):
    """Current vs potential income/expense analysis"""
    property_id: str
    by_unit_type: List[IncomeExpenseByUnitType]
    total_current_monthly: float
    total_potential_monthly: float
    total_potential_increase: float
    total_annual_current: float
    total_annual_potential: float


# Rent Roll Schemas
class RentRollUnit(BaseModel):
    """Individual unit rent roll entry"""
    unit_id: str
    unit_type: str
    sqft: float
    status: str
    market_rent: float
    actual_rent: float
    loss_to_lease: float
    occupancy: str


class RentRollAnalysisResponse(BaseModel):
    """Detailed rent roll analysis"""
    __root__: List[RentRollUnit]


class RentRollSummaryByType(BaseModel):
    """Rent roll summary by unit type"""
    unit_type: str
    units_count: int
    monthly_rent: float
    market_rent: float
    loss_to_lease: float
    annual_rent: float


class RentRollSummaryResponse(BaseModel):
    """Aggregated rent roll summary"""
    __root__: List[RentRollSummaryByType]


# Occupancy Schemas
class OccupancyAnalysisResponse(BaseModel):
    """Occupancy rate analysis"""
    total_units: int
    occupied_units: int
    vacant_units: int
    occupancy_rate_percent: float
    vacancy_rate_percent: float


# Loss to Lease Schemas
class LossToLeaseResponse(BaseModel):
    """Loss to Lease analysis"""
    total_loss_to_lease_monthly: float
    total_loss_to_lease_annual: float
    average_ltl_per_unit: float
    ltl_percentage: float


# Comprehensive Dashboard Schema
class PropertyDashboardResponse(BaseModel):
    """Comprehensive property dashboard"""
    property_id: str
    property_name: str
    purchase_price: float
    market_cap_rate: float
    income_expense_summary: IncomeExpenseSummaryResponse
    ten_year_proforma: ProformaResponse
    last_updated: datetime


# Recalculation Response
class RecalculationResponse(BaseModel):
    """Response after recalculation"""
    last_calculated_at: datetime
    message: str = "Property calculations updated successfully"
