from fastapi import HTTPException
from app.models.income_model import IncomeGrowth, Income, IncomeType
from app.models.expenses_model import ExpenseGrowth, Expense, ExpenseTypes
from app.models.property_model import PropertyLoan
from app.core.utils_functions import generate_id
from openpyxl.utils import get_column_letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_DOWN
import logging


getcontext().prec = 28
logger = logging.getLogger(__name__)



class PerformanceService:

    @staticmethod
    async def calculate_financial_summary(db, property_id: int):
        loan_info = await PropertyLoan.get_by_property_id(db, property_id)
        income_data = await IncomeType.get_property_income_details(db, property_id)
        expense_data = await ExpenseTypes.get_property_expense_details(db, property_id)

        income_breakdown = {}
        total_gross_income_per_year = {year: 0.0 for year in range(12)}
        vacancy_percentage_map = {year: 0.0 for year in range(12)}

        # Process Income ---------------------------------------
        for category in income_data:
            type_name = category.get('income_type_name', '').strip()

            for item in category.get('incomes', []):
                current_val = float(item.get('current_income', 0.0))
                growth_list = sorted(item.get('income_growth', []), key=lambda x: x['year'])
                growth_map = {g['year']: g['growth_percentage'] for g in growth_list}

                # VACANCY HANDLING --------------------------------------

                if type_name.lower() == "vacancy":
                    for year in range(12):
                        shifted_year = year + 1
                        vacancy_percentage_map[year] = float(growth_map.get(shifted_year, 0.0))

                # NORMAL INCOME ---------------------------------
                else:
                    if type_name not in income_breakdown:
                        income_breakdown[type_name] = {}

                    running_income = current_val

                    for year in range(12):
                        if year > 0:
                            growth = growth_map.get(year, 0.0)
                            running_income *= (1 + growth / 100)

                        income_breakdown[type_name][year] = round(running_income, 2)
                        total_gross_income_per_year[year] += running_income


        # Vacancy Amount + EGI ----------------------------------
        vacancy_dollar_breakdown = {}
        total_effective_income = {}

        for year in range(12):
            pgi = total_gross_income_per_year[year]
            v_rate = vacancy_percentage_map.get(year, 0.0)

            v_amount = (pgi * v_rate) / 100
            vacancy_dollar_breakdown[year] = round(v_amount, 2)

            total_effective_income[year] = round(pgi - v_amount, 2)

        # Vacancy to income (as LOSS)-------------
        income_breakdown["Vacancy"] = vacancy_dollar_breakdown

        # Expenses ------------------------

        expense_breakdown = {}

        for category in expense_data:
            type_name = category.get('expense_type_name', '').strip()

            for item in category.get('expenses', []):
                current_exp = float(item.get('current_expense', 0.0))
                growth_list = item.get('expense_growth', [])
                rates_map = {g['year']: g['growth_percentage'] for g in growth_list}

                # MANAGEMENT FEES ------------------------------

                if type_name in ["Asset Management", "Property Management", "Advertising & Misc"]:
                    expense_breakdown[type_name] = {}

                    for year in range(12):
                        if year == 0:
                            expense_breakdown[type_name][year] = round(current_exp, 2)
                        else:
                            fee_perc = float(rates_map.get(year, 0.0))

                            pgi = total_gross_income_per_year[year]
                            expense_breakdown[type_name][year] = round((pgi * fee_perc) / 100, 2)

                # NORMAL EXPENSES ----------------------------------------
                else:
                    if type_name not in expense_breakdown:
                        expense_breakdown[type_name] = {}

                    running_exp = current_exp

                    for year in range(12):
                        if year > 0:
                            growth = rates_map.get(year, 0.0)
                            running_exp *= (1 + growth / 100)

                        expense_breakdown[type_name][year] = round(running_exp, 2)

        # Totals ----------------------------------------------
        total_expense_per_year = {
            year: round(
                sum(exp.get(year, 0.0) for exp in expense_breakdown.values()),
                2
            )
            for year in range(12)
        }

        net_operating_income = {
            year: round(
                total_effective_income[year] - total_expense_per_year[year],
                2
            )
            for year in range(12)
        }

        opex_ratio = {
            year: round(
                (total_expense_per_year[year] / total_effective_income[year]) * 100,
                2
            )
            for year in range(12)
        }

        debt_payment = {
            year: 0 if year == 0 else round(float(loan_info.total_annual_payment or 0), 2)
            for year in range(12)
        }

        cash_flow_after_debt = {
            year: round(
                (net_operating_income[year] - debt_payment[year]),
                2
            )
            for year in range(12)
        }

        dscr = {
            year: round(
                (net_operating_income[year] / debt_payment[year]),
                2
            )
            for year in range(1, 12)
        }

        # FINAL RESPONSE ------------------------------------
        return {
            "income_breakdown": income_breakdown,
            "total_gross_income_per_year": {
                y: round(v, 2) for y, v in total_gross_income_per_year.items()
            },
            "vacancy_percentage": vacancy_percentage_map,
            "vacancy_amount": vacancy_dollar_breakdown,
            "total_income_per_year": total_effective_income,  
            "expense_breakdown": expense_breakdown,
            "total_expense_per_year": total_expense_per_year,
            "OPEX_ratio": opex_ratio,
            "net_operating_income": net_operating_income,
            "debt_repayment": debt_payment,
            "cashflow_after_deb_repayment": cash_flow_after_debt,
            "DSCR": dscr
        }