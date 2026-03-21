from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models.expenses_model import ExpenseTypes, Expense, ExpenseGrowth
from app.models.audit_model import AuditModel
from app.services.income_service import IncomeTypeService
from app.services.expense_service import ExpenseTypeService
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class IncomeExpanseGrowthService:

    async def export_growth_assumption(db, property_id):
        expense_data = await ExpenseTypeService.get_property_all_expense_details(db, property_id)
        income_data =await IncomeTypeService.get_property_all_income_details(db, property_id)

        return {
            "expense_info" : expense_data,
            "income_info": income_data
        }

    async def create_growth_projection_excel(db, property_id):
        data = await IncomeExpanseGrowthService.export_growth_assumption(db, property_id)

        wb = Workbook()
        ws = wb.active
        ws.title = "Growth Projections"

        # ===================== TITLE =====================
        ws.merge_cells("A1:N1")
        ws["A1"] = "GROWTH RATE PROJECTIONS"
        ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
        ws["A1"].alignment = Alignment(horizontal="center")
        ws["A1"].fill = PatternFill("solid", fgColor="1F4E79")

        # ===================== INCOME HEADER =====================
        header_row = 3

        ws.cell(row=header_row, column=1, value="Income Type")
        ws.cell(row=header_row, column=2, value="Current")

        ws.cell(row=header_row, column=1).fill = PatternFill("solid", fgColor="ED7D31")
        ws.cell(row=header_row, column=2).fill = PatternFill("solid", fgColor="ED7D31")
        ws.cell(row=header_row, column=1).font = Font(bold=True, color="FFFFFF")
        ws.cell(row=header_row, column=2).font = Font(bold=True, color="FFFFFF")

        # Year columns
        for year in range(1, 12):
            col = year + 2
            ws.cell(row=header_row, column=col, value=f"Year {year}")
            ws.cell(row=header_row, column=col).fill = PatternFill("solid", fgColor="ED7D31")
            ws.cell(row=header_row, column=col).font = Font(bold=True, color="FFFFFF")

        # ===================== INCOME DATA =====================
        row = 4

        for income in data.get("income_info", []):
            ws.cell(row=row, column=1, value=income.get("income_type_name"))

            incomes = income.get("incomes", [])
            if incomes:
                info = incomes[0]

                # Current income
                if income.get("income_type_name") == "Total Revenue":
                    ws.cell(row=row, column=2, value=info.get("current_income", 0))
                else:
                    ws.cell(row=row, column=2, value=info.get("pro_forma_income", 0))

                # Growth %
                for g in info.get("income_growth", []):
                    col = g["year"] + 2
                    ws.cell(row=row, column=col, value=g.get("growth_percentage", 0) / 100)

            else:
                ws.cell(row=row, column=2, value=0)

            row += 1

        # ===================== EXPENSE HEADER =====================
        row += 1
        expense_header_row = row

        ws.cell(row=expense_header_row, column=1, value="Expense Type")
        ws.cell(row=expense_header_row, column=2, value="Current")

        ws.cell(row=expense_header_row, column=1).fill = PatternFill("solid", fgColor="ED7D31")
        ws.cell(row=expense_header_row, column=2).fill = PatternFill("solid", fgColor="ED7D31")
        ws.cell(row=expense_header_row, column=1).font = Font(bold=True, color="FFFFFF")
        ws.cell(row=expense_header_row, column=2).font = Font(bold=True, color="FFFFFF")

        for year in range(1, 12):
            col = year + 2
            ws.cell(row=expense_header_row, column=col, value=f"Year {year}")
            ws.cell(row=expense_header_row, column=col).fill = PatternFill("solid", fgColor="ED7D31")
            ws.cell(row=expense_header_row, column=col).font = Font(bold=True, color="FFFFFF")

        row += 1

        # ===================== EXPENSE DATA =====================
        for expense in data.get("expense_info", []):
            ws.cell(row=row, column=1, value=expense.get("expense_type_name"))

            expenses = expense.get("expenses", [])
            if expenses:
                info = expenses[0]

                # Current expense
                ws.cell(row=row, column=2, value=info.get("pro_forma_expense", 0))

                # Growth %
                for g in info.get("expense_growth", []):
                    col = g["year"] + 2
                    ws.cell(row=row, column=col, value=g.get("growth_percentage", 0) / 100)

            else:
                ws.cell(row=row, column=2, value=0)

            row += 1

        # ===================== FORMATTING =====================
        for r in range(4, row):
            ws.cell(r, 2).number_format = '"$"#,##0'

            for c in range(3, 14):
                ws.cell(r, c).number_format = '0.00%'

        # Column widths
        ws.column_dimensions["A"].width = 28
        ws.column_dimensions["B"].width = 16

        for col in range(3, 14):
            ws.column_dimensions[get_column_letter(col)].width = 12

        # ===================== SAVE TO STREAM =====================
        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)

        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=growth_projection.xlsx"
            },
        )


        