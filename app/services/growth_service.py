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
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import traceback
from typing import Dict, Any
import os
import time
import logging

load_dotenv()
logger = logging.getLogger(__name__)

timestamp_ms = int(time.time() * 1000)


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
                "Content-Disposition": f"attachment; filename=growth_projection{timestamp_ms}.xlsx"
            },
        )



    async def export_income_expense_to_excel(
        rent_summary: dict,
        inc_summary: dict,
        exp_summary: dict,
        filename: str = f"income_expense_summary{timestamp_ms}.xlsx",
    ):
        wb = Workbook()
        ws = wb.active
        ws.title = "Income & Expense Summary"
        header_fill = PatternFill("solid", fgColor="1F4E79")
        cell_fill = PatternFill("solid", fgColor="FF6700")
        header_font = Font(bold=True, color="FFFFFF")
        bold_font = Font(bold=True)
        center = Alignment(horizontal="center")

        def style_header(row):
            for cell in ws[row]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center

        def style_any(row):
            for cell in ws[row]:
                cell.fill = cell_fill
                cell.font = header_font

        def bold_first_three(row):
            for cell in ws[row]:
                if cell.col_idx <= 3:
                    # cell.font = bold_font
                    cell.fill = cell_fill
                    cell.font = header_font
        

        def currency(cell):
            if cell.value not in ("", None):
                cell.number_format = '"$"#,##0'

        ws.merge_cells("A1:H1")
        ws["A1"] = "Income & Expense Summary"
        ws["A1"].font = Font(size=14, bold=True, color="FFFFFF")
        ws["A1"].alignment = center
        ws["A1"].fill = header_fill

        # Unit Table Header
        ws.append([])
        ws.append([])
        ws.append([])
        ws.append(["", "", "", "Current", "", "Potential"])
        ws.merge_cells("D5:E5")
        ws.merge_cells("F5:G5")
        ws["D5"].fill = header_fill
        ws["F5"].fill = header_fill
        ws["D5"].font = header_font
        ws["F5"].font = header_font
        ws["D5"].alignment = center
        ws["F5"].alignment = center

        ws.append([
            "Unit Type",
            "# of Units",
            "Avg/ Sqft",
            "Avg Rent/Sqft",
            "Monthly Rent",
            "Avg Rent/Sqft",
            "Monthly Rent",
        ])
        style_header(ws.max_row)
        # Unit Rows
        total_units = 0
        total_current_rent = 0
        total_potential_rent = 0

        for name, val in rent_summary.items():
            units = val["total_units"]
            avg_sqft = round(val["avg_sqft"], 2)
            current_rent = val["actual_monthly_rent"]
            potential_rent = val["current_monthly_rent"]

            avg_current = current_rent / (units * avg_sqft) if units and avg_sqft else 0
            avg_potential = potential_rent / (units * avg_sqft) if units and avg_sqft else 0

            ws.append([
                name,
                units,
                avg_sqft,
                round(avg_current, 2),
                current_rent,
                round(avg_potential, 2),
                potential_rent,
            ])

            row = ws.max_row
            currency(ws[f"E{row}"])
            currency(ws[f"G{row}"])

            total_units += units
            total_current_rent += current_rent
            total_potential_rent += potential_rent

        ws.append([
            "Total",
            total_units,
            "",
            "",
            total_current_rent,
            "",
            total_potential_rent,
        ])
        style_any(ws.max_row)
        currency(ws[f"E{ws.max_row}"])
        currency(ws[f"G{ws.max_row}"])

        # Income & Expense Header
        ws.append([])
        ws.append([])
        ws.append([])
        ws.append([])
        ws.append(["Income", "Current", "Pro Forma", "", "Expenses", "Current", "Pro Forma", "Per Unit"])
        header_row = ws.max_row
        for cell in ws[header_row]:
            if cell.column_letter != "D":
                cell.fill = header_fill
            cell.font = header_font

        # Income Calculations
        gross_current = inc_summary["Rental Income"]["current_income"]
        gross_proforma = inc_summary["Rental Income"]["proforma_income"]
        vacancy = inc_summary.get("Vacancy", {}).get("proforma_income", 0)
        other_income = inc_summary.get("Other Income", {}).get("current_income", 0)

        total_income_current = gross_current + other_income
        total_income_proforma = gross_proforma - vacancy + other_income

        # Expense Calculations
        total_exp_current = sum(v["current_expense"] for v in exp_summary.values())
        total_exp_proforma = sum(v["proforma_expense"] for v in exp_summary.values())

        per_unit_current = total_exp_proforma / total_units if total_units else 0
        per_unit_proforma = total_exp_proforma / total_units if total_units else 0

        expense_pct_current = (total_exp_current / total_income_current) * 100 if total_income_current else 0
        expense_pct_proforma = (total_exp_proforma / total_income_proforma) * 100 if total_income_proforma else 0

        noi_current = total_income_current - total_exp_current

        # Income Rows
        income_rows = [
            ["Gross Scheduled Rent", gross_current, gross_proforma],
            ["Vacancy", "", -vacancy],
            ["Total Effective Rental Income", gross_current, gross_proforma - vacancy],
            ["Other Income", other_income, other_income],
            ["Gross Income", total_income_current, total_income_proforma],
            ["Less: Expenses", -total_exp_current, -total_exp_proforma],
            ["Net Operating Income", noi_current, noi_current],
        ]

        start_income_row = ws.max_row + 1
        for row_data in income_rows:
            ws.append(row_data)
            r = ws.max_row

            currency(ws[f"B{r}"])
            currency(ws[f"C{r}"])

        bold_first_three(ws.max_row)

        # Expense Rows (side by side)
        start_row = start_income_row
        for i, (name, val) in enumerate(exp_summary.items()):
            row = start_row + i
            ws.cell(row=row, column=5, value=name)
            ws.cell(row=row, column=6, value=val["current_expense"])
            ws.cell(row=row, column=7, value=val["proforma_expense"])
            ws.cell(row=row, column=8, value=val["proforma_expense"] / total_units if total_units else 0)

            currency(ws.cell(row=row, column=6))
            currency(ws.cell(row=row, column=7))
            currency(ws.cell(row=row, column=8))

        # Expense Totals
        ws.append(["", "", "", "", "Total Expenses", total_exp_current, total_exp_proforma, per_unit_current])
        for cell in ws[ws.max_row]:
            if cell.column_letter in ("E", "F", "G", "H"):
                currency(cell)
                cell.fill = cell_fill
                cell.font = header_font

        ws.append(["", "", "", "", "Expense as % of revenue", f"{expense_pct_current:.1f}%", f"{expense_pct_proforma:.1f}%"])
        for cell in ws[ws.max_row]:
            if cell.column_letter in ("E", "F", "G", "H"):
                cell.fill = header_fill
                cell.font = header_font

        ws.append(["", "", "", "", "Net operating Income", noi_current, noi_current])
        for cell in ws[ws.max_row]:
        #     cell.font = bold_font
        # currency(ws[f"F{ws.max_row}"])
        # currency(ws[f"G{ws.max_row}"])
            if cell.column_letter in ("E", "F", "G", "H"):
                currency(cell)
                cell.fill = cell_fill
                cell.font = header_font

        # Auto Column Width
        for col_idx, column_cells in enumerate(ws.columns, start=1):
            max_length = max(len(str(cell.value)) for cell in column_cells if cell.value)
            ws.column_dimensions[get_column_letter(col_idx)].width = max_length + 4

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


