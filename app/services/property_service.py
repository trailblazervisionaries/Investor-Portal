from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.utils_functions import generate_id
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.audit_model import AuditModel
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from io import BytesIO
from fastapi.responses import StreamingResponse
from openpyxl.utils import get_column_letter
from decimal import Decimal, ROUND_HALF_UP
from app.models.property_model import Property, PropertyUnitType, PropertyUnit
import traceback
import time
import os
import logging


logger = logging.getLogger(__name__)
timestamp_ms = int(time.time() * 1000)

class PropertyService:

    async def add_new_property(db, user_id, data):

        new_property = Property(
            property_id = generate_id(data.name),
            added_by = user_id,
            name = data.name,
            description = data.description,
            risk_status = data.risk_status,
            purchase_price = data.purchase_price,
            closing_cost = data.closing_cost,
            loan_amount = data.loan_amount,
            market_cap_rate = data.market_cap_rate,
            cap_rate_flactuation = data.cap_rate_flactuation,
            property_type= data.property_type,
            total_area = data.total_area,
            pro_forma_start_date = data.pro_forma_start_date,
            total_investment_required = data.total_investment_required,
            available_required_for_investment = data.available_required_for_investment,
            gp_equity_stake = data.gp_equity_stake,
            hurdle = data.hurdle,
            go_promote_at_hurdle = data.go_promote_at_hurdle,
            go_promote_above_hurdle = data.go_promote_above_hurdle,
            address_line_1 = data.address_line_1,
            address_line_2 = data.address_line_2,
            city = data.city,
            province = data.province,
            country = data.country,
            postal_code = data.postal_code
        )

        db.add(new_property)
        await db.flush()
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(mode='json'),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Property Management",
            object_id = new_property.property_id
        )
        await db.commit()
        await db.refresh(new_property)
        logger.info("PropertyServices: property data is stored successfully")
        return new_property
    
    async def update_property(db, user_id, property_id, data):

        property_obj = await Property.get_by_id(db, property_id)
        if not property_obj:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property_obj)
        allowed_fields = {
            "name", "description", "risk_status", "purchase_price", "closing_cost",
            "loan_amount", "market_cap_rate", "cap_rate_flactuation","pro_forma_start_date",
            "property_type", "total_area", "total_investment_required",
            "gp_equity_stake", "hurdle", "go_promote_at_hurdle", "go_promote_above_hurdle"
            "available_required_for_investment", "address_line_1",
            "address_line_2", "city", "province", "country", "postal_code"
        }

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(property_obj, field, value)

        property_obj.updated_by = user_id

        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(mode='json'),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property_obj.property_id
        )

        await db.commit()
        await db.refresh(property_obj)

        logger.info("PropertyServices: property data is updated successfully")

        return property_obj

    

    async def delete_property(db, property_id, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        property.is_deleted = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property deleted successfully")
        return {"message ": "PropertyServices: property deleted successfully"}


    
    async def update_property_risk(db, property_id, risk_status, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        property.risk_status = risk_status
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"risk_status": risk_status},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property risk updated successfully")
        return {"message ": "PropertyServices: property risk updated successfully"}

    async def update_property_available_required_for_investment(db, property_id, available_required_for_investment, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        if property.is_approved == False:
            raise HTTPException(500, "property with this property_id is not not approved now")
        old_data = Property.model_to_dict(property)
        property.available_required_for_investment = available_required_for_investment
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"available_required_for_investment": available_required_for_investment},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property available_required_for_investment value updated successfully")
        return {
            "message ": "PropertyServices: property available_required_for_investment value updated successfully"
        }


    async def update_property_approval(db, property_id, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        if property.is_approved:
            property.is_approved = False
        else:
            property.is_approved = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_approved": property.is_approved},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property approval updated successfully")
        return {
            "message ": "PropertyServices: property approval updated successfully"
        }

    
    async def update_property_open_for_the_investment(db, property_id, user_id):
        property = await Property.get_by_id(db, property_id)
        if not property:
            raise HTTPException(404, "property with this property_id is not found or already deleted")
        old_data = Property.model_to_dict(property)
        if property.is_open_for_investment:
            property.is_open_for_investment = False
        else:
            property.is_open_for_investment = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_open_for_investment": property.is_open_for_investment},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Management",
            object_id = property.property_id
        )
        await db.commit()
        await db.refresh(property)
        logger.info("PropertyServices: property approval updated successfully")
        return {
            "message ": "PropertyServices: property approval updated successfully"
        }

    
    async def get_all_properties(db):
        stmt = (select(Property).where(Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_info_all_properties(db, skip: int = 0, limit: int = 10, deleted: bool = False):
        stmt = (
            select(Property)
            .where(Property.is_deleted == deleted)
            .offset(skip)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(Property)
            .where(Property.is_deleted == deleted)
        )
        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        return result.scalars().all(), total_res.scalar() or 0

    @staticmethod
    async def get_all_properties_info_by_risk(db, risk_status, skip: int = 0, limit: int = 10, deleted: bool = False):
        stmt = (
            select(Property)
            .where(Property.is_deleted == deleted, Property.risk_status == risk_status)
            .offset(skip)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(Property)
            .where(Property.is_deleted == deleted, Property.risk_status == risk_status)
        )
        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        return result.scalars().all(), total_res.scalar() or 0
    
    
    async def get_all_property_by_risk(db, risk_status):
        stmt = (select(Property).where(Property.is_deleted.is_(False), Property.risk_status == risk_status))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_total_count(db):

        stmt = (
            select(func.count(Property.property_id))
            .where(Property.is_deleted == False)
        )
        result = await db.execute(stmt)
        return result.scalar()

    
    async def get_by_id_of_property(db, property_id):
        stmt = (select(Property).where(Property.property_id == property_id, Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_all_property_name_id(db):
        stmt = (select(Property.name, Property.property_id).where(Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        rows = result.all()
        return [
                {"property_name": row.name, "property_id": row.id} 
                for row in rows
            ]

    @staticmethod
    async def get_all_info_related_rent(db, property_id: str):

        result = await db.execute(
            select(Property)
            .where(
                Property.property_id == property_id,
                Property.is_deleted == False
            )
            .options(
                selectinload(Property.unit_types)
                .selectinload(PropertyUnitType.units)
            )
        )

        property_obj = result.scalars().first()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        return {
            "property_id": property_obj.property_id,
            "name": property_obj.name,
            "description": property_obj.description,
            "risk_status": property_obj.risk_status,
            "purchase_price": property_obj.purchase_price,
            "total_investment_required": property_obj.total_investment_required,
            "unit_type": [
                {
                    "unit_type_id": ut.id,
                    "name": ut.name,
                    "unit_type": ut.unit_type,
                    "total_units": ut.total_units,
                    "occupied_units": ut.occupied_units,
                    "units": [
                        {
                            "unit_id": u.unit_id,
                            "area_sqft": u.area_sqft,
                            "unit_status": u.unit_status,
                            "market_lease_rent": u.market_lease_rent,
                            "actual_lease_rent": u.actual_lease_rent,
                            "lease_start_date": u.lease_start_date,
                            "lease_end_date": u.lease_end_date,
                        }
                        for u in ut.units if not u.is_deleted
                    ]
                }
                for ut in property_obj.unit_types if not ut.is_deleted
            ]
        }
    
    
    async def create_rent_roll_excel(db, property_id) -> BytesIO:
        data = await PropertyService.get_all_info_related_rent(db, property_id)
        wb = Workbook()
        ws = wb.active
        ws.title = "Rent Roll"

        ws.merge_cells("A1:N1")
        ws["A1"] = "Rent Roll Analysis"
        ws["A1"].alignment = Alignment(horizontal="center")
        ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
        ws["A1"].fill = PatternFill("solid", fgColor="1F4E79")

        ws.merge_cells("A3:B3")
        ws.merge_cells("C3:H3")
        ws["A3"] = "Property Name :"
        ws["C3"] = data["name"]

        ws.merge_cells("A4:B4")
        ws.merge_cells("C4:E4")
        ws["A4"] = "Rent Roll Date :"
        ws["C4"] = "As of: -----"

        for a in ["A3","A4","C3","C4"]:
            ws[a].alignment = Alignment(horizontal="center")
            ws[a].font = Font(bold=True, color="FFFFFF")
            ws[a].fill = PatternFill("solid", fgColor="1F4E79")

        header_row_1 = 6
        header_row_2 = 7

        headers_lvl1 = [
            "ID", "Type", "SF", "Status", "Move-In", "Start", "End",
            "Market Rent", "Lease Rent", "Loss to Lease", "% Loss",
            "Vacant", "Occupied"
        ]

        headers_lvl2 = [
            "Unit ID", "Unit Type", "Unit SF", "Unit Status", "Move In Date",
            "Lease Start", "End Date", "Market Rent", "Lease Rent",
            "LTL", "to Lease", "Unit Count", " SF Count"
        ]

        for col, header in enumerate(headers_lvl1, 1):
            ws.cell(row=header_row_1, column=col, value=header)
            ws.cell(row=header_row_1, column=col).font = Font(bold=True, color="FFFFFF")
            ws.cell(row=header_row_1, column=col).fill = PatternFill("solid", fgColor="fc7703")
            ws.cell(row=header_row_1, column=col).alignment  = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for col, header in enumerate(headers_lvl2, 1):
            ws.cell(row=header_row_2, column=col, value=header)
            ws.cell(row=header_row_2, column=col).font = Font(bold=True, color="FFFFFF")
            ws.cell(row=header_row_2, column=col).fill = PatternFill("solid", fgColor="fc7703")
            ws.cell(row=header_row_2, column=col).alignment  = Alignment(horizontal="center", vertical="center", wrap_text=True)

        row = header_row_2 + 1
        unit_counter = 100

        for unit_type in data["unit_type"]:
            # type_letter = "C" if "Bedroom" in unit_type["name"] else "A"

            for unit in unit_type["units"]:
                market = unit["market_lease_rent"]
                actual = unit["actual_lease_rent"]
                loss = actual - market
                percent_loss = (loss / actual) * 100 if market else 0
                start_date = datetime.fromisoformat(str(unit["lease_start_date"]))
                end_date = datetime.fromisoformat(str(unit["lease_end_date"]))

                ws.cell(row=row, column=1, value=unit_counter)
                ws.cell(row=row, column=2, value=unit_type["name"])
                ws.cell(row=row, column=3, value=unit["area_sqft"])
                ws.cell(row=row, column=4, value=unit["unit_status"])
                ws.cell(row=row, column=5, value="")

                ws.cell(row=row, column=6, value=start_date)
                ws.cell(row=row, column=7, value=end_date)

                ws.cell(row=row, column=6).number_format = 'yyyy-mm-dd'
                ws.cell(row=row, column=7).number_format = 'yyyy-mm-dd'

                ws.cell(row=row, column=8, value=market)
                ws.cell(row=row, column=9, value=actual)
                ws.cell(row=row, column=10, value=loss)
                ws.cell(row=row, column=11, value=percent_loss)
                # ws.cell(row=row, column=11).value = f"=IF(I{row}=0,0,(H{row}-I{row})/I{row})"
                # ws.cell(row=row, column=11).number_format = '0.00%'

                ws.cell(row=row, column=12, value=False)
                ws.cell(row=row, column=13, value=unit["area_sqft"])

                row += 1
                unit_counter += 1


        for r in range(header_row_2 + 1, row):
            ws.cell(r, 8).number_format = '#,##0.00'
            ws.cell(r, 9).number_format = '#,##0.00'
            ws.cell(r, 10).number_format = '"$"#,##0'
            ws.cell(r, 11).number_format = '0.00"%"'

        # column widths
        widths = [10, 18, 8, 10, 12, 12, 12, 14, 14, 14, 10, 14, 18]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
            ws.allignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=rent_roll_{timestamp_ms}.xlsx"
            }
        )


    def round_half_up(value):
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


    @staticmethod
    async def calculate_rent_roll_summary(db, property_id):

        property_data = await PropertyService.get_all_info_related_rent(db, property_id)
        summary = []

        for unit_type in property_data.get("unit_type", []):

            total_units = unit_type.get("total_units", 0)
            occupied_units = unit_type.get("occupied_units", 0)
            vacant_units = total_units - occupied_units

            total_area = Decimal("0")
            total_market_rent = Decimal("0")
            total_actual_rent = Decimal("0")

            for unit in unit_type.get("units", []):

                area = Decimal(str(unit.get("area_sqft") or 0))
                market_rent = Decimal(str(unit.get("market_lease_rent") or 0))
                actual_rent = Decimal(str(unit.get("actual_lease_rent") or 0))

                total_area += area
                total_market_rent += market_rent
                total_actual_rent += actual_rent

            annual_total_market_rent =PropertyService.round_half_up(
                    total_market_rent * Decimal("12")
                )
        
            annual_total_actual_rent =PropertyService.round_half_up(
                    total_actual_rent * Decimal("12")
                )
            
            area_per_unit = PropertyService.round_half_up(
                    total_area / Decimal(total_units)
                ) if total_units else Decimal("0")
            
            if annual_total_actual_rent != Decimal("0"):
                ltl_gap = (
                    (annual_total_actual_rent / annual_total_market_rent)
                    - Decimal("1")
                ) * Decimal("100")
            else:
                ltl_gap = Decimal("0")


            summary.append({
                "unit_type": unit_type.get("name"),
                "total_units": total_units,
                "total_occupied": occupied_units,
                "total_vacant": vacant_units,
                "total_area_sqft": PropertyService.round_half_up(total_area),
                "area_per_unit": area_per_unit,

                "market_rent_per_unit" : total_market_rent / total_units,
                "market_rent_per_sf": (total_market_rent / total_units)/area_per_unit,
                "total_market_rent": PropertyService.round_half_up(total_market_rent),
                "total_market_rent_annual": annual_total_market_rent,

                "ltl": (((total_actual_rent / total_units)/(total_market_rent / total_units)-1)*100)if total_actual_rent else Decimal("0"),

                "actual_rent_per_unit" : total_actual_rent / total_units,
                "actual_rent_per_sf": (total_actual_rent / total_units)/area_per_unit,
                "total_actual_rent": PropertyService.round_half_up(total_actual_rent),
                "total_actual_rent_annual": annual_total_actual_rent,

                "ltl_gap_to_market": ltl_gap
            })

            overall_summary = PropertyService.final_overall_summary(summary)
        return {

            "summary": summary, "overall_summary":overall_summary, "property_name" : property_data["name"] 
        }


    async def create_rent_roll_summary_excel(db, property_id) -> BytesIO:
        summary_data = await PropertyService.calculate_rent_roll_summary(db, property_id)
        wb = Workbook()
        ws = wb.active
        ws.title = "Rent Roll Summary"

        ws.merge_cells("A1:Q1")
        ws["A1"] = "Rent Roll Summary"
        ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
        ws["A1"].alignment = Alignment(horizontal="center")
        ws["A1"].fill = PatternFill("solid", fgColor="1F4E79")

        ws.merge_cells("A2:Q2")
        ws["A2"] = summary_data["property_name"]
        ws["A2"].font = Font(size=12, bold=True, color="FFFFFF")
        ws["A2"].alignment = Alignment(horizontal="center")
        ws["A2"].fill = PatternFill("solid", fgColor="1F4E79")

        ws.merge_cells("A3:Q3")
        ws["A3"] = "Rent Roll Summary"
        ws["A3"].font = Font(size=12, bold=True, color="FFFFFF")
        ws["A3"].alignment = Alignment(horizontal="center")
        ws["A3"].fill = PatternFill("solid", fgColor="1F4E79")

        ws.merge_cells("G5:H5")
        ws["G5"] = "Status"

        ws.merge_cells("I5:J5")
        ws["I5"] = "Market"

        ws.merge_cells("K5:M5")
        ws["K5"] = "Actual"

        ws.merge_cells("N5:O5")
        ws["N5"] = "Actual"

        ws.merge_cells("P5:Q5")
        ws["P5"] = "Market"

        ws.merge_cells("R5:S5")
        ws["R5"] = "Gap-to-Market"

        for cell in ["G5", "I5", "K5", "N5", "P5", "R5"]:
            ws[cell].font = Font(bold=True, color="FFFFFF")
            ws[cell].alignment = Alignment(horizontal="center")
            ws[cell].fill = PatternFill("solid", fgColor="fc7703")

        headers = [
            "Type", "Unit Description", "Units", "%", "SF Total", "SF / Unit",
            "Occupied", "Vacant",
            "Rent", "PSF",
            "Rent", "PSF", "LTL",
            "Monthly Rent", "Annual Rent",
            "Monthly Rent", "Annual Rent",
            "LTL"
        ]

        for col, val in enumerate(headers, 1):
            ws.cell(row=6, column=col, value=val).font = Font(bold=True, color="FFFFFF")
            ws.cell(row=6, column=col, value=val).fill = PatternFill("solid", fgColor="1F4E79")

        row = 7
        type_labels = ["A", "B", "C", "D", "E"]
        description_map = {
            "Bachelors": "BACH",
            "2 Bedroom": "2 BR/BA",
            "1 Bedroom": "1 BR/BA",
            "2 Bedroom Den": "1 BR/BA DEN",
            "3 Bedroom Den": "1 BR/BA DEN"
        }

        total_units = summary_data["overall_summary"]["overall_total_units"]

        for idx, item in enumerate(summary_data["summary"]):
            ws.cell(row=row, column=1, value=type_labels[idx])
            ws.cell(row=row, column=2, value=description_map.get(item["unit_type"], item["unit_type"]))

            ws.cell(row=row, column=3, value=item["total_units"])
            ws.cell(row=row, column=4, value=item["total_units"] / total_units)

            ws.cell(row=row, column=5, value=item["total_area_sqft"])
            ws.cell(row=row, column=6, value=item["area_per_unit"])

            ws.cell(row=row, column=7, value=item["total_occupied"])
            ws.cell(row=row, column=8, value=item["total_vacant"])

            ws.cell(row=row, column=9, value=item["market_rent_per_unit"])
            ws.cell(row=row, column=10, value=item["market_rent_per_sf"])

            ws.cell(row=row, column=11, value=item["actual_rent_per_unit"])
            ws.cell(row=row, column=12, value=item["actual_rent_per_sf"])
            ws.cell(row=row, column=13, value=item["ltl"] / 100)

            ws.cell(row=row, column=14, value=item["total_actual_rent"])
            ws.cell(row=row, column=15, value=item["total_actual_rent_annual"])

            ws.cell(row=row, column=16, value=item["total_market_rent"])
            ws.cell(row=row, column=17, value=item["total_market_rent_annual"])
            ws.cell(row=row, column=18, value=item["ltl_gap_to_market"] / 100)

            row += 1

        overall = summary_data["overall_summary"]

        ws.cell(row=row, column=3, value=overall["overall_total_units"])
        ws.cell(row=row, column=4, value=1)

        ws.cell(row=row, column=5, value=overall["overall_total_area_sqft"])
        ws.cell(row=row, column=6, value=overall["overall_total_area_sqft_per_unit"])

        ws.cell(row=row, column=7, value=overall["overall_total_occupied"])
        ws.cell(row=row, column=8, value=overall["overall_total_vacant"])

        ws.cell(row=row, column=9, value=overall["overall_total_market_rent_per_unit"])
        ws.cell(row=row, column=10, value=overall["overall_total_market_rent_per_unit_psf"])

        ws.cell(row=row, column=11, value=overall["overall_total_actual_rent_per_unit"])
        ws.cell(row=row, column=12, value=overall["overall_total_actual_rent_per_unit_psf"])
        ws.cell(row=row, column=13, value=overall["overall_ltl_percent"] / 100)

        ws.cell(row=row, column=14, value=overall["overall_total_actual_rent"])
        ws.cell(row=row, column=15, value=overall["overall_total_actual_rent_annual"])

        ws.cell(row=row, column=16, value=overall["overall_total_market_rent"])
        ws.cell(row=row, column=17, value=overall["overall_total_market_rent_annual"])

        ws.cell(row=row, column=18, value=overall["overall_ltl_gap_to_market_percent"] / 100)

        orange_fill = PatternFill(start_color="FC7703", end_color="FC7703", fill_type="solid")
        white_bold_font = Font(bold=True, color="FFFFFF")
        top_border_style = Border(top=Side(style='thick', color='1F4E79')) 
        for col in range(3, 19):
            cell = ws.cell(row=row, column=col)
            cell.border = top_border_style
            cell.fill = orange_fill
            cell.font = white_bold_font

        for r in range(7, row + 1):
            ws.cell(r, 4).number_format = '0.0%'
            ws.cell(r, 9).number_format = '"$"#,##0'
            ws.cell(r, 10).number_format = '"$"#,##0.00'
            ws.cell(r, 11).number_format = '"$"#,##0'
            ws.cell(r, 12).number_format = '"$"#,##0.00'
            ws.cell(r, 13).number_format = '0.0%'
            ws.cell(r, 14).number_format = '"$"#,##0'
            ws.cell(r, 15).number_format = '"$"#,##0'
            ws.cell(r, 16).number_format = '"$"#,##0'
            ws.cell(r, 17).number_format = '"$"#,##0'
            ws.cell(r, 18).number_format = '0.0%'

        widths = [6, 18, 8, 8, 10, 10, 10, 8, 12, 8, 12, 8, 10, 14, 14, 14, 14, 10]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; "
                f"filename=rent_roll_summary_{timestamp_ms}.xlsx"
                }
        )


    @staticmethod
    def final_overall_summary(summary):

        total_units = Decimal("0")
        total_occupied = Decimal("0")
        total_vacant = Decimal("0")

        total_area = Decimal("0")

        total_market_rent = Decimal("0")
        total_market_rent_annual = Decimal("0")

        total_actual_rent = Decimal("0")
        total_actual_rent_annual = Decimal("0")

        for units in summary:
            total_units += Decimal(units.get("total_units", 0))
            total_occupied += Decimal(units.get("total_occupied", 0))
            total_vacant += Decimal(units.get("total_vacant", 0))

            total_area += Decimal(units.get("total_area_sqft", 0))

            total_market_rent += Decimal(units.get("total_market_rent", 0))
            total_market_rent_annual += Decimal(units.get("total_market_rent_annual", 0))

            total_actual_rent += Decimal(units.get("total_actual_rent", 0))
            total_actual_rent_annual += Decimal(units.get("total_actual_rent_annual", 0))


        avg_area_per_unit = (
            total_area / total_units
            if total_units != 0 else Decimal("0")
        )

        market_rent_per_unit = (
            total_market_rent / total_units
            if total_units != 0 else Decimal("0")
        )

        actual_rent_per_unit = (
            total_actual_rent / total_occupied
            if total_occupied != 0 else Decimal("0")
        )

        market_rent_psf = (
            market_rent_per_unit / avg_area_per_unit
            if avg_area_per_unit != 0 else Decimal("0")
        )

        actual_rent_psf = (
            actual_rent_per_unit / avg_area_per_unit
            if avg_area_per_unit != 0 else Decimal("0")
        )

        overall_ltl = (
            (actual_rent_per_unit / market_rent_per_unit - Decimal("1")) * Decimal("100")
            if market_rent_per_unit != 0 else Decimal("0")
        )

        overall_ltl_gap = (
            (total_actual_rent_annual / total_market_rent_annual - Decimal("1")) * Decimal("100")
            if total_market_rent_annual != 0 else Decimal("0")
        )

        return {
            "overall_total_units": total_units,
            "overall_total_occupied": total_occupied,
            "overall_total_vacant": total_vacant,

            "overall_total_area_sqft": total_area,
            "overall_total_area_sqft_per_unit": PropertyService.round_half_up(avg_area_per_unit),

            "overall_total_market_rent": PropertyService.round_half_up(total_market_rent),
            "overall_total_market_rent_annual": PropertyService.round_half_up(total_market_rent_annual),

            "overall_total_actual_rent": PropertyService.round_half_up(total_actual_rent),
            "overall_total_actual_rent_annual": PropertyService.round_half_up(total_actual_rent_annual),

            "overall_total_market_rent_per_unit": PropertyService.round_half_up(market_rent_per_unit),
            "overall_total_market_rent_per_unit_psf": PropertyService.round_half_up(market_rent_psf),

            "overall_total_actual_rent_per_unit": PropertyService.round_half_up(actual_rent_per_unit),
            "overall_total_actual_rent_per_unit_psf": PropertyService.round_half_up(actual_rent_psf),

            "overall_ltl_percent": PropertyService.round_half_up(overall_ltl),
            "overall_ltl_gap_to_market_percent": PropertyService.round_half_up(overall_ltl_gap),
        }






class PropertyUnitTypeServices:

    async def add_new_property_unit_type(db, property_id, data, user_id):
        new_property_type = PropertyUnitType(
            property_id = property_id,
            name = data.name,
            unit_type = data.unit_type,
            total_units = data.total_units,
            occupied_units = data.occupied_units,
        )

        db.add(new_property_type)
        await db.flush()
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Property Unit Type Management",
            object_id = str(new_property_type.id)
        )
        await db.commit()
        await db.refresh(new_property_type)
        logger.info("PropertyUnitService: Property unit type added successfully for the property")
        return new_property_type
    

    async def update_property_unit_type(db, id, property_id, data, user_id):
        unit_type = await PropertyUnitType.get_by_id(db, id, property_id)
        if not unit_type:
            raise HTTPException(404, "property unit type not found or already deleted for this id and property_id")
        old_data = PropertyUnitType.model_to_dict(unit_type)
        if data.name is not None:
            unit_type.name = data.name

        if data.unit_type is not None:
            unit_type.unit_type = data.unit_type

        if data.total_units is not None:
            unit_type.total_units = data.total_units

        if data.occupied_units is not None:
            unit_type.occupied_units = data.occupied_units
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Unit Type Management",
            object_id = str(id)
        )
        await db.commit()
        await db.refresh(unit_type)
        logger.info("PropertyUnitType: property unit type data updated successfully")

        return unit_type
    

    async def delete_property_unit_type(db, id, property_id, user_id):
        unit_type = await PropertyUnitType.get_by_id(db, id, property_id)
        if not unit_type:
            raise HTTPException(404, "property unit type not found or already deleted for this id and property_id")
        old_data = PropertyUnitType.model_to_dict(unit_type)
        unit_type.is_deleted = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"id_deleted":True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Property Unit Type Management",
            object_id = str(id)
        )
        await db.commit()
        await db.refresh(unit_type)
        logger.info("PropertyUnitType: property unit type data deleted successfully")
        return {
            "message": "PropertyUnitType: property unit type deleted successfully"
        }
    

    async def get_all_unit_type_for_property_id(db, property_id):
        stmt = (select(PropertyUnitType).where(PropertyUnitType.property_id == property_id, PropertyUnitType.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_unit_type_by_property_id_and_id(db, id, property_id):
        return await PropertyUnitType.get_by_id(db, id, property_id)

    async def get_property_rent_summary(db: Session, property_id: str):
        stmt = (
            select(
                PropertyUnitType.name.label("unit_type_name"),
                func.count(PropertyUnit.unit_id).label("total_units"),
                func.avg(PropertyUnit.area_sqft).label("avg_sqft"),
                func.sum(PropertyUnit.market_lease_rent).label("current_monthly_rent"),
                func.sum(PropertyUnit.actual_lease_rent).label("actual_monthly_rent"),
            )
            .join(PropertyUnit, PropertyUnit.unit_type_id == PropertyUnitType.id)
            .where(
                PropertyUnitType.property_id == property_id,
                PropertyUnitType.is_deleted.is_(False),
                PropertyUnit.is_deleted.is_(False),
            )
            .group_by(PropertyUnitType.name)
        )

        result = await db.execute(stmt)
        rows = result.all()

        data = {}
        for row in rows:
            data[row.unit_type_name] = {
                "total_units": int(row.total_units or 0),
                "avg_sqft": float(row.avg_sqft or 0),
                "current_monthly_rent": float(row.current_monthly_rent or 0),
                "actual_monthly_rent": float(row.actual_monthly_rent or 0),
            }

        return data


class PropertyUnitServices:

    async def add_new_property_unit(db, data, user_id):
        get_available = await PropertyUnit.get_all_available_by_ids(db, data.property_id, data.unit_type_id)
        if get_available == data.total_required:
            raise HTTPException(400, "you have added remt for all the unit for this type.")
        new_unit = PropertyUnit(
            unit_id = generate_id("unit"),
            property_id = data.property_id,
            unit_type_id = data.unit_type_id,
            area_sqft = data.area_sqft,
            unit_status = data.unit_status,
            market_lease_rent = data.market_lease_rent,
            actual_lease_rent = data.actual_lease_rent,
            lease_start_date = data.lease_start_date,
            lease_end_date = data.lease_end_date
        )
        db.add(new_unit)
        await db.flush()
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(mode="json"),
            old_data = None,
            audit_type = "ADD",
            entity_type = "Property Unit Management",
            object_id = new_unit.unit_id
        )
        await db.commit()
        await db.refresh(new_unit)
        logger.info("PropertyUnitService: Property unit detials created for the given property_id, and unit_type_id")
        # return{
        #     "message" : "PropertyUnitService: Property unit detials created for the given property_id, and unit_type_id"
        # }
        return new_unit
    


    async def update_property_unit(db, unit_id, data, user_id):
        unit = await PropertyUnit.get_by_id(db, unit_id, data.unit_type_id, data.property_id)
        if not unit:
            raise HTTPException(404, "property unit not found or already deleted for this id and property_id")
        old_data = PropertyUnit.model_to_dict(unit)
        if data.unit_type_id is not None:
            unit.unit_type_id = data.unit_type_id
        
        if data.property_id is not None:
            unit.property_id = data.property_id

        if data.total_units is not None:
            unit.total_units = data.total_units

        if data.area_sqft is not None:
            unit.area_sqft = data.area_sqft

        if data.unit_status is not None:
            unit.unit_status = data.unit_status

        if data.market_lease_rent is not None:
            unit.market_lease_rent = data.market_lease_rent
        
        if data.actual_lease_rent is not None:
            unit.actual_lease_rent = data.actual_lease_rent

        if data.lease_start_date is not None:
            unit.lease_start_date = data.lease_start_date

        if data.lease_end_date is not None:
            unit.lease_end_date = data.lease_end_date
       
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data.model_dump(),
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Property Unit Management",
            object_id = unit_id
        )
        await db.commit()
        await db.refresh(unit)
        logger.info("PropertyUnit: property unit data updated successfully")
        return unit
    

    async def delete_property_unit(db, unit_id, unit_type_id, property_id, user_id):
        unit = await PropertyUnit.get_by_id(db, unit_id, unit_type_id, property_id)
        if not unit:
            raise HTTPException(404, "property unit  not found or already deleted for this id and property_id")
        old_data = PropertyUnit.model_to_dict(unit)
        unit.is_deleted = True
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"is_deleted": True},
            old_data = old_data,
            audit_type = "DELETE",
            entity_type = "Property Unit Management",
            object_id = unit_id
        )
        await db.commit()
        await db.refresh(unit)
        logger.info("PropertyUnit: property unit  data deleted successfully")
        return {
            "message": "PropertyUnit: property unit  deleted successfully"
        }
    

    async def update_occupied_property_unit_status(db, unit_id, data):
        pass
        # unit = await PropertyUnit.get_by_id(db, unit_id, data.unit_type_id, data.property_id)
        # if not unit:
        #     raise HTTPException(404, "property unit  not found or already deleted for this id and property_id")
        
        # if data.occupied_units > unit.total_units:
        #     raise HTTPException(500, f"total unit is only : {unit.total_units} nos but you want to fill : {data.occupied_units} nos that is not possible.")
        # if data.unit_status is not None:
        #     unit.unit_status = data.unit_status
        # if data.occupied_units == unit.total_units:
        #     unit.unit_status = "Occupied"
        # unit.occupied_units = data.occupied_units
        # if data.occupied_units == 0:
        #     unit.unit_status = "vacant"
        # await db.commit()
        # await db.refresh(unit)
        # logger.info("PropertyUnit: property unit occupancy updated successfully")
        # # return {
        # #     "message": "PropertyUnit: property unit occupancy updated successfully"
        # # }
        # return unit


    async def get_all_unit_for_property_id(db, unit_type_id, property_id):
        stmt = (select(PropertyUnit).where(PropertyUnit.property_id == property_id, PropertyUnit.unit_type_id == unit_type_id, PropertyUnit.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()



    async def get_unit_by_property_id_and_id(db, unit_id, unit_type_id, property_id):
        return await PropertyUnit.get_by_id(db, unit_id, unit_type_id, property_id)

