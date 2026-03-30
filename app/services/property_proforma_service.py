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

ORANGE = "F79646"
BLUE = "032254"
LIGHT_GRAY = "D9D9D9"
timestamp_ms = int(time.time() * 1000)

class PropertyPerformaService:

    @staticmethod
    async def get_all_info_about_property_Property_type_loans(db, property_id):
        
        result = await db.execute(
            select(Property)
            .where(
                Property.property_id == property_id,
                Property.is_deleted == False
            )
            .options(
                # selectinload(Property.unit_types),
                selectinload(Property.unit_types)
                .selectinload(PropertyUnitType.units),
                selectinload(Property.loans)
            )
        )

        property_obj = result.scalars().first()

        return property_obj
    
    async def get_all_info_about_property_Property_type(db, property_id):
        
        result = await db.execute(
            select(Property)
            .where(
                Property.property_id == property_id,
                Property.is_deleted == False
            )
            .options(
                selectinload(Property.unit_types)
                .selectinload(PropertyUnitType.units),
            )
        )
        property_obj = result.scalars().first()
        return property_obj
    

    async def get_all_property_info(db, property_id):
        property_detials = await PropertyPerformaService.get_all_info_about_property_Property_type_loans(db, property_id)
        if not property_detials:
            raise HTTPException(404, "PropertyPerformaService: property_detials not found for the given property_id")
        
        total_flats = sum( types.total_units for types in (property_detials.unit_types or []) )
        closing_percent = property_detials.closing_cost * Decimal("0.01")
        total_aqz_cost = property_detials.purchase_price + (property_detials.purchase_price * closing_percent)
        aquization_cost_per_unit = (total_aqz_cost) / total_flats

        average_rent = PropertyPerformaService.get_all_info_related_actual_rent_average(property_detials)

        return {
            "property_name": property_detials.name,
            "property_id": property_detials.property_id,
            "description":property_detials.description,
            "purchase_price": property_detials.purchase_price,
            "closing_cost": property_detials.closing_cost,
            "total_aqz_cost": total_aqz_cost,
            "market_cap_rate": property_detials.market_cap_rate,
            "cap_rate_flactuation": property_detials.cap_rate_flactuation,
            "property_type": property_detials.property_type,
            "total_area": property_detials.total_area,
            "total_investment_required": property_detials.total_investment_required,
            "pro_forma_start_date": property_detials.pro_forma_start_date,
            "gp_equity_stake":property_detials.gp_equity_stake,
            "lp_equity_stake": (Decimal("100") - property_detials.gp_equity_stake),
            "lp_equity_stake_amount": (property_detials.total_investment_required * ((Decimal("100") - property_detials.gp_equity_stake) * Decimal("0.01"))),
            "hurdle": property_detials.hurdle,
            "go_promote_at_hurdle": property_detials.go_promote_at_hurdle,
            "go_promote_above_hurdle": property_detials.go_promote_above_hurdle,
            "address_line_1": property_detials.address_line_1,
            "address_line_2": property_detials.address_line_2,
            "city": property_detials.city,
            "province": property_detials.province,
            "country": property_detials.country,
            "postal_code": property_detials.postal_code,
            "aquization_cost_per_unit": aquization_cost_per_unit,
            "going_out_cap_rate": property_detials.market_cap_rate + property_detials.cap_rate_flactuation,
            "average_rent": average_rent,
            "no_of_units": total_flats,
            "loans": [
                {
                    "loan_id": loan.loan_id,
                    "loan_start_date": loan.started_date,
                    "loan_end_date": loan.end_date,
                    "total_loan_amount": loan.total_loan_amount,
                    "interest_rate": loan.interest_rate,
                    "spread_intrest_rate": loan.spread_intrest_rate,
                    "stabilized_cap_rate": loan.stabilized_cap_rate,
                    "property_ltv": loan.ltv,
                    "amortization_period": loan.amortization_period,
                    "term": loan.term,
                    "origination_fee(%)":(loan.total_loan_amount * (loan.origination_fee) * Decimal("0.01")),
                    "origination_fee_amt": loan.origination_fee,
                    "no_of_payments": loan.no_of_payments,
                    "intrest_only_period": loan.intrest_only_period,
                    "monthly_payments": loan.monthly_payments,
                    "total_annual_payment": loan.total_annual_payment,
                    "loan_repayment_and_debt_constant": PropertyPerformaService.loan_repayment(loan.interest_rate, loan.spread_intrest_rate,
                            loan.amortization_period, loan.term, loan.total_annual_payment, loan.total_loan_amount),

                }
                for loan in (property_detials.loans or [])
            ]
        }


    def loan_repayment(lending_rate, spread,
                    amortization_period,
                    term,
                    annual_payment,
                    loan_amount):

        r = (float(lending_rate) + float(spread)) / 100.0
        n = float(term)

        pv = float(loan_amount)
        pmt = float(annual_payment)

        if r == 0:
            remaining = pv - (pmt * n)
        else:
            remaining = (
                pv * (1 + r) ** n
                - pmt * ((1 + r) ** n - 1) / r
            )

        return {
            "loan_repayment": round(remaining, 2),
            "debt_constant": round((pmt / remaining) * 100, 4)
        }


    @staticmethod
    def round_half_up(value):
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def get_all_info_related_actual_rent_average(property_obj):
        return {
            "unit_type": [
                {
                    "id": ut.id,
                    "name": ut.name,
                    "total_units": ut.total_units,
                    "property_type_unit_type": ut.unit_type,
                    "average_actual_lease_rent":PropertyPerformaService.round_half_up (
                        sum(
                            (u.actual_lease_rent or Decimal("0"))
                            for u in ut.units
                            if not u.is_deleted and u.actual_lease_rent is not None
                        ) / len(
                            [
                                u for u in ut.units
                                if not u.is_deleted and u.actual_lease_rent is not None
                            ]
                        )
                    ) if any(
                        not u.is_deleted and u.actual_lease_rent is not None
                        for u in ut.units
                    ) else Decimal("0")
                }
                for ut in property_obj.unit_types if not ut.is_deleted
            ]
        }



    # async def get_all_revenue(db, property_id, is_for_noi = None):

    #     data_response = await IncomeType.get_property_income_details(db, property_id)

    #     rental_projection = {}
    #     other_projection = {}
    #     parking_projection = {}
    #     vacancy_growth = {}
    #     total_revenue_growth = {}

    #     for income_type in data_response:

    #         name = income_type["income_type_name"].strip().lower()

    #         for income in income_type.get("incomes", []):

    #             current = Decimal(str(income.get("current_income", 0)))
    #             proforma = Decimal(str(income.get("pro_forma_income", 0)))
    #             growth_data = sorted(
    #                 income.get("income_growth", []),
    #                 key=lambda x: x["year"]
    #             )

    #             # ---------------- VACANCY ----------------
    #             if name == "vacancy":
    #                 for g in growth_data:
    #                     vacancy_growth[g["year"]] = Decimal(
    #                         str(g["growth_percentage"])
    #                     )
    #                 continue

    #             # ---------------- TOTAL REVENUE GROWTH % ----------------
    #             if name == "total revenue":
    #                 for g in growth_data:
    #                     total_revenue_growth[g["year"]] = Decimal(
    #                         str(g["growth_percentage"])
    #                     )
    #                 continue

    #             # ---------------- RENTAL ----------------
    #             if name == "rental income":
    #                 rental_projection[0] = current
    #                 rental_projection[1] = proforma

    #                 for g in growth_data:
    #                     year = g["year"]
    #                     if year <= 1:
    #                         continue

    #                     prev = rental_projection[year - 1]
    #                     growth_percent = Decimal(str(g["growth_percentage"]))

    #                     rental_projection[year] = prev + (
    #                         prev * growth_percent / Decimal("100")
    #                     )

    #             # ---------------- OTHER (FIXED HERE) ----------------
    #             elif name == "other income":

    #                 # Year 0 = current
    #                 other_projection[0] = current

    #                 for g in growth_data:
    #                     year = g["year"]

    #                     # Year 1 grows from Year 0
    #                     if year == 1:
    #                         prev = current
    #                     else:
    #                         prev = other_projection.get(year - 1, current)

    #                     growth_percent = Decimal(str(g["growth_percentage"]))

    #                     other_projection[year] = prev + (
    #                         prev * growth_percent / Decimal("100")
    #                     )

    #             # ---------------- PARKING ----------------
    #             elif name == "parking":

    #                 parking_projection[0] = current

    #                 for g in growth_data:
    #                     year = g["year"]

    #                     if year == 1:
    #                         prev = current
    #                     else:
    #                         prev = parking_projection.get(year - 1, current)

    #                     growth_percent = Decimal(str(g["growth_percentage"]))

    #                     parking_projection[year] = prev + (
    #                         prev * growth_percent / Decimal("100")
    #                     )

    #     # ---------------- FINAL RESULT ----------------
    #     final_projection = {}
    #     previous_total = None

    #     for year in range(0, 12):

    #         rental = rental_projection.get(year, Decimal("0"))
    #         other = other_projection.get(year, Decimal("0"))
    #         parking = parking_projection.get(year, Decimal("0"))

    #         gross = rental + other + parking

    #         vacancy_percent = vacancy_growth.get(year, Decimal("0"))
    #         vacancy_amount = rental * vacancy_percent / Decimal("100")

    #         if year in (0, 1):
    #             total = gross - vacancy_amount
    #             previous_total = total
    #         else:
    #             growth_percent = total_revenue_growth.get(year, Decimal("0"))
    #             total = previous_total + (
    #                 previous_total * growth_percent / Decimal("100")
    #             )
    #             previous_total = total

    #         if is_for_noi is not None:
    #             final_projection[year] = {
    #                 "total_revenue": total,
    #             }
    #         else:
    #             final_projection[year] = {
    #                 "rental_income": PropertyPerformaService.round_half_up(rental),
    #                 "other_income": PropertyPerformaService.round_half_up(other),
    #                 "parking_income": PropertyPerformaService.round_half_up(parking),
    #                 "gross_income": PropertyPerformaService.round_half_up(gross),
    #                 "vacancy": PropertyPerformaService.round_half_up(-vacancy_amount),
    #                 "total_revenue": PropertyPerformaService.round_half_up(total),
    #             }
        
    #     return final_projection



    async def get_all_revenue(db, property_id, is_for_noi = None):
        data_response = await IncomeType.get_property_income_details(db, property_id)

        # Dictionary to hold projections for ANY income type: { "parking": {0: val, 1: val...}, "laundry": {...} }
        revenue_projections = {}
        vacancy_growth = {}
        total_revenue_growth = {}

        for income_type in data_response:
            name = income_type["income_type_name"].strip().lower()

            for income in income_type.get("incomes", []):
                current = Decimal(str(income.get("current_income", 0)))
                proforma = Decimal(str(income.get("pro_forma_income", 0)))
                growth_data = sorted(income.get("income_growth", []), key=lambda x: x["year"])

                # 1. Handle Vacancy and Total Revenue metadata
                if name == "vacancy":
                    for g in growth_data:
                        vacancy_growth[g["year"]] = Decimal(str(g["growth_percentage"]))
                    continue

                if name == "total revenue":
                    for g in growth_data:
                        total_revenue_growth[g["year"]] = Decimal(str(g["growth_percentage"]))
                    continue

                # 2. Initialize the projection tracker for this specific income name
                if name not in revenue_projections:
                    revenue_projections[name] = {0: current}

                # 3. Apply Growth Logic
                if name == "rental income":
                    # Rental uses Proforma for Year 1
                    revenue_projections[name][1] = proforma
                    for g in growth_data:
                        year = g["year"]
                        if year <= 1: continue
                        
                        prev = revenue_projections[name][year - 1]
                        growth_percent = Decimal(str(g["growth_percentage"]))
                        revenue_projections[name][year] = prev + (prev * growth_percent / Decimal("100"))
                else:
                    # ALL other income types (Parking, Other, or any new type)
                    for g in growth_data:
                        year = g["year"]
                        # Year 1 grows from Year 0 (current), others grow from year-1
                        prev = revenue_projections[name].get(year - 1, current)
                        growth_percent = Decimal(str(g["growth_percentage"]))
                        revenue_projections[name][year] = prev + (prev * growth_percent / Decimal("100"))

        # ---------------- FINAL RESULT ----------------
        final_projection = {}
        previous_total = None

        for year in range(0, 12):
            # Calculate Gross by summing every revenue type found
            gross = sum(proj.get(year, Decimal("0")) for proj in revenue_projections.values())

            # Vacancy is calculated specifically against "rental income"
            rental_val = revenue_projections.get("rental income", {}).get(year, Decimal("0"))
            vac_percent = vacancy_growth.get(year, Decimal("0"))
            vacancy_amount = rental_val * vac_percent / Decimal("100")

            # Total Revenue Logic
            if year in (0, 1):
                total = gross - vacancy_amount
                previous_total = total
            else:
                growth_percent = total_revenue_growth.get(year, Decimal("0"))
                total = previous_total + (previous_total * growth_percent / Decimal("100"))
                previous_total = total

            if is_for_noi is not None:
                final_projection[year] = {"total_revenue": total}
            else:
                # Build dynamic row with all individual income types
                row = { 
                    f"{k.replace(' ', '_')}": PropertyPerformaService.round_half_up(v.get(year, Decimal("0"))) 
                    for k, v in revenue_projections.items() 
                }
                # Add the summary fields
                row.update({
                    "gross_income": PropertyPerformaService.round_half_up(gross),
                    "vacancy": PropertyPerformaService.round_half_up(-vacancy_amount),
                    "total_revenue": PropertyPerformaService.round_half_up(total),
                })
                final_projection[year] = row

        return final_projection

    

    # async def calculate_all_expenses(db, property_id, is_for_noi = None):

    #     result = defaultdict(dict)
    #     expense_data = await ExpenseTypes.get_property_expense_details(db, property_id)
    #     for expense_type in expense_data:
    #         expense_name = expense_type["expense_type_name"]

    #         for expense in expense_type["expenses"]:

    #             growth_map = {
    #                 g["year"]: Decimal(str(g["growth_percentage"]))
    #                 for g in expense["expense_growth"]
    #             }

    #             current_value = Decimal(str(expense["current_expense"]))
    #             proforma_value = Decimal(str(expense["pro_forma_expense"]))

    #             result[0][expense_name] = current_value
    #             # ---------- YEAR 1 ----------
    #             if expense_name in ["CapEx", "Management Fee"]:
    #                 previous_value = proforma_value
    #             else:
    #                 growth = growth_map.get(1, Decimal("0"))
    #                 previous_value = current_value + (
    #                     current_value * growth / Decimal("100")
    #                 )

    #             result[1][expense_name] = float(previous_value)

    #             # ---------- YEAR 2–11 ----------
    #             for year in range(2, 12):
    #                 growth = growth_map.get(year, Decimal("0"))

    #                 new_value = previous_value + (
    #                     previous_value * growth / Decimal("100")
    #                 )

    #                 result[year][expense_name] = new_value

    #                 previous_value = new_value

    #     # ---------- ADD TOTAL ----------
    #     final_output = {}

    #     for year in range(0, 12):
    #         year_data = result[year]
    #         total = sum(year_data.values())

    #         year_data["total_expanse"] = total

    #         if is_for_noi is not None:
    #             final_output[year] = year_data["total_expanse"]
    #         else:
    #             final_output[year] = year_data
        
    #     return final_output


    async def calculate_all_expenses(db, property_id, is_for_noi = None):

        result = defaultdict(dict)
        expense_data = await ExpenseTypes.get_property_expense_details(db, property_id)
        for expense_type in expense_data:
            expense_name = expense_type["expense_type_name"]

            for expense in expense_type["expenses"]:

                growth_map = {
                    g["year"]: Decimal(str(g["growth_percentage"]))
                    for g in expense["expense_growth"]
                }

                current_value = Decimal(str(expense["current_expense"]))
                proforma_value = Decimal(str(expense["pro_forma_expense"]))

                result[0][expense_name] = current_value
                
                # ---------- YEAR 1 ----------
                if expense_name in ["CapEx", "Management Fee"]:
                    previous_value = proforma_value
                else:
                    growth = growth_map.get(1, Decimal("0"))
                    previous_value = current_value + (
                        current_value * growth / Decimal("100")
                    )

                result[1][expense_name] = previous_value

                # ---------- YEAR 2–11 ----------
                for year in range(2, 12):
                    growth = growth_map.get(year, Decimal("0"))
                    new_value = previous_value + (
                        previous_value * growth / Decimal("100")
                    )

                    result[year][expense_name] = new_value

                    previous_value = new_value

        # ---------- ADD TOTAL ----------
        final_output = {}

        for year in range(0, 12):
            year_data = result[year]

            formatted_data = {}
            total = Decimal("0")

            for key, val in year_data.items():
                formatted_val = PropertyPerformaService.format_value(val)
                formatted_data[key] = formatted_val
                total += formatted_val

            formatted_data["total_expanse"] = total

            if is_for_noi is not None:
                final_output[year] = total.quantize(Decimal("1"), rounding=ROUND_DOWN).quantize(Decimal("0.00"))
            else:
                final_output[year] = formatted_data

        return final_output


    def format_value(value):
        value = Decimal(str(value))
        decimal_part = value - int(value)
        if decimal_part < Decimal("0.50"):
            return Decimal(int(value)).quantize(Decimal("0.00"))
        return value.quantize(Decimal("0.00"))






    # @staticmethod
    # async def get_noi_opex_and_other_detials(db, property_id, investment_required = None):
    #     revenue_resp = await PropertyPerformaService.get_all_revenue(db, property_id, True)
    #     expense_resp = await PropertyPerformaService.calculate_all_expenses(db, property_id, True)
    #     loan_payment = await PropertyLoan.get_by_property_id(db, property_id)
    #     noi_output = {}

    #     for year in revenue_resp:
    #         total_revenue = Decimal(str(revenue_resp[year]["total_revenue"]))
    #         total_expense = Decimal(str(expense_resp.get(year, 0)))

    #         noi = total_revenue - total_expense
    #         opex_ratio = (total_expense/total_revenue)*100
    #         cash_flow_after_financing = noi - loan_payment.total_annual_payment
    #         levered_cashflow = cash_flow_after_financing
    #         noi_output[year] = {
    #             "noi": noi,
    #             "opex_ratio": opex_ratio,
    #             "debt_payment": loan_payment.total_annual_payment,
    #             "dscr": noi/loan_payment.total_annual_payment,
    #             "cash_flow_after_financing": cash_flow_after_financing,
    #             "sweet_equity": cash_flow_after_financing * Decimal("0.05"),
    #             "investor_cashflow": cash_flow_after_financing * Decimal("0.95"),
    #             "levered_cashflow_10": levered_cashflow,
    #             "levered_cashflow_5": levered_cashflow
    #         }

    #     noi_output[0]["debt_payment"] = 0.00
    #     noi_output[0]["dscr"] = 0.00
    #     noi_output[0]["cash_flow_after_financing"] = 0.00
    #     noi_output[0]["sweet_equity"] = 0.00
    #     noi_output[0]["investor_cashflow"] = 0.00
    #     noi_output[0]["levered_cashflow_10"] = investment_required
    #     noi_output[0]["levered_cashflow_5"] = investment_required

    #     loan_repayment_data = []
    #     for term in [5,10]:
    #         repayment = PropertyPerformaService.loan_repayment(loan_payment.interest_rate, loan_payment.spread_intrest_rate, loan_payment.amortization_period, 
    #                                                                   term, loan_payment.total_annual_payment, loan_payment.total_loan_amount)
    #         loan_repayment_data.append(repayment)

    #     deposition = await PropertyPerformaService.get_the_deposition_data(db, property_id, noi_output)
    #     sales_5 = deposition.get("sales_year_5", Decimal("0"))
    #     sales_10 = deposition.get("sales_year_10", Decimal("0"))

    #     loan_repayment_5 = loan_repayment_data[0].get("loan_repayment", Decimal("0"))
    #     loan_repayment_10 = loan_repayment_data[1].get("loan_repayment", Decimal("0"))

    #     net_proceeds_5 = sales_5 - Decimal(str(loan_repayment_5))
    #     print("sales_5 ", sales_5)
    #     print("loan_repayment_5 ", loan_repayment_5)
    #     net_proceeds_10 = sales_10 - Decimal(str(loan_repayment_10))

    #     noi_output["sales_year_5"] = deposition.get("sales_year_5")
    #     noi_output["loan_repayment_5"] = loan_repayment_data[0]
    #     noi_output["net_proceeds_5"] = net_proceeds_5
    #     noi_output["sales_year_10"] = deposition.get("sales_year_10")
    #     noi_output["loan_repayment_10"] = loan_repayment_data[1]
    #     noi_output["net_proceeds_10"] = net_proceeds_10
    #     noi_output[10]["levered_cashflow_10"] = noi_output[10].get("levered_cashflow_10") + net_proceeds_10
    #     noi_output[5]["levered_cashflow_5"] = sales_5 - Decimal(str(loan_repayment_5))
    #     noi_output[6]["levered_cashflow_5"] =  0.00
    #     noi_output[7]["levered_cashflow_5"] =  0.00
    #     noi_output[8]["levered_cashflow_5"] =  0.00
    #     noi_output[9]["levered_cashflow_5"] =  0.00
    #     noi_output[10]["levered_cashflow_5"] =  0.00
    #     noi_output[11]["levered_cashflow_5"] =  0.00


    #     return noi_output



    @staticmethod
    async def get_noi_opex_and_other_detials(db, property_id, investment_required=None, total_cost=None):
        revenue_resp = await PropertyPerformaService.get_all_revenue(db, property_id, True)
        expense_resp = await PropertyPerformaService.calculate_all_expenses(db, property_id, True)
        loan_payment = await PropertyLoan.get_by_property_id(db, property_id)

        noi_output = {}

        annual_debt = Decimal(str(loan_payment.total_annual_payment or 0))

        # Core yearly calculations -----------------------------------------------
        for year, revenue_data in revenue_resp.items():
            total_revenue = Decimal(str(revenue_data.get("total_revenue", 0)))
            total_expense = Decimal(str(expense_resp.get(year, 0)))

            noi = total_revenue - total_expense

            opex_ratio = (total_expense / total_revenue * 100) if total_revenue else Decimal("0")
            dscr = (noi / annual_debt) if annual_debt else Decimal("0")

            cash_flow = noi - annual_debt

            noi_output[year] = {
                "noi": noi,
                "opex_ratio": opex_ratio,
                "debt_payment": annual_debt,
                "dscr": dscr,
                "cash_flow_after_financing": cash_flow,
                "sweet_equity": cash_flow * Decimal("0.05"),
                "investor_cashflow": cash_flow * Decimal("0.95"),
                "levered_cashflow_10": cash_flow,
                "levered_cashflow_5": cash_flow,
                "unlevered_cashflow_10": noi,
                "unlevered_cashflow_5": noi

            }

        # Year 0 override ---------------------------------------
        if 0 in noi_output:
            noi_output[0].update({
                "debt_payment": Decimal("0"),
                "dscr": Decimal("0"),
                "cash_flow_after_financing": Decimal("0"),
                "sweet_equity": Decimal("0"),
                "investor_cashflow": Decimal("0"),
                "levered_cashflow_10": Decimal(str(investment_required or 0)),
                "levered_cashflow_5": Decimal(str(investment_required or 0)),
                "unlevered_cashflow_10": total_cost - noi_output[0]["noi"],
                "unlevered_cashflow_5": (total_cost - noi_output[0]["noi"]) + revenue_resp[0]["total_revenue"]
            })

        # Loan repayment--------------------------------------------
        loan_repayment_data = {
            term: PropertyPerformaService.loan_repayment(
                loan_payment.interest_rate,
                loan_payment.spread_intrest_rate,
                loan_payment.amortization_period,
                term,
                loan_payment.total_annual_payment,
                loan_payment.total_loan_amount
            )
            for term in (5, 10)
        }

        # Sale & proceeds ---------------------------------------
        deposition = await PropertyPerformaService.get_the_deposition_data(db, property_id, noi_output)

        sales_5 = Decimal(str(deposition.get("sales_year_5", 0)))
        sales_10 = Decimal(str(deposition.get("sales_year_10", 0)))

        loan_repayment_5 = Decimal(str(loan_repayment_data[5].get("loan_repayment", 0)))
        loan_repayment_10 = Decimal(str(loan_repayment_data[10].get("loan_repayment", 0)))

        net_proceeds_5 = sales_5 - loan_repayment_5
        net_proceeds_10 = sales_10 - loan_repayment_10


        # Attach summary data-----------------------------------------
        noi_output.update({
            "sales_year_5": sales_5,
            "loan_repayment_5": loan_repayment_data[5],
            "net_proceeds_5": net_proceeds_5,
            "sales_year_10": sales_10,
            "loan_repayment_10": loan_repayment_data[10],
            "net_proceeds_10": net_proceeds_10,
        })

        # Levered cashflow adjustments ------------------------------------
        if 10 in noi_output:
            noi_output[10]["levered_cashflow_10"] += net_proceeds_10
            noi_output[10]["unlevered_cashflow_10"] += sales_10

        if 5 in noi_output:
            noi_output[5]["levered_cashflow_5"] = net_proceeds_5
            noi_output[5]["unlevered_cashflow_5"] += sales_5

        # Clear years after exit (5-year scenario) --------------------------
        for year in range(6, 12):
            if year in noi_output:
                noi_output[year]["levered_cashflow_5"] = Decimal("0")
                noi_output[year]["unlevered_cashflow_5"] = Decimal("0")

        return noi_output


    

    async def get_the_deposition_data(db, property_id, noi_output):
        property_datas = await Property.get_by_id(db, property_id)
        if not property_datas:
            raise HTTPException(404, "Property detials not found for the provided property_id")
        going_out_cap_rate = property_datas.market_cap_rate - property_datas.cap_rate_flactuation
        nio_5  = noi_output[5]["noi"]
        sales_price_5 = nio_5/going_out_cap_rate * Decimal("100")

        nio_10 = noi_output[11]["noi"]
        sales_price_10 = nio_10/going_out_cap_rate * Decimal("100")

        return {
            "sales_year_5" : sales_price_5,
            "sales_year_10" : sales_price_10
        }
    


    async def get_performa_rent_per_year(db, property_id):
        property_detials = await PropertyPerformaService.get_all_info_about_property_Property_type(db, property_id)
        if not property_detials:
            raise HTTPException(404, "property_detials not found")

        data_response = await IncomeType.get_property_income_details(db, property_id)
        if not data_response:
            raise HTTPException(404, "revenue_response not found")
        average_rent = PropertyPerformaService.get_all_info_related_actual_rent_average(property_detials)

        unit_rents = {}
        for unit in average_rent["unit_type"]:
            unit_rents[unit["name"]] = Decimal(str(unit["average_actual_lease_rent"]))
        rental_growth = []
        for income_type in data_response:
            if income_type["income_type_name"] == "Rental Income":
                rental_growth = income_type["incomes"][0]["income_growth"]
                break
        rent_per_year = {}

        rent_per_year[0] = {k: float(v) for k, v in unit_rents.items()}

        for growth in rental_growth:
            year = growth["year"]
            growth_percent = Decimal(str(growth["growth_percentage"])) / Decimal("100")

            previous_year = rent_per_year[year - 1]
            current_year = {}

            for unit_name, rent in previous_year.items():
                new_rent = Decimal(str(rent)) * (Decimal("1") + growth_percent)
                current_year[unit_name] = float(new_rent.quantize(Decimal("0.00")))

            rent_per_year[year] = current_year

        return rent_per_year



    async def get_year_wise_cashflow(db, property_id):
        pass




    async def get_overall_performa_sumary(db, property_id):
        property_detials = await PropertyPerformaService.get_all_property_info(db, property_id)
        investment_required = property_detials["total_investment_required"]
        total_cost = property_detials["total_aqz_cost"]
        revenue_detials = await PropertyPerformaService.get_all_revenue(db, property_id)
        expense_detials = await PropertyPerformaService.calculate_all_expenses(db, property_id)
        other_detials = await PropertyPerformaService.get_noi_opex_and_other_detials(db, property_id, investment_required, total_cost)
        rent_summary = await PropertyPerformaService.get_performa_rent_per_year(db, property_id)

        return {
            "property_detials":property_detials,
            "revenue_detials":revenue_detials,
            "expense_detials":expense_detials,
            "other_detials":other_detials,
            "rent_summary": rent_summary
        }







