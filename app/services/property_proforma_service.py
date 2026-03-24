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
from openpyxl.utils import get_column_letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_DOWN
from typing import Dict, Any
import logging
from collections import defaultdict

getcontext().prec = 28
logger = logging.getLogger(__name__)

ORANGE = "F79646"
BLUE = "1F4E78"
LIGHT_GRAY = "D9D9D9"


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



    async def get_all_revenue(db, property_id, is_for_noi = None):

        data_response = await IncomeType.get_property_income_details(db, property_id)

        rental_projection = {}
        other_projection = {}
        parking_projection = {}
        vacancy_growth = {}
        total_revenue_growth = {}

        for income_type in data_response:

            name = income_type["income_type_name"].strip().lower()

            for income in income_type.get("incomes", []):

                current = Decimal(str(income.get("current_income", 0)))
                proforma = Decimal(str(income.get("pro_forma_income", 0)))
                growth_data = sorted(
                    income.get("income_growth", []),
                    key=lambda x: x["year"]
                )

                # ---------------- VACANCY ----------------
                if name == "vacancy":
                    for g in growth_data:
                        vacancy_growth[g["year"]] = Decimal(
                            str(g["growth_percentage"])
                        )
                    continue

                # ---------------- TOTAL REVENUE GROWTH % ----------------
                if name == "total revenue":
                    for g in growth_data:
                        total_revenue_growth[g["year"]] = Decimal(
                            str(g["growth_percentage"])
                        )
                    continue

                # ---------------- RENTAL ----------------
                if name == "rental income":
                    rental_projection[0] = current
                    rental_projection[1] = proforma

                    for g in growth_data:
                        year = g["year"]
                        if year <= 1:
                            continue

                        prev = rental_projection[year - 1]
                        growth_percent = Decimal(str(g["growth_percentage"]))

                        rental_projection[year] = prev + (
                            prev * growth_percent / Decimal("100")
                        )

                # ---------------- OTHER (FIXED HERE) ----------------
                elif name == "other income":

                    # Year 0 = current
                    other_projection[0] = current

                    for g in growth_data:
                        year = g["year"]

                        # Year 1 grows from Year 0
                        if year == 1:
                            prev = current
                        else:
                            prev = other_projection.get(year - 1, current)

                        growth_percent = Decimal(str(g["growth_percentage"]))

                        other_projection[year] = prev + (
                            prev * growth_percent / Decimal("100")
                        )

                # ---------------- PARKING ----------------
                elif name == "parking":

                    parking_projection[0] = current

                    for g in growth_data:
                        year = g["year"]

                        if year == 1:
                            prev = current
                        else:
                            prev = parking_projection.get(year - 1, current)

                        growth_percent = Decimal(str(g["growth_percentage"]))

                        parking_projection[year] = prev + (
                            prev * growth_percent / Decimal("100")
                        )

        # ---------------- FINAL RESULT ----------------
        final_projection = {}
        previous_total = None

        for year in range(0, 12):

            rental = rental_projection.get(year, Decimal("0"))
            other = other_projection.get(year, Decimal("0"))
            parking = parking_projection.get(year, Decimal("0"))

            gross = rental + other + parking

            vacancy_percent = vacancy_growth.get(year, Decimal("0"))
            vacancy_amount = rental * vacancy_percent / Decimal("100")

            if year in (0, 1):
                total = gross - vacancy_amount
                previous_total = total
            else:
                growth_percent = total_revenue_growth.get(year, Decimal("0"))
                total = previous_total + (
                    previous_total * growth_percent / Decimal("100")
                )
                previous_total = total

            if is_for_noi is not None:
                final_projection[year] = {
                    "total_revenue": total,
                }
            else:
                final_projection[year] = {
                    "rental_income": PropertyPerformaService.round_half_up(rental),
                    "other_income": PropertyPerformaService.round_half_up(other),
                    "parking_income": PropertyPerformaService.round_half_up(parking),
                    "gross_income": PropertyPerformaService.round_half_up(gross),
                    "vacancy": PropertyPerformaService.round_half_up(-vacancy_amount),
                    "total_revenue": PropertyPerformaService.round_half_up(total),
                }
        
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
    async def get_noi_opex_and_other_detials(db, property_id, investment_required=None):
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
                "levered_cashflow_5": cash_flow
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

        if 5 in noi_output:
            noi_output[5]["levered_cashflow_5"] = net_proceeds_5

        # Clear years after exit (5-year scenario) --------------------------
        for year in range(6, 12):
            if year in noi_output:
                noi_output[year]["levered_cashflow_5"] = Decimal("0")

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
        revenue_detials = await PropertyPerformaService.get_all_revenue(db, property_id)
        expense_detials = await PropertyPerformaService.calculate_all_expenses(db, property_id)
        other_detials = await PropertyPerformaService.get_noi_opex_and_other_detials(db, property_id, investment_required)
        rent_summary = await PropertyPerformaService.get_performa_rent_per_year(db, property_id)

        return {
            "property_detials":property_detials,
            "revenue_detials":revenue_detials,
            "expense_detials":expense_detials,
            "other_detials":other_detials,
            "rent_summary": rent_summary
        }







#  10 year performa sheet code written here -------------------------

    def _header_fill():
        return PatternFill(start_color=ORANGE, end_color=ORANGE, fill_type="solid")


    def _blue_fill():
        return PatternFill(start_color=BLUE, end_color=BLUE, fill_type="solid")


    def _thin_border():
        return Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
    

    async def generate_real_estate_excel(db, property_id):
        data = await PropertyPerformaService.get_overall_performa_sumary(db, property_id)

        if not data:
            raise HTTPException(400, "Property not found")

        revenue = {str(k): v for k, v in data["revenue_detials"].items()}
        expense = {str(k): v for k, v in data["expense_detials"].items()}
        other = {str(k): v for k, v in data["other_detials"].items()}
        rent_summary = {str(k): v for k, v in data["rent_summary"].items()}
        prop = data["property_detials"]

        wb = Workbook()
        ws = wb.active
        ws.title = "ProForma"

        # =========================================================
        # COLUMN WIDTH
        # =========================================================
        for col in range(1, 20):
            ws.column_dimensions[get_column_letter(col)].width = 16

        # =========================================================
        # PROPERTY HEADER
        # =========================================================
        ws.merge_cells("A1:N1")
        cell = ws["A1"]
        cell.value = prop["property_name"]
        cell.font = Font(size=14, bold=True)

        # =========================================================
        # YEAR HEADER ROW
        # =========================================================
        year_row = 4
        ws.cell(row=year_row, column=1, value="Current")

        year_cols = sorted(revenue.keys(), key=lambda x: int(x))
        for idx, yr in enumerate(year_cols):
            ws.cell(row=year_row, column=3 + idx, value=f"Year {yr}")

        # =========================================================
        # REVENUE SECTION
        # =========================================================
        revenue_start = 6

        ws.cell(row=revenue_start, column=1, value="Revenue").fill = PropertyPerformaService._blue_fill()
        ws.cell(row=revenue_start, column=1).font = Font(color="FFFFFF", bold=True)

        labels = [
            ("Rental Income", "rental_income"),
            ("Other Income", "other_income"),
            ("Vacancy", "vacancy"),
            ("Total Revenue", "total_revenue"),
        ]

        for i, (label, key) in enumerate(labels):
            r = revenue_start + 1 + i
            ws.cell(row=r, column=1, value=label)

            for c, yr in enumerate(year_cols):
                ws.cell(row=r, column=3 + c, value=revenue[yr].get(key, 0))

        # =========================================================
        # EXPENSE SECTION
        # =========================================================
        expense_start = revenue_start + 7

        ws.cell(row=expense_start, column=1, value="Expenses").fill = PropertyPerformaService._blue_fill()
        ws.cell(row=expense_start, column=1).font = Font(color="FFFFFF", bold=True)

        expense_rows = [
            ("Gas", "Gas"),
            ("Water", "Water"),
            ("Hydro", "Hydro"),
            ("Insurance", "Insurance"),
            ("Real Estate Taxes", "Real Estate Taxes"),
            ("Repairs & Maintenance", "Repaires & Maintenance"),
            ("Management Fee", "Management Fee"),
            ("Capital Expenditures", "CapEx"),
            ("Total Expenses", "total_expanse"),
        ]

        for i, (label, key) in enumerate(expense_rows):
            r = expense_start + 1 + i
            ws.cell(row=r, column=1, value=label)

            for c, yr in enumerate(year_cols):
                ws.cell(row=r, column=3 + c, value=expense[yr].get(key, 0))

        #  opex ratio here ====================

        opex_start = expense_start + 11
        ws.cell(row=opex_start, column=1, value="Opex Ratio").fill = PropertyPerformaService._header_fill()

        for c, yr in enumerate(year_cols):
            ws.cell(
                row=opex_start,
                column=3 + c,
                value=other[yr]["opex_ratio"],
            )

        # =========================================================
        # NOI SECTION
        # =========================================================
        noi_start = opex_start + 3

        ws.cell(row=noi_start, column=1, value="Net Operating Income").fill = PropertyPerformaService._header_fill()

        for c, yr in enumerate(year_cols):
            ws.cell(
                row=noi_start,
                column=3 + c,
                value=other[yr]["noi"],
            )

        # =========================================================
        # DEBT SECTION
        # =========================================================
        debt_start = noi_start + 3

        ws.cell(row=debt_start, column=1, value="Debt Payments")

        for c, yr in enumerate(year_cols):
            ws.cell(row=debt_start, column=3 + c, value=other[yr]["debt_payment"])

        ws.cell(row=debt_start + 1, column=1, value="DSCR")
        for c, yr in enumerate(year_cols):
            ws.cell(row=debt_start + 1, column=3 + c, value=other[yr]["dscr"])

        ws.cell(row=debt_start + 2, column=1, value="Cash Flow After Financing")
        for c, yr in enumerate(year_cols):
            ws.cell(
                row=debt_start + 2,
                column=3 + c,
                value=other[yr]["cash_flow_after_financing"],
            )

        # =========================================================
        # RENT SUMMARY
        # =========================================================
        rent_start = debt_start + 5

        ws.cell(row=rent_start, column=1, value="Rent Summary").fill = PropertyPerformaService._blue_fill()
        ws.cell(row=rent_start, column=1).font = Font(color="FFFFFF", bold=True)

        first_year = next(iter(rent_summary))
        unit_types = rent_summary[first_year].keys()

        for i, unit in enumerate(unit_types):
            r = rent_start + 1 + i
            ws.cell(row=r, column=1, value=unit)

            for c, yr in enumerate(year_cols):
                ws.cell(row=r, column=3 + c, value=rent_summary[yr].get(unit, 0))


        equity_start = rent_start + 3

        ws.cell(row=equity_start, column=1, value="Sweet Equity").fill = PropertyPerformaService._header_fill()

        for c, yr in enumerate(year_cols):
            ws.cell(
                row=equity_start,
                column=3 + c,
                value=other[yr]["sweet_equity"],
            )

        cashflow_start = equity_start + 2

        ws.cell(row=cashflow_start, column=1, value="Investor Cashflow").fill = PropertyPerformaService._header_fill()

        for c, yr in enumerate(year_cols):
            ws.cell(
                row=cashflow_start,
                column=3 + c,
                value=other[yr]["sweet_equity"],
            )


        levered_start_10 = cashflow_start + 2
        ws.cell(row=levered_start_10, column=1, value="Levered Cashflow").fill = PropertyPerformaService._header_fill()

        for c, yr in enumerate(year_cols):
            ws.cell(
                row=levered_start_10,
                column=3 + c,
                value=other[yr]["levered_cashflow_10"],
            )

        
        levered_start_5 = cashflow_start + 4
        ws.cell(row=levered_start_5, column=1, value="Levered Cashflow").fill = PropertyPerformaService._header_fill()

        for c, yr in enumerate(year_cols):
            ws.cell(
                row=levered_start_5,
                column=3 + c,
                value=other[yr]["levered_cashflow_5"],
            )

        # =========================================================
        # EXIT VALUES
        # =========================================================
        exit_row = levered_start_5 + 6

        ws.cell(row=exit_row, column=1, value="Sale Year 5")
        ws.cell(row=exit_row, column=3, value=other["sales_year_5"])

        ws.cell(row=exit_row + 1, column=1, value="Net Proceeds Year 5")
        ws.cell(row=exit_row + 1, column=3, value=other["net_proceeds_5"])

        ws.cell(row=exit_row + 3, column=1, value="Sale Year 10")
        ws.cell(row=exit_row + 3, column=3, value=other["sales_year_10"])

        ws.cell(row=exit_row + 4, column=1, value="Net Proceeds Year 10")
        ws.cell(row=exit_row + 4, column=3, value=other["net_proceeds_10"])

        # =========================================================
        # SAVE
        # =========================================================
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{prop["property_id"]}_proforma.xlsx"'
            },
        )

