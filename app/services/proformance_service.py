from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.property_model import Property, PropertyUnit, PropertyUnitType, PropertyLoan
from app.models.income_model import IncomeGrowth, Income, IncomeType
from app.models.expenses_model import ExpenseGrowth, Expense, ExpenseTypes
from app.core.utils_functions import generate_id
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from dateutil.relativedelta import relativedelta
from openpyxl.utils import get_column_letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_DOWN
from typing import Dict, Any
import logging
import time
from collections import defaultdict

getcontext().prec = 28
logger = logging.getLogger(__name__)

from typing import List, Dict
class PerformanceService:
    @staticmethod
    async def calculate_financial_summary(db, property_id: int):
        # Fetching data from your existing models
        income_data = await IncomeType.get_property_income_details(db, property_id)
        expense_data = await ExpenseTypes.get_property_expense_details(db, property_id)

        income_breakdown = {}
        total_gross_income_per_year = {year: 0.0 for year in range(12)}
        vacancy_percentage_map = {year: 0.0 for year in range(12)}

        # --- STEP 1: Process Positive Income & Identify Vacancy Rate ---
        for category in income_data:
            type_name = category.get('income_type_name')
            for item in category.get('incomes', []):
                current_val = float(item.get('current_income', 0.0))
                growth_list = sorted(item.get('income_growth', []), key=lambda x: x['year'])
                growth_map = {g['year']: g['growth_percentage'] for g in growth_list}
                
                # Special Handling: Store the Vacancy PERCENTAGE only
                if type_name.lower() == "vacancy":
                    running_rate = current_val
                    vacancy_percentage_map[0] = running_rate
                    for year in range(1, 12):
                        rate_growth = growth_map.get(year, 0.0)
                        running_rate *= (1 + rate_growth / 100)
                        vacancy_percentage_map[year] = running_rate
                else:
                    # Regular Income (Rent, Parking, etc.)
                    income_breakdown[type_name] = {0: current_val}
                    total_gross_income_per_year[0] += current_val
                    
                    running_income = current_val
                    for year in range(1, 12):
                        inc_growth = growth_map.get(year, 0.0)
                        running_income *= (1 + inc_growth / 100)
                        income_breakdown[type_name][year] = round(running_income, 2)
                        total_gross_income_per_year[year] += running_income

        # --- STEP 2: Calculate Vacancy $ Based on Gross Total ---
        vacancy_dollar_breakdown = {}
        total_effective_income = {} # This is EGI (Effective Gross Income)

        for year in range(12):
            pgi = total_gross_income_per_year[year]
            v_rate = vacancy_percentage_map[year]
            
            # PROOF: Vacancy calculation based on total gross income
            v_amount = (pgi * v_rate) / 100
            vacancy_dollar_breakdown[year] = round(v_amount, 2)
            
            # Total Income = Gross - Vacancy Loss
            total_effective_income[year] = round(pgi - v_amount, 2)
        
        # Inject the calculated dollar amounts back into the breakdown
        income_breakdown["Vacancy"] = vacancy_dollar_breakdown

        # --- STEP 3: Calculate Expenses (Management Fees on Effective Income) ---
        expense_breakdown = {}
        for category in expense_data:
            type_name = category.get('expense_type_name')
            for item in category.get('expenses', []):
                current_exp = float(item.get('current_expense', 0.0))
                growth_list = item.get('expense_growth', [])
                rates_map = {g['year']: g['growth_percentage'] for g in growth_list}
                
                # PROOF: Fees calculated on EGI (Actual Income Collected)
                if type_name in ["Asset Management", "Property Management"]:
                    expense_breakdown[type_name] = {}
                    for year in range(12):
                        fee_perc = rates_map.get(year, 0.0) if year > 0 else current_exp
                        egi = total_effective_income[year]
                        expense_breakdown[type_name][year] = round((egi * fee_perc) / 100, 2)
                else:
                    # Standard Expenses
                    expense_breakdown[type_name] = {0: current_exp}
                    running_exp = current_exp
                    for year in range(1, 12):
                        exp_growth = rates_map.get(year, 0.0)
                        running_exp *= (1 + exp_growth / 100)
                        expense_breakdown[type_name][year] = round(running_exp, 2)

        # --- STEP 4: Final Totals ---
        total_expense_per_year = {
            year: round(sum(cat.get(year, 0.0) for cat in expense_breakdown.values()), 2)
            for year in range(12)
        }

        net_operating_income = {
            year: round(total_effective_income[year] - total_expense_per_year[year], 2)
            for year in range(12)
        }

        return {
            "income_breakdown": income_breakdown,
            "total_gross_income_per_year": {y: round(v, 2) for y, v in total_gross_income_per_year.items()},
            "total_income_per_year": total_effective_income,
            "expense_breakdown": expense_breakdown,
            "total_expense_per_year": total_expense_per_year,
            "net_operating_income": net_operating_income
        }