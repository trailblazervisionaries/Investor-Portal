from fastapi import HTTPException
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, or_
from datetime import datetime
from app.models.audit_model import AuditModel
from dotenv import load_dotenv
from app.models.leads import Leads, LeadRemark
from app.models.investor_assist_model import InvestorAssistant
from app.schemas.leads import createLeads
import logging
from io import BytesIO
from fastapi.responses import StreamingResponse

from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent.parent



load_dotenv()
logger = logging.getLogger(__name__)



class LeadService:

    async def create_the_leads(db: Session, data: createLeads):
        try:
            result = await db.execute(select(Leads).where(Leads.email == data.email, Leads.is_deleted.is_(False)))
            existing_lead = result.scalars().first()

            if existing_lead:
                existing_lead.fname = data.fname
                existing_lead.lname = data.lname
                existing_lead.i_am_type = data.i_am_type
                existing_lead.description = data.description
                existing_lead.phone = data.phone
                existing_lead.consent_check = data.consent_check
                existing_lead.updated_at = datetime.utcnow()
                logger.info("LeadService: Lead info found for this email so we are updating you previous info insted of creating a new one.")
                await db.commit()
                await db.refresh(existing_lead)
                return existing_lead
            logger.info("LeadService: Lead info not found for this email so we are creating a new lead for you and stored you data.")
            # CREATE new lead if not found
            new_lead = Leads(
                fname=data.fname,
                lname=data.lname,
                email=data.email,
                i_am_type= data.i_am_type,
                description=data.description,
                phone=data.phone,
                consent_check=data.consent_check
            )

            db.add(new_lead)
            logger.info("LeadService: New Lead Data created and stored into the database successfully.")
            await db.commit()
            await db.refresh(new_lead)
            return new_lead

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error while processing lead.")
    
    
    async def get_leads_by_attendend_id_and_status(db, user_id, status, page, page_size):
        return await Leads.get_all_leads_by_attendend_id_and_status(
            db,
            user_id,
            status,
            page,
            page_size
        )


    async def get_all_lead(db, page: int, page_size: int):
        return await Leads.get_all_leads_(db, page, page_size)

    async def get_leads_by_status(db, status: str, page: int, page_size: int):
        return await Leads.get_all_leads_by_status_(
            db=db,
            status=status,
            page=page,
            page_size=page_size
        )

    

    async def delete_the_lead(db, id, user_id, remarks):
        lead = await Leads.get_lead_by_id(db, id)
        if not lead:
            raise HTTPException(404, "lead with this id is not found.")
        lead.is_deleted = True
        new_remark = await LeadService.add_lead_remark(db, id, remarks, user_id)
        await db.commit()
        await db.refresh(lead)
        await db.refresh(new_remark)
        return {
            "message": "lead deleted and remark added successfully."
        }
   
   
    async def permanant_delete_the_lead(db: Session, id: int, user_id: str, remarks: str):
        lead = await Leads.get_lead_by_id(db, id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead with this ID not found.")
        try:
            # await LeadService.add_lead_remark(db, id, remarks, user_id)
            await db.delete(lead)
            logger.info(f"LeadService: Lead with id {id} is deleted permanently.")
            await AuditModel.add_new_logs(
                db=db,
                added_by=user_id,
                new_data=None,
                old_data={"lead_id": id, "final_remarks": remarks},
                audit_type="PERMANENT_DELETE",
                entity_type="Lead Management",
                object_id=str(id)
            )
            await db.commit()
            return {
                "status": "success",
                "message": "Lead permanently deleted and final remark recorded in history."
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error during permanent delete of lead {id}: {e}")
            raise HTTPException(status_code=500, detail="Could not complete deletion.")


    async def Update_the_lead_status(db, id, status, updatedby, remarks):
        lead = await Leads.get_lead_by_id(db, id)
        if not lead:
            raise HTTPException(404, "lead with this id is not found.")
        lead.updated_by = updatedby
        lead.status = status
        lead.updated_at = datetime.utcnow()
        logger.info("LeadService: Lead status updated successfully and also added the remarks for the lead.")
        new_remark = await LeadService.add_lead_remark(db, id, remarks, updatedby)
        await db.commit()
        await db.refresh(lead)
        await db.refresh(new_remark)
        return {
            "message": "lead updated and remark added successfully."
        }
    
    async def update_marked_the_lead_assisted_by(db, id, assistedby, remarks):
        lead = await Leads.get_lead_by_id(db, id)
        if not lead:
            raise HTTPException(404, "lead with this id is not found.")
        lead.assisted_by = assistedby
        new_remark = await LeadService.add_lead_remark(db, id, remarks, assistedby)
        logger.info("LeadService: update the marked the assisted lead and add new lead remarks.")
        await db.commit()
        await db.refresh(lead)
        await db.refresh(new_remark)
        return {
            "message": "lead assisted marked and remarks added successfully."
        }

    async def marked_the_lead_assisted_by(db, id, assistedby, remarks):
        # Use with_for_update() to lock the row while we check/update it
        stmt = select(Leads).where(Leads.id == id).with_for_update()
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            raise HTTPException(404, "Lead not found.")

        # Check if someone else already assisted this lead
        if lead.assisted_by is not None:
            raise HTTPException(400, f"This lead is already being assisted by {lead.assisted_by}")

        lead.assisted_by = assistedby
        # The rest of your logic remains the same
        new_remark = await LeadService.add_lead_remark(db, id, remarks, assistedby)
        logger.info("LeadService: Lead marked for assistance and added the remarks")
        await db.commit()
        return {"message": "lead assisted marked and remarks added successfully."}

    

    async def update_the_lead_by_id(db, id, data, user_id):
        lead = await Leads.get_lead_by_id(db, id)
        if not lead:
            raise HTTPException(404, "Lead data not found")
        if data.fname is not None:
            lead.fname = data.fname

        if data.lname is not None:
            lead.lname = data.lname
        
        if data.i_am_type is not None:
            lead.i_am_type = data.i_am_type

        if data.email is not None:
            lead.email = data.email

        if data.description is not None:
            lead.description = data.description
                
        if data.status is not None:
            lead.status = data.status

        if data.consent_check is not None:
            lead.consent_check = data.consent_check

        if data.phone is not None:
            lead.phone = data.phone

        lead.updated_by = user_id
        new_remark = await LeadService.add_lead_remark(db, id, data.remarks, user_id)
        logger.info("LeadService: Lead info updated successfully and lead remarks added successfully.")
        await db.commit()
        await db.refresh(new_remark)

        return {
            "message" : "lead data updated successfully"
        }


    async def add_lead_remark(db, lead_id: str, remark: str, user_id: str):
        new_remark = LeadRemark(
            lead_id=lead_id,
            remark=remark,
            created_by=user_id
        )
        db.add(new_remark)
        return new_remark


    def _export_leads_to_excel(leads: list, sheet_title: str, filename: str):

        wb = Workbook()
        ws = wb.active
        ws.title = sheet_title

        headers = [
            "ID",
            "First_Name",
            "Last_Name",
            "Email",
            "Description",
            "Phone",
            "User_type",
            "Assisted By",
            "Status",
            "Consent_Check",
            "Latest Remark",
            "Remark Added By",
            "Remark Created At",
            "Created At",
            "Updated At",
        ]

        ws.append(headers)

        # make headers bold
        for col in range(1, len(headers) + 1):
            ws.cell(row=1, column=col).font = Font(bold=True)

        for lead in leads:
            latest_remark = lead.remarks[0] if lead.remarks else None

            ws.append([
                lead.id,
                lead.fname,
                lead.lname,
                lead.email,
                lead.description,
                lead.phone,
                lead.i_am_type,
                lead.assisted_by,
                lead.status,
                lead.consent_check,
                latest_remark.remark if latest_remark else "",
                latest_remark.created_by if latest_remark else "",
                latest_remark.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_remark else "",
                lead.created_at.strftime("%Y-%m-%d %H:%M:%S") if lead.created_at else "",
                lead.updated_at.strftime("%Y-%m-%d %H:%M:%S") if lead.updated_at else "",
            ])

        # Auto column width
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max_length + 3

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )


    async def convert_to_excel_all_status_wise_leads(db, status):
        leads = await Leads.get_all_leads_by_status(db, status)
        if not leads:
            return None

        filename = f"{status}_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return LeadService._export_leads_to_excel(
            leads=leads,
            sheet_title=f"{status.capitalize()} Leads",
            filename=filename,
        )


    async def convert_to_excel_status_and_date_wise_leads(db, status: str, start_date: datetime, end_date: datetime):

        leads = await Leads.get_leads_by_status_and_date_range(
            db=db,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        if not leads:
            return None

        filename = (
            f"{status}_leads_"
            f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
        )

        return LeadService._export_leads_to_excel(
            leads=leads,
            sheet_title=f"{status.capitalize()} Leads",
            filename=filename,
        )

    
    async def assign_unassigned_leads_round_robin(db: Session, admin_id: str):
        """
        Assign all unassigned leads to investor assistants using round-robin distribution.
        Each lead gets assigned to an investor assistant in a round-robin manner.
        """
        try:
            unassigned_leads_stmt = select(Leads).where(
                and_(
                    Leads.is_deleted == False,
                    or_(
                        Leads.assisted_by == None,
                        Leads.assisted_by == ""
                    )
                )
            )
            
            unassigned_result = await db.execute(unassigned_leads_stmt)
            unassigned_leads = unassigned_result.scalars().all()
            
            active_assistants_stmt = select(InvestorAssistant).where(
                and_(
                    InvestorAssistant.is_active == True,
                    InvestorAssistant.is_deleted == False
                )
            )
            
            assistants_result = await db.execute(active_assistants_stmt)
            active_assistants = assistants_result.scalars().all()
            
            if not unassigned_leads:
                logger.info("LeadService: No unassigned leads found for round-robin assignment.")
                return {
                    "status": "success",
                    "message": "No unassigned leads found",
                    "assigned_count": 0,
                    "total_assistants": len(active_assistants) if active_assistants else 0
                }
            
            if not active_assistants:
                logger.warning("LeadService: No active investor assistants available for assignment.")
                return {
                    "status": "error",
                    "message": "No active investor assistants available",
                    "assigned_count": 0
                }
            
            assistant_count = len(active_assistants)
            assigned_count = 0
            assignments_detail = []
            
            for idx, lead in enumerate(unassigned_leads):
                assigned_assistant = active_assistants[idx % assistant_count]
                
                old_assisted_by = lead.assisted_by
                lead.assisted_by = assigned_assistant.user_id
                lead.updated_by = admin_id
                lead.updated_at = datetime.utcnow()
                

                remark_text = f"Lead auto-assigned to {assigned_assistant.fname} {assigned_assistant.lname} via round-robin distribution"
                await LeadService.add_lead_remark(db, lead.id, remark_text, admin_id)
                
                assignments_detail.append({
                    "lead_id": lead.id,
                    "lead_email": lead.email,
                    "assigned_to": assigned_assistant.user_id,
                    "assistant_name": f"{assigned_assistant.fname} {assigned_assistant.lname}"
                })
                
                assigned_count += 1
            
            await db.commit()
            
            logger.info(
                f"LeadService: Successfully assigned {assigned_count} leads to {assistant_count} "
                f"investor assistants using round-robin by admin {admin_id}."
            )
            
            await AuditModel.add_new_logs(
                db=db,
                added_by=admin_id,
                new_data={"assigned_count": assigned_count, "assistant_count": assistant_count},
                old_data=None,
                audit_type="BULK_ASSIGNMENT",
                entity_type="Lead Management",
                object_id="bulk_assignment"
            )
            
            await db.commit()
            
            return {
                "status": "success",
                "message": "Leads assigned successfully using round-robin distribution",
                "assigned_count": assigned_count,
                "total_assistants": assistant_count,
                "leads_per_assistant": assigned_count // assistant_count if assistant_count > 0 else 0,
                "summary": f"Distributed {assigned_count} leads among {assistant_count} assistants"
            }
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"LeadService: Database error during round-robin assignment: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error during lead assignment: {str(e)}"
            )
        except Exception as e:
            await db.rollback()
            logger.error(f"LeadService: Unexpected error during round-robin assignment: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during lead assignment: {str(e)}"
            )