#  10 year performa sheet code written here -------------------------

    def header_fill():
        return PatternFill(start_color=ORANGE, end_color=ORANGE, fill_type="solid")


    def blue_fill():
        return PatternFill(start_color=BLUE, end_color=BLUE, fill_type="solid")

    def currency(cell):
        cell.number_format = '#,##0'


    def percent(cell):
        cell.number_format = '0.0%'

    def get_em(cash_flows):
        sum_positives = sum(x for x in cash_flows if x > 0)
        sum_negatives = sum(x for x in cash_flows if x < 0)
        if sum_negatives != 0:
            ratio = sum_positives / -sum_negatives
            return f"{ratio:.2f}x"
        return 0


    async def generate_real_estate_excel(db, property_id):
        data = await PropertyPerformaService.get_overall_performa_sumary(db, property_id)

        if not data:
            raise HTTPException(400, "Property not found")

        prop = data["property_detials"]
        revenue = data["revenue_detials"]
        expense = data["expense_detials"]
        other = data["other_detials"]
        rent = data["rent_summary"]

        def sort_years(d):
            return sorted(d.keys(), key=lambda x: int(x))

        revenue_years = sort_years(revenue)
        expense_years = sort_years(expense)
        rent_years = sort_years(rent)

        other_years = sorted(
            [k for k in other.keys() if str(k).isdigit()],
            key=lambda x: int(x)
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "10 Year ProForma"

        for col in range(1, 30):
            ws.column_dimensions[get_column_letter(col)].width = 16

        # HEADER
        # -------------------------------------------------
        ws.merge_cells("A1:T1")
        ws["A1"] = prop.get("property_name", "NA")
        ws["A1"].font = Font(size=40, bold=True, color="1F4E79")
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:T2")
        cell = ws["A2"]
        address_parts = [prop.get(k, "") for k in ["address_line_1", "address_line_2", "city", "province", "country", "postal_code"]]
        cell.value = ", ".join(filter(None, address_parts))
        cell.font = Font(size=14, bold=True, color="1F4E79")
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions['F'].width = 30
    
        # YEAR HEADER (F onward)
        # -------------------------------------------------
        start_col = 7  # column F

        val = prop.get("pro_forma_start_date")
        logger.info(f"DEBUG: val is {val}, type is {type(val)}")
        if isinstance(val, str):
            base_date = datetime.fromisoformat(val)
        elif isinstance(val, datetime):
            base_date = val
        else:
            base_date = datetime.now()
        base_date = base_date.replace(month=6, day=1)

        for idx, year in enumerate(revenue_years):

            current_date = base_date + relativedelta(months=idx * 12)
            cell = ws.cell(row=3, column=start_col + idx, value=current_date)
            cell.number_format = 'DD-MM-YYYY'
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            cell.alignment = Alignment(horizontal="left")

            label = "Current" if str(year) == "0" else f"Year {year}"
            cell = ws.cell(row=4, column=start_col + idx, value=label)
            cell.fill = PropertyPerformaService.blue_fill()
            cell.font = Font(bold = True, color = "FFFFFF")

        # PROPERTY DETAILS (A–D)
        # -------------------------------------------------
        r = 5

        def write_detail(label, value, is_percent=False, is_currency=False, value2 = ""):
            nonlocal r
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
            # ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)

            cell_lab = ws.cell(row=r, column=1, value=label)
            cell_lab.font = Font(color = "FFFFFF")
            cell_lab.fill = PropertyPerformaService.blue_fill()
            cell = ws.cell(row=r, column=3, value=value)

            if is_percent:
                PropertyPerformaService.percent(cell)
            if is_currency:
                PropertyPerformaService.currency(cell)
            if isinstance(value, datetime):
                cell.number_format = 'YYYY-MM-DD'
            cell.font = Font(color = "FFFFFF")
            cell.fill = PropertyPerformaService.blue_fill()
            cell = ws.cell(row=r, column=4, value = value2)
            cell.font = Font(color = "FFFFFF")
            cell.alignment = Alignment(horizontal="center")
            cell.fill = PropertyPerformaService.blue_fill()

            r += 1
        write_detail("", "", "")
        write_detail("Market Cap Rate", prop.get("market_cap_rate", 0)/100, True)
        write_detail("Purchase Price", prop.get("purchase_price", 0), False, True)
        write_detail("Closing Cost", prop.get("closing_cost", 0)/100 , True)
        write_detail("Total Acquisition Cost", prop.get("total_aqz_cost", 0), False, True)

        #  Assumptions ---------------------
        write_detail("", "", "")
        write_detail("Assumptions :-", "", "")
        write_detail("Property Type", prop.get("property_type", ""))
        write_detail("location City", prop.get("city", ""))
        write_detail("location province", prop.get("province", ""))
        write_detail("Size (SF)", prop.get("total_area", 0))
        raw_date = prop.get("pro_forma_start_date")
        if raw_date and raw_date != "null":
            try:
                if isinstance(raw_date, datetime):
                    date_obj = raw_date
                else:
                    date_obj = datetime.fromisoformat(str(raw_date).split('T')[0])
                    
                write_detail("Transaction Date", date_obj)
            except (ValueError, TypeError, AttributeError):
                write_detail("Transaction Date", "NA")
        else:
            write_detail("Transaction Date", "---- -- --")

        
        write_detail("Number of Units", prop.get("no_of_units", 0))

        #  average rent and no. of units
        write_detail("", "", "")
        write_detail("average rent and units :-", "", "")
        for unit in prop['average_rent']['unit_type']:
            write_detail(unit.get("name", ""), unit.get("total_units", 0))
            write_detail(unit.get("name", ""), unit.get("average_actual_lease_rent", 0), False, True)

        # just space ------
        write_detail("", "", "")
        write_detail("Space and other Rent :-","", "")
        write_detail("Parking Space", prop.get("parking_space", 0))
        write_detail("parking Rent", revenue.get(0, {}).get("parking", 0),False, True)
        write_detail("Other Incomes", revenue.get(0, {}).get("other_income", 0),False, True)


        # Debt Section (FIXED)
        # -------------------------------------------------
        write_detail("", "", "")
        write_detail("Debt :-", "", "")
        acq_cap = 0
        purchase_price = prop.get("purchase_price", 0)
        noi_0 = other.get("0", {}).get("noi", 0) if "0" in other else other.get(0, {}).get("noi", 0)
        
        if purchase_price != 0 and noi_0 != 0:
            acq_cap = round((noi_0 / purchase_price) * 100)

        loan_list = prop.get("loans", [])
        loan_data = loan_list[0] if isinstance(loan_list, list) and len(loan_list) > 0 else {}

        loan_amount = loan_data.get("total_loan_amount", 0)
        sell_price_10 = other.get("sales_year_10", 0)
        
        closing_ltv = round((loan_amount / sell_price_10) * 100) if sell_price_10 else 0
        
        num_units = prop.get("no_of_units", 0)
        sell_price_unit = (sell_price_10 / num_units) if num_units else 0

        write_detail("Acquisition Cap Rate", acq_cap/100,  True)
        write_detail("Stabilized Cap Rate", loan_data.get("stabilized_cap_rate", 0)/100, True)
        write_detail("LTV", loan_data.get("property_ltv", 0)/100, True)
        write_detail("Base Lending Rate", loan_data.get("interest_rate", 0)/100, True)
        write_detail("Spread", loan_data.get("spread_intrest_rate", 0)/100, True)
        write_detail("Amortization Period", f"{loan_data.get('amortization_period', 0)} Years")
        write_detail("Term", f"{loan_data.get('term', 0)} Years")
        write_detail("Intrest Only Period", f"{loan_data.get('intrest_only_period', 0)} Years")
        write_detail("Loan Start Date", loan_data.get("loan_start_date", 0))
        write_detail("Origination Fee", loan_data.get("origination_fee(%)", 0)/100, True)
        write_detail("Loan Amount", loan_amount,False, True)
        write_detail("PMT", loan_data.get("total_annual_payment", 0), False, True)
    
        repayment_data = loan_data.get("loan_repayment_and_debt_constant", {})
        write_detail("Loan Repayment", repayment_data.get("loan_repayment", 0), False, True)
        write_detail("Closing LTV", closing_ltv/100, True)
        


        # Equity --------
        write_detail("", "", "")
        write_detail("Initial Equity :-", "", "")
        init_equity = prop.get("lp_equity_stake_amount", 0)
        write_detail("Initial Equity", init_equity, False, True)
        gp_equity = prop.get("gp_equity_stake", 0)/100
        write_detail("GP Equity Stake", gp_equity, True, False, (init_equity*gp_equity))
        lp_equity = prop.get("lp_equity_stake", 0)/100
        write_detail("LP Equity Stake", lp_equity, True, False, (init_equity*lp_equity))

        write_detail("", "", "")
        write_detail("", "", "")
        write_detail("Unlevered IRR", 0/100, True)
        write_detail("Levered IRR", 0/100, True)
        unlevered_10 = [float(other[k]["unlevered_cashflow_10"]) for k in range(11)]
        if unlevered_10:
            unlevered_10[0] = -abs(float(unlevered_10[0]))
        write_detail("Unlevered EM", PropertyPerformaService.get_em(unlevered_10))
        levered_10 = [float(other[k]["levered_cashflow_10"]) for k in range(11)]
        if levered_10:
            levered_10[0] = -abs(float(levered_10[0]))
        write_detail("Levered EM", PropertyPerformaService.get_em(levered_10))

        write_detail("", "", "")
        write_detail("", "", "")
        write_detail("Hurdle", prop.get("hurdle", 0)/100, True)
        write_detail("GP Promote at Hurdle", prop.get("go_promote_at_hurdle", 0)/100, True)
        write_detail("GP Promote Above Hurdle", prop.get("go_promote_above_hurdle", 0)/100, True)

        write_detail("", "", "")
        write_detail("", "", "")
        write_detail("GP Return", 0)
        write_detail("LP Return", other.get("net_proceeds_10", 0), False, True)

        write_detail("", "", "")
        write_detail("", "", "")
        write_detail("Going Out Cap Rate", prop.get("going_out_cap_rate", 0)/100, True)
        write_detail("Debt Constant", repayment_data.get("debt_constant", 0)/100, True)
        write_detail("Sale Price/Unit", sell_price_unit, False, True)
        write_detail("Acquisition Price/Unit", prop.get("aquization_cost_per_unit", 0), False, True)

        # 5-Year -------------
        write_detail("", "", "")
        write_detail("5-Year :-", "", "")
        write_detail("Unlevered IRR", 0/100, True)
        write_detail("Levered IRR", 0/100, True)
        unlevered_5 = [float(other[k]["unlevered_cashflow_5"]) for k in range(6)]
        if unlevered_5:
            unlevered_5[0] = -abs(float(unlevered_5[0]))
        write_detail("Unlevered EM", PropertyPerformaService.get_em(unlevered_5))
        levered_5 = [float(other[k]["levered_cashflow_5"]) for k in range(6)]
        if levered_5:
            levered_5[0] = -abs(float(levered_5[0]))
        write_detail("Levered EM", PropertyPerformaService.get_em(levered_5))

        write_detail("", "", "")
        write_detail("", "", "")
        write_detail("GP Return", 0)
        write_detail("LP Return", other.get("net_proceeds_5", 0), False, True)
        write_detail("", "", "")

        #  Acquisition
        #  ----------------------------------------------
        r = 5
        cell = ws.cell(row=r-1, column=start_col-1, value="Acquisition")
        cell.fill = PropertyPerformaService.blue_fill()
        cell.font = Font(bold = True, color = "FFFFFF")
        cell = ws.cell(row=r, column=start_col-1, value="Purchase Price")
        cell = ws.cell(row=r, column=start_col, value= prop.get("purchase_price", 0))
        PropertyPerformaService.currency(cell)
        cell = ws.cell(row=r+1, column=start_col-1, value="Closing Cost")
        closing_cost_ = (prop.get("purchase_price", 0) * prop.get("closing_cost", 0))/100
        cell = ws.cell(row=r+1, column=start_col, value= closing_cost_ )
        PropertyPerformaService.currency(cell)
        cell = ws.cell(row=r+2, column=start_col-1, value="Total Acquisition Price")
        cell.fill = PropertyPerformaService.header_fill()
        cell.font = Font(bold = True, color = "FFFFFF")
        cell = ws.cell(row=r+2, column=start_col, value=prop.get("total_aqz_cost", 0))
        PropertyPerformaService.currency(cell)
        cell.fill = PropertyPerformaService.header_fill()
        cell.font = Font(bold = True, color = "FFFFFF")


   
        # REVENUE (starts column F)
        # -------------------------------------------------
        r = 10
        cell = ws.cell(row=r-1, column=start_col-1, value="Revenue")
        cell.fill = PropertyPerformaService.blue_fill()
        cell.font = Font(bold = True, color = "FFFFFF")
        revenue_rows = [
            ("Rental Income", "rental_income"),
            ("Other Income", "other_income"),
            ("Parking Income", "parking"),
            ("Vacancy", "vacancy"),
            ("Total Revenue", "total_revenue"),
        ]

        # for label, key in revenue_rows:
        #     ws.cell(row=r, column=6, value=label)  # column E label
        #     for c, yr in enumerate(revenue_years):
        #         cell = ws.cell(row=r, column=start_col + c, value=revenue.get(yr, {}).get(key, 0))
        #         PropertyPerformaService.currency(cell)
        #     r += 1

        for label, key in revenue_rows:
            label_cell = ws.cell(row=r, column=6, value=label)
            
            if key == "total_revenue":
                label_cell.fill = PropertyPerformaService.header_fill()
                label_cell.font = Font(bold = True, color = "FFFFFF")

            for c, yr in enumerate(expense_years):
                year_data = revenue.get(str(yr)) or revenue.get(int(yr)) or {}
                val = year_data.get(key, 0)
                cell = ws.cell(row=r, column=start_col + c, value=val)
                PropertyPerformaService.currency(cell)
                
                if key == "total_revenue":
                    cell.fill = PropertyPerformaService.header_fill()
                    cell.font = Font(bold = True, color = "FFFFFF")
                    
            r += 1

        # EXPENSES
        # -------------------------------------------------
        r += 2
        cell = ws.cell(row=r, column=start_col-1, value="Expenses")
        cell.fill = PropertyPerformaService.blue_fill()
        cell.font = Font(bold = True, color = "FFFFFF")
        r += 1

        expense_rows = [
            ("Gas", "Gas"),
            ("Water", "Water"),
            ("Hydro", "Hydro"),
            ("Insurance", "Insurance"),
            ("Real Estate Taxes", "Real Estate Taxes"),
            ("Repairs & Maintenance", "Repaires & Maintenance"),
            ("Superintendent", "Superintendent"),
            ("Management Fee", "Management Fee"),
            ("Capital Expenditures", "CapEx"),
            ("Total Expenses", "total_expanse"),
        ]

        for label, key in expense_rows:
            label_cell = ws.cell(row=r, column=6, value=label)
            
            if key == "total_expanse":
                label_cell.fill = PropertyPerformaService.header_fill()
                label_cell.font = Font(bold = True, color = "FFFFFF")

            for c, yr in enumerate(expense_years):
                year_data = expense.get(str(yr)) or expense.get(int(yr)) or {}
                val = year_data.get(key, 0)
                cell = ws.cell(row=r, column=start_col + c, value=val)
                PropertyPerformaService.currency(cell)
                
                if key == "total_expanse":
                    cell.fill = PropertyPerformaService.header_fill()
                    cell.font = Font(bold = True, color = "FFFFFF")
                    
            r += 1


        # Opex Ratio
        # -------------------------------------------------
        r += 0
        cell = ws.cell(row=r, column=6, value="Opex Ratio %")
        cell.fill = PropertyPerformaService.blue_fill()
        cell.font = Font(bold = True, color = "FFFFFF")

        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=round(other.get(yr, {}).get("opex_ratio", 0)/100,3))
            PropertyPerformaService.percent(cell)
            cell.fill = PropertyPerformaService.blue_fill()
            cell.font = Font(bold = True, color = "FFFFFF")

        # NOI
        # -------------------------------------------------
        r += 2
        cell = ws.cell(row=r, column=6, value="Net Operating Income")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()
        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("noi", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        # Debt payments
        # -------------------------------------------------
        r += 2
        cell = ws.cell(row=r, column=6, value="Debt. Payments")
        cell.font = Font(bold = True, color = "F20D11")
        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("debt_payment", 0))
            cell.font = Font(bold = True, color = "F20D11")
            PropertyPerformaService.currency(cell)

    
        # dscr
        # -------------------------------------------------
        r += 1
        cell = ws.cell(row=r, column=6, value="DSCR")
        cell.font = Font(bold = True)
        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=round(other.get(yr, {}).get("dscr", 0),3))
            cell.font = Font(bold = True)


        # cashflow afer financing
        # -------------------------------------------------
        r += 2
        cell = ws.cell(row=r, column=6, value="Cash Flow After Financing")
        cell.font = Font(bold = True, color = "13EC49")
        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("cash_flow_after_financing", 0))
            cell.font = Font(bold = True, color = "13EC49")
            PropertyPerformaService.currency(cell)

        # unlevered_cashflow_10
        # -------------------------------------------------
        r += 4
        cell = ws.cell(row=r, column=6, value="Unlevered Cashflow 10 Year")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()
        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("unlevered_cashflow_10", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        # levered_cashflow_10
        # -------------------------------------------------
        r += 1
        cell = ws.cell(row=r, column=6, value="Levered Cashflow 10 Year")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()
        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("levered_cashflow_10", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        #  rent summary --------
        #  -------------------------------------------------------
        r += 4
        ws.cell(row=r, column=6, value="Rent Summary").fill = PropertyPerformaService.blue_fill()
        ws.cell(row=r, column=6).font = Font(color="FFFFFF", bold=True)

        rent_rows = [
            ("Bachelors", "Bachelors"),
            ("1 Bedroom", "1 Bedroom"),
            ("2 Bedroom", "2 Bedroom"),
            ("3 Bedroom", "3 Bedroom"),
            ("2+Den Bedroom", "2+Den Bedroom"),
        ]
        r +=1
        for label, key in rent_rows:
            ws.cell(row=r, column=6, value=label)  # column F label
            for c, yr in enumerate(rent_years):
                cell = ws.cell(row=r, column=start_col + c, value=rent.get(yr, {}).get(key, 0))
                PropertyPerformaService.currency(cell)
            r += 1

        #  Parking ---------------------------------------
        r += 0
        ws.cell(row=r, column=6, value="Parking Revenue")

        for c, yr in enumerate(revenue_years):
            cell = ws.cell(row=r, column=start_col + c, value=revenue.get(yr, {}).get("parking", 0))
            # cell.font = Font(bold = True, color = "FFFFFF")
            # cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        #  Sweet Equity ---------------------------------------
        r += 3
        cell = ws.cell(row=r, column=6, value="Sweet Equity")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()

        for c, yr in enumerate(revenue_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("sweet_equity", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        #  investor_cashflow ---------------------------------------
        r += 1
        cell = ws.cell(row=r, column=6, value="Investor Cashflow")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()

        for c, yr in enumerate(revenue_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("investor_cashflow", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)


        # levered_cashflow_5
        # -------------------------------------------------
        r += 4
        cell = ws.cell(row=r, column=6, value="Levered Cashflow 5 Year")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()

        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("levered_cashflow_5", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        r += 1
        cell = ws.cell(row=r, column=6, value="Unlevered Cashflow 5 Year")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()

        for c, yr in enumerate(other_years):
            cell = ws.cell(row=r, column=start_col + c, value=other.get(yr, {}).get("unlevered_cashflow_5", 0))
            cell.font = Font(bold = True, color = "FFFFFF")
            cell.fill = PropertyPerformaService.header_fill()
            PropertyPerformaService.currency(cell)

        # EXIT VALUES
        # -------------------------------------------------
        def extract_number(val, key=None):
            if isinstance(val, dict):
                if key and key in val:
                    return val[key]
                return list(val.values())[0]
            return val

        # sales, loan repayment, net proceeds for 5 years ------------------------------------ 
        r += 4
        cell = ws.cell(row=r, column=6, value="Sale Year 5")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.blue_fill()
        cell = ws.cell(row=r, column=start_col, value=extract_number(other.get("sales_year_5", 0)))
        PropertyPerformaService.currency(cell)
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.blue_fill()

        r += 1
        cell = ws.cell(row=r, column=6, value="Loan Repayment Year 5")
        cell.font = Font(bold = True, color = "F20D11")
        cell = ws.cell(row=r, column=start_col, value=-extract_number(other.get("loan_repayment_5", 0), "loan_repayment"))
        PropertyPerformaService.currency(cell)
        cell.font = Font(bold = True, color = "F20D11")


        r += 1
        cell = ws.cell(row=r, column=6, value="Net Proceeds Year 5")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PatternFill(start_color="13EC49", end_color="13EC49", fill_type="solid")
        cell = ws.cell(row=r, column=start_col, value=extract_number(other.get("net_proceeds_5", 0)))
        PropertyPerformaService.currency(cell)
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PatternFill(start_color="13EC49", end_color="13EC49", fill_type="solid")


        # sales, loan repayment, net proceeds for 10 years ------------------------------------ 
        r += 3
        cell = ws.cell(row=r, column=6, value="Sale Year 10")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()
        cell = ws.cell(row=r, column=start_col, value=extract_number(other.get("sales_year_10", 0)))
        PropertyPerformaService.currency(cell)
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PropertyPerformaService.header_fill()

        r += 1
        cell = ws.cell(row=r, column=6, value="Loan Repayment Year 10")
        cell.font = Font(bold = True, color = "F20D11")
        cell = ws.cell(row=r, column=start_col, value=-extract_number(other.get("loan_repayment_10", 0), "loan_repayment"))
        PropertyPerformaService.currency(cell)
        cell.font = Font(bold = True, color = "F20D11")

        r += 1
        cell = ws.cell(row=r, column=6, value="Net Proceeds Year 10")
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PatternFill(start_color="13EC49", end_color="13EC49", fill_type="solid")
        cell = ws.cell(row=r, column=start_col, value=extract_number(other.get("net_proceeds_10", 0)))
        PropertyPerformaService.currency(cell)
        cell.font = Font(bold = True, color = "FFFFFF")
        cell.fill = PatternFill(start_color="13EC49", end_color="13EC49", fill_type="solid")

        r += 9  
        ws.merge_cells(f"F{r}:T{r}")
        cell = ws.cell(row=r, column=6, value=" ** Information contained herein has been obtained from the owners or from other sources deemed reliable. " \
        " We have no reason to doubt its accuracy but regret we cannot guarantee it.")
        cell.font = Font(bold=True, color="F20D11")
        cell.alignment = Alignment(horizontal="center")
        ws.merge_cells(f"F{r+1}:T{r+1}")
        cell = ws.cell(row=r+1, column=6, value=" ** All properties subject to change or withdrawal without notice.")												
        cell.font = Font(bold=True, color="F20D11")
        cell.alignment = Alignment(horizontal="center")

        # SAVE
        # -------------------------------------------------
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        timestamp_ms = int(time.time() * 1000)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{prop.get("property_id","prop")}_proforma_{timestamp_ms}.xlsx"'
            },
        )
    






    