from fastapi import Request, Response, HTTPException, status
# from fastapi.responses import FileResponse
from sqlalchemy.orm import selectinload, joinedload
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.models.property_model import Property, PropertyUnitType, PropertyUnit, PropertyLoan
from decimal import Decimal, getcontext, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
import traceback
import os
import math
import logging
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from app.models.audit_model import AuditModel

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class PropertyLoanService:

    async def add_new_loan_details(db, property_id, data, user_id):

        calculate_other_info = AmortizationScheduleService.calculate_basic_loan_details(data)
        new_load = PropertyLoan(
            loan_id = generate_id("loan"),
            property_id = property_id,
            started_date = data.started_date,
            end_date = data.end_date,
            total_loan_amount = data.total_loan_amount,
            interest_rate = data.interest_rate,
            spread_intrest_rate = data.spread_intrest_rate,
            stabilized_cap_rate = data.stabilized_cap_rate,
            ltv = data.ltv,
            origination_fee = data.origination_fee,
            amortization_period = data.amortization_period,
            term = data.term,
            intrest_only_period = data.intrest_only_period,
            no_of_payments = data.term*12,
            monthly_payments = AmortizationScheduleService.round_half_up(calculate_other_info["emi"]),
            total_annual_payment = AmortizationScheduleService.round_half_up(calculate_other_info["emi"] * 12)
        )
        db.add(new_load)
        audit_log = AuditModel.add_new_logs(
                db = db,
                added_by = user_id,
                new_data = data,
                old_data = None,
                audit_type = "ADD",
                entity_type = "PropertyLoan Management",
                object_id = new_load.loan_id
            )
        db.add(audit_log)
        logger.info("PropertyLoanService: Audit log recorded for new loan.")
        await db.commit()
        await db.refresh(new_load)
        logger.info("PropertyLoanService: loan detials added successfully for the provided property")
        return new_load
    
    
    # async def update_loan_detials(db, loan_id, property_id, data):
    #     loan = await PropertyLoan.get_by_id(db, loan_id, property_id)
    #     if not loan:
    #         raise HTTPException(404, "LoanServices: no any loan found with provided loan_id and property_id")
        
    #     if data.started_date is not None:
    #         loan.started_date = data.started_date

    #     if data.end_date is not None:
    #         loan.end_date = data.end_date

    #     if data.total_loan_amount is not None:
    #         loan.total_loan_amount = data.total_loan_amount

    #     if data.interest_rate is not None:
    #         loan.interest_rate = data.interest_rate

    #     if data.interest_per_period is not None:
    #         loan.interest_per_period = data.interest_per_period

    #     if data.intrest_only_period is not None:
    #         loan.intrest_only_period = data.intrest_only_period

    #     if data.spread_intrest_rate is not None:
    #         loan.spread_intrest_rate = data.spread_intrest_rate

    #     if data.term is not None:
    #         loan.term = data.term

    #     if data.amortization_period is not None:
    #         loan.amortization_period = data.amortization_period

    #     if data.no_of_payments is not None:
    #         loan.no_of_payments = data.no_of_payments

    #     if data.monthly_payments is not None:
    #         loan.monthly_payments = data.monthly_payments

    #     if data.total_annual_payment is not None:
    #         loan.total_annual_payment = data.total_annual_payment

    #     await db.commit()
    #     await db.refresh(loan)
    #     logger.info("LoanServices: loan data updated successfully")
    #     return loan
    

    async def update_loan_detials(db, loan_id, property_id, data, user_id):

        loan = await PropertyLoan.get_by_id(db, loan_id, property_id)
        if not loan:
            raise HTTPException(status_code=404,
                detail="LoanServices: no loan found with provided loan_id and property_id"
            )
        old_data = PropertyLoan.model_to_dict(loan)
        update_fields = [
            "started_date",
            "end_date",
            "total_loan_amount",
            "interest_rate",
            "spread_intrest_rate",
            "intrest_only_period",
            "term",
            "amortization_period",
            "stabilized_cap_rate",
            "origination_fee",
            "ltv",
        ]

        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(loan, field, value)

        calculate_other_info = AmortizationScheduleService.calculate_basic_loan_details(loan)

        loan.no_of_payments = loan.term * 12

        loan.monthly_payments = AmortizationScheduleService.round_half_up(
            calculate_other_info["emi"]
        )

        loan.total_annual_payment = AmortizationScheduleService.round_half_up(
            calculate_other_info["emi"] * 12
        )

        audit_log = AuditModel.add_new_logs(
                db = db,
                added_by = user_id,
                new_data = data,
                old_data = old_data,
                audit_type = "UPDATE",
                entity_type = "PropertyLoan Management",
                object_id = loan_id
            )
        db.add(audit_log)
        logger.info("PropertyLoanService: Audit log recorded for this update in the loan data.")
        await db.commit()
        await db.refresh(loan)

        logger.info("LoanServices: loan data updated successfully")
        return loan



    async def delete_loan_data(db, loan_id, property_id, user_id):
        loan = await PropertyLoan.get_by_id(db, loan_id, property_id)
        if not loan:
            raise HTTPException(404, "LoanServices: no any loan found with provided loan_id and property_id")
        old_data = PropertyLoan.model_to_dict(loan)
        loan.is_deleted = True

        audit_log = AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "PropertyLoan Management",
            object_id = loan_id
            )
        db.add(audit_log)
        logger.info("PropertyLoanService: Audit log recorded for this delete.")
        await db.commit()
        await db.refresh(loan)
        logger.info("PropertyLoanServices: loan details deleted successfully for the provided loan_id and property_id")
        return{
            "message":"PropertyLoanServices: loan details deleted successfully for the provided loan_id and property_id"
        }
    
    async def activate_deactivate_loan_data(db, loan_id, property_id, user_id):
        loan = await PropertyLoan.get_by_id(db, loan_id, property_id)
        new_data = None
        type = None
        if not loan:
            raise HTTPException(404, "LoanServices: no any loan found with provided loan_id and property_id")
        old_data = PropertyLoan.model_to_dict(loan)
        if loan.is_active:
            loan.is_active = False
            type = "ACTIVATE"
        else:
            loan.is_active = True
            type = "DEACTIVATE"

        audit_log = AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = new_data,
            old_data = old_data,
            audit_type = type,
            entity_type = "PropertyLoan Management",
            object_id = loan_id
        )
        db.add(audit_log)
        logger.info("PropertyLoanServices: Audit Log data is for the loan data activate/deactivate.")
        await db.commit()
        await db.refresh(loan)
        logger.info("PropertyLoanServices: loan is_activate is updated successfully for the provided loan_id and property_id")
        return{
            "message":"PropertyLoanServices: loan is_activate is updated successfully for the provided loan_id and property_id"
        }
    
    async def get_loan_detials_for_property(db, loan_id, property_id):
        return await PropertyLoan.get_by_id(db, loan_id, property_id)
    

    async def get_all_loans_details(db):
        stmt = (select(PropertyLoan).where(PropertyLoan.is_active.is_(True), PropertyLoan.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()





class AmortizationScheduleService:

    async def get_all_by_year(db, loan_id, property_id):
        pass


    def round_half_up(value):
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    

    @staticmethod
    def calculate_basic_loan_details(loan_info):

        interest_total_per_year = (
            Decimal(loan_info.interest_rate) +
            Decimal(loan_info.spread_intrest_rate)
        )

        loan_amount = Decimal(loan_info.total_loan_amount)

        monthly_rate = (interest_total_per_year / Decimal(100)) / Decimal(12)

        total_months = int(loan_info.amortization_period) * 12

        if monthly_rate == 0:
            emi = loan_amount / Decimal(total_months)
        else:
            emi = (
                loan_amount * monthly_rate
            ) / (
                Decimal(1) -
                (Decimal(1) + monthly_rate) ** Decimal(-total_months)
            )

        return {
            "interest_total_per_year": interest_total_per_year,
            "loan_amount": loan_amount,
            "monthly_rate": monthly_rate,
            "total_months": total_months,
            "emi": emi
        }


    @staticmethod
    def build_yearly_summary(yearly_data):

        summary = []

        for year, data in yearly_data.items():
            summary.append({
                "year": year,
                "total_principal_paid_year": float(
                    AmortizationScheduleService.round_half_up(data["principal"])
                ),
                "total_interest_paid_year": float(
                    AmortizationScheduleService.round_half_up(data["interest"])
                ),
                "ending_balance_year": float(
                    AmortizationScheduleService.round_half_up(
                        data["ending_balance"] if data["ending_balance"] > 0 else Decimal(0)
                    )
                )
            })

        return summary
    


    @staticmethod
    def generate_amortization_schedule(
        loan_amount,
        monthly_rate,
        emi,
        total_months,
        start_date
    ):

        balance = loan_amount
        years = {}

        # total_principal_paid = Decimal(0)
        # total_interest_paid = Decimal(0)

        for month in range(1, total_months + 1):

            interest_amount = balance * monthly_rate
            principal_paid = emi - interest_amount
            ending_balance = balance - principal_paid

            payment_date = start_date + relativedelta(months=month)

            # total_principal_paid += principal_paid
            # total_interest_paid += interest_amount

            year_number = (month - 1) // 12 + 1

            if year_number not in years:
                years[year_number] = {
                    "year": year_number,
                    "total_principal_paid_year": Decimal(0),
                    "total_interest_paid_year": Decimal(0),
                    "ending_balance_year": Decimal(0),
                    "months": []
                }

            # accumulate yearly
            years[year_number]["total_principal_paid_year"] += principal_paid
            years[year_number]["total_interest_paid_year"] += interest_amount
            years[year_number]["ending_balance_year"] = ending_balance

            # append month inside year
            years[year_number]["months"].append({
                "month": month,
                "payment_date": payment_date.strftime("%Y-%m-%d"),
                "beginning_balance": float(
                    AmortizationScheduleService.round_half_up(balance)
                ),
                "monthly_payment": float(
                    AmortizationScheduleService.round_half_up(emi)
                ),
                "interest_amount": float(
                    AmortizationScheduleService.round_half_up(interest_amount)
                ),
                "principal_paid": float(
                    AmortizationScheduleService.round_half_up(principal_paid)
                ),
                "ending_balance": float(
                    AmortizationScheduleService.round_half_up(
                        ending_balance if ending_balance > 0 else Decimal(0)
                    )
                )
            })

            balance = ending_balance

            if balance <= 0:
                break

        # Final formatting (round yearly values)
        formatted_years = []

        for year_data in years.values():
            formatted_years.append({
                "year": year_data["year"],
                "total_principal_paid_year": float(
                    AmortizationScheduleService.round_half_up(
                        year_data["total_principal_paid_year"]
                    )
                ),
                "total_interest_paid_year": float(
                    AmortizationScheduleService.round_half_up(
                        year_data["total_interest_paid_year"]
                    )
                ),
                "ending_balance_year": float(
                    AmortizationScheduleService.round_half_up(
                        year_data["ending_balance_year"]
                        if year_data["ending_balance_year"] > 0
                        else Decimal(0)
                    )
                ),
                "months": year_data["months"]
            })

        return {
            "years": formatted_years,
            # "total_principal_paid": total_principal_paid,
            # "total_interest_paid": total_interest_paid
        }



    async def get_all(db, loan_id, property_id):

        loan_info = await PropertyLoanService.get_loan_detials_for_property(
            db, loan_id, property_id
        )

        if not loan_info:
            raise HTTPException(
                status_code=404,
                detail="Loan info not found to calculate the amortization schedule details"
            )

        getcontext().prec = 28

        # Step 1: Basic loan calculation
        basic = AmortizationScheduleService.calculate_basic_loan_details(loan_info)

        # Step 2: Generate schedule
        schedule_data = AmortizationScheduleService.generate_amortization_schedule(
            basic["loan_amount"],
            basic["monthly_rate"],
            basic["emi"],
            basic["total_months"],
            loan_info.started_date
        )


        return {
            "loan_amount": float(basic["loan_amount"]),
            "annual_interest_rate": float(basic["interest_total_per_year"]),
            "monthly_interest_rate" : float(basic["monthly_rate"]*100),
            "monthly_payment": float(
                AmortizationScheduleService.round_half_up(basic["emi"])
            ),
            "yearly_payment": float(
                AmortizationScheduleService.round_half_up(basic["emi"] * 12)
            ),
            "total_months": basic["total_months"],
            # "total_principal_paid": float(
            #     AmortizationScheduleService.round_half_up(
            #         schedule_data["total_principal_paid"]
            #     )
            # ),
            # "total_interest_paid": float(
            #     AmortizationScheduleService.round_half_up(
            #         schedule_data["total_interest_paid"]
            #     )
            # ),
            # "yearly_summary": yearly_summary,
            # "schedule": schedule_data["schedule"]
            "years": schedule_data["years"],
        }


    async def export_to_sheet(db, loan_id, property_id):
        data = await AmortizationScheduleService.get_all(db, loan_id, property_id)

        return AmortizationScheduleService.export_debt_schedule_excel(
            data, loan_id
        )


    def export_debt_schedule_excel(data: dict, loan_id: str):

        wb = Workbook()
        ws = wb.active
        ws.title = "Debt Schedule"

        styles = AmortizationScheduleService._create_styles()

        row = 1
        row = AmortizationScheduleService._add_main_title(ws, row, styles)
        row = AmortizationScheduleService._add_loan_info_block(ws, row, data, styles)
        row = AmortizationScheduleService._add_10_year_summary(ws, row, data, styles)
        row = AmortizationScheduleService._add_fye_summary(ws, row, data, styles)
        row = AmortizationScheduleService._add_amortization_schedule(ws, row, data, styles)

        AmortizationScheduleService._auto_adjust_columns(ws)
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={loan_id}_amortization_schedule.xlsx"
            },
        )



    def _create_styles():
        return {
            "blue_fill": PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid"),
            "light_gray": PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid"),
            "white_bold": Font(color="FFFFFF", bold=True),
            "bold": Font(bold=True),
            "header": Font(bold=True),
            "center": Alignment(horizontal="center", vertical="center"),
            "right": Alignment(horizontal="right"),
            "border": Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )
        }

    def _add_main_title(ws, row, styles):
        ws.merge_cells(f"A{row}:J{row}")
        cell = ws[f"A{row}"]
        cell.value = "Debt Schedule"
        cell.font = styles["white_bold"]
        cell.fill = styles["blue_fill"]
        cell.alignment = styles["center"]
        ws.row_dimensions[row].height = 25
        return row + 2


    def _add_loan_info_block(ws, row, data, styles):

        left_info = [
            ("1st Mortgage", data["loan_amount"]),
            ("Interest Rate", f"{data['annual_interest_rate']}%"),
            ("Interest per Period", f"{round(data['monthly_interest_rate'],2)}%"),
            ("Amortization Period", int(data["total_months"]/12)),
            ("Number of Payments", data["total_months"]),
            ("Monthly Payment", data["monthly_payment"]),
            ("Total Annual Payment", data["yearly_payment"]),
        ]

        right_info = [
            ("Term:", "10 Years"),
            ("Start Date:", data["years"][0]["months"][0]["payment_date"]),
        ]

        for i, (label, value) in enumerate(left_info):
            ws[f"A{row+i}"] = label
            ws[f"A{row+i}"].font = styles["bold"]
            ws[f"B{row+i}"] = value

        for i, (label, value) in enumerate(right_info):
            ws[f"E{row+i}"] = label
            ws[f"F{row+i}"] = value

        return row + max(len(left_info), len(right_info)) + 2



    def _add_10_year_summary(ws, row, data, styles):

        years = data["years"][:10] 

        ws.merge_cells(f"A{row}:E{row}")
        cell = ws[f"A{row}"]
        cell.value = "Fixed-Rate 10-Year Loan"
        cell.font = styles["white_bold"]
        cell.fill = styles["blue_fill"]
        cell.alignment = styles["center"]

        row += 1

        headers = ["Year", "Interest", "Principal", "Balance", "Payment"]

        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=h)
            cell.font = styles["header"]
            cell.fill = styles["light_gray"]
            cell.border = styles["border"]
            cell.alignment = styles["center"]

        row += 1

        for y in years:
            ws.cell(row=row, column=1, value=y["year"]).border = styles["border"]
            ws.cell(row=row, column=2, value=y["total_interest_paid_year"]).border = styles["border"]
            ws.cell(row=row, column=3, value=y["total_principal_paid_year"]).border = styles["border"]
            ws.cell(row=row, column=4, value=y["ending_balance_year"]).border = styles["border"]
            ws.cell(row=row, column=5, value=data["yearly_payment"]).border = styles["border"]
            row += 1

        return row + 2


    def _add_fye_summary(ws, row, data, styles):

        years = data["years"][:10]

        ws.merge_cells(f"A{row}:K{row}")
        header_cell = ws[f"A{row}"]
        header_cell.value = "Fixed-Rate 10-Year Loan"
        header_cell.font = styles["white_bold"]
        header_cell.fill = styles["blue_fill"]
        header_cell.alignment = styles["center"]

        row += 1
        ws.cell(row=row, column=1, value="")

        col = 2
        for y in years:
            cell = ws.cell(row=row, column=col, value=f"FYE {y['year']}")
            cell.font = styles["bold"]
            cell.fill = styles["light_gray"]
            cell.border = styles["border"]
            cell.alignment = styles["center"]
            col += 1

        row += 1
        ws.cell(row=row, column=1, value="Principal").font = styles["bold"]

        col = 2
        for y in years:
            cell = ws.cell(row=row, column=col, value=y["total_principal_paid_year"])
            cell.border = styles["border"]
            col += 1

        row += 1
        ws.cell(row=row, column=1, value="Interest").font = styles["bold"]

        col = 2
        for y in years:
            cell = ws.cell(row=row, column=col, value=y["total_interest_paid_year"])
            cell.border = styles["border"]
            col += 1

        row += 1
        ws.cell(row=row, column=1, value="Total Payment").font = styles["bold"]

        col = 2
        for _ in years:
            cell = ws.cell(row=row, column=col, value=data["yearly_payment"])
            cell.border = styles["border"]
            col += 1

        row += 1
        ws.cell(row=row, column=1, value="Balance").font = styles["bold"]

        col = 2
        for y in years:
            cell = ws.cell(row=row, column=col, value=y["ending_balance_year"])
            cell.border = styles["border"]
            col += 1

        row += 1

        return row + 1



    def _add_amortization_schedule(ws, row, data, styles):

        ws.merge_cells(f"A{row}:H{row}")
        cell = ws[f"A{row}"]
        cell.value = "Amortization Schedule"
        cell.font = styles["white_bold"]
        cell.fill = styles["blue_fill"]
        cell.alignment = styles["center"]

        row += 1

        headers = [
            "Year", "Month Name", "Month No",
            "Beginning Balance", "PMT",
            "Interest", "Principal", "Loan Balance"
        ]

        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=h)
            cell.font = styles["header"]
            cell.fill = styles["light_gray"]
            cell.border = styles["border"]

        row += 1

        for y in data["years"]:
            for m in y["months"]:
                ws.cell(row=row, column=1, value=y["year"]).border = styles["border"]
                ws.cell(row=row, column=2, value=m["payment_date"]).border = styles["border"]
                ws.cell(row=row, column=3, value=m["month"]).border = styles["border"]
                ws.cell(row=row, column=4, value=m["beginning_balance"]).border = styles["border"]
                ws.cell(row=row, column=5, value=m["monthly_payment"]).border = styles["border"]
                ws.cell(row=row, column=6, value=m["interest_amount"]).border = styles["border"]
                ws.cell(row=row, column=7, value=m["principal_paid"]).border = styles["border"]
                ws.cell(row=row, column=8, value=m["ending_balance"]).border = styles["border"]
                row += 1

        return row


    def _auto_adjust_columns(ws):
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max_length + 3



















        

    # async def add_new_amortization_schedule(db, loan_id, property_id, data):
    #     loan_data = await PropertyLoanService.get_loan_detials_for_property(db, loan_id, property_id)
    #     if not loan_data:
    #         raise HTTPException(404, "AmortizationScheduleService: Loan Data not found with the provided property_id and loan_id please correct the ids")
    #     amort_schedule = AmortizationSchedule(
    #         amortization_id = generate_id("amort"),
    #         property_id =property_id,
    #         loan_id = loan_id,
    #         year = data.year,
    #         month = data.month,
    #         principal_amount = data.principal_amount,
    #         PMT = data.PMT,   # PMT means might be Payment(monthly against the loan)
    #         interest = data.interest,
    #         principal_paid = data.principal_paid,
    #         loan_balance = data.loan_balance
    #     )

    #     db.add(amort_schedule)
    #     await db.commit()
    #     await db.refresh(amort_schedule)
    #     logger.info("AmortizationScheduleService: amortization schedule data created successfully.")
    #     return amort_schedule
    


    # async def update_amortization_schedule(db, amortization_id, loan_id, property_id, data):
    #     schedule = await AmortizationSchedule.get_by_id(db, amortization_id, loan_id, property_id)
    #     if not schedule:
    #         raise HTTPException(404, "AmortizationScheduleService: AmortizationSchedule data not found using these amortization_id, loan_id, property_id detials ")

    #     if data.year is not None:
    #         schedule.year = data.year

    #     if data.month is not None:
    #         schedule.month = data.month

    #     if data.principal_amount is not None:
    #         schedule.principal_amount = data.principal_amount

    #     if data.PMT is not None:
    #         schedule.PMT = data.PMT

    #     if data.interest is not None:
    #         schedule.interest = data.interest

    #     if data.principal_paid is not None:
    #         schedule.principal_paid = data.principal_paid
        
    #     if data.loan_balance is not None:
    #         schedule.loan_balance = data.loan_balance

    #     await db.commit()
    #     await db.refresh(schedule)
    #     logger.info("AmortizationScheduleService: amortization schedule data updated successfully.")
    #     return schedule



    # async def delete_amortization_schedule(db, amortization_id, loan_id, property_id):
    #     schedule = await AmortizationSchedule.get_by_id(db, amortization_id, loan_id, property_id)
    #     if not schedule:
    #         raise HTTPException(404, "AmortizationScheduleService: AmortizationSchedule data not found using these amortization_id, loan_id, property_id detials.")
    #     schedule.is_deleted = True
    #     await db.commit()
    #     await db.refresh(schedule)
    #     return{
    #         "message": "AmortizationSchedule data is deleted successfully."
    #     }
    

    # async def get_all(db, loan_id, property_id, year):
    #     stmt = (
    #         select(AmortizationSchedule)
    #         .where(
    #             AmortizationSchedule.loan_id == loan_id,
    #             AmortizationSchedule.property_id == property_id,
    #             AmortizationSchedule.year == year,
    #             AmortizationSchedule.is_deleted.is_(False),
    #         )
    #         .order_by(
    #             AmortizationSchedule.month,
    #         )
    #     )

    #     result = await db.execute(stmt)
    #     records = result.scalars().all()

    #     if not records:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="AmortizationSchedules data not found with these loan_id, property_id details."
    #         )

    #     return records


    # async def get_one(db, amortization_id, loan_id, property_id):
    #     stmt = (
    #         select(AmortizationSchedule)
    #         .where(
    #             AmortizationSchedule.amortization_id == amortization_id,
    #             AmortizationSchedule.loan_id == loan_id,
    #             AmortizationSchedule.property_id == property_id,
    #             AmortizationSchedule.is_deleted.is_(False),
    #         )
    #     )
    #     result = await db.execute(stmt)
    #     record = result.scalar_one_or_none()
    #     if not record:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="AmortizationSchedules data not found with these amortization_id, loan_id, property_id details."
    #         )
    #     return record
    

    # async def mark_paid_the_amortization(db, amortization_id, loan_id, property_id, data):
    #     schedule = await AmortizationSchedule.get_by_id(db, amortization_id, loan_id, property_id)
    #     if not schedule:
    #         raise HTTPException(404, "AmortizationScheduleService: AmortizationSchedule data not found using these amortization_id, loan_id, property_id detials.")
    #     schedule.is_paid = data.is_paid
    #     schedule.paid_date = data.paid_date
    #     await db.commit()
    #     await db.refresh(schedule)
    #     return{
    #         "message":f"AmortizationScheduleService: AmortizationSchedule payment marked for this amortization_id: {amortization_id}."
    #     }


    # async def mark_unpaid_the_amortization(db, amortization_id, loan_id, property_id, data):
    #     schedule = await AmortizationSchedule.get_by_id(db, amortization_id, loan_id, property_id)
    #     if not schedule:
    #         raise HTTPException(404, "AmortizationScheduleService: AmortizationSchedule data not found using these amortization_id, loan_id, property_id detials.")
    #     schedule.is_paid = data.is_paid
    #     schedule.paid_date = None
    #     await db.commit()
    #     await db.refresh(schedule)
    #     return{
    #         "message":f"AmortizationScheduleService: AmortizationSchedule payment un-marked for this amortization_id: {amortization_id}."
    #     }

