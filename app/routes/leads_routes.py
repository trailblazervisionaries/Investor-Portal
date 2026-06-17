from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File, status
from app.config.database import get_db
from app.services.leads_services import LeadService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.leads import createLeads, updateLeads, addRemarksLeads, PaginatedLeadResponse
from datetime import datetime
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add")
async def add_new_lead(data:createLeads, db: Session = Depends(get_db)):
    lead = await LeadService.create_the_leads(db, data)
    if not lead:
        raise HTTPException(500, "some issue occured during the creattion of the lead")
    return {
        "message":"lead added successfully"
    }



@router.put("/update/{id}")
async def update_the_lead(data: updateLeads, id: int, request: Request, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    lead = await LeadService.update_the_lead_by_id(db, id, data, user_id)
    return lead


# @router.get("/get-all", response_model = List[LeadResponse])
# async def get_all_leads(db: Session = Depends(get_db)):
#     leads = await LeadService.get_all_lead(db)
#     if not leads:
#         raise HTTPException(404, "associated leads not available")
#     return [LeadResponse.model_validate(lead) for lead in leads]


# @router.get("/get-all/{status}", response_model = List[LeadResponse])
# async def get_all_leads_by_status(status: str, db: Session = Depends(get_db)):
#     leads = await LeadService.get_all_by_status(db, status)
#     if not leads:
#         logger.info("Leads Route: provided status associated leads not available")
#         return []
#         # raise HTTPException(404, "provided status associated leads not available")
#     return [LeadResponse.model_validate(lead) for lead in leads]


@router.get("/get-all", response_model=PaginatedLeadResponse)
async def get_all_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = await LeadService.get_all_lead(
        db=db,
        page=page,
        page_size=page_size
    )

    return result

@router.get("/get-all/{status}", response_model=PaginatedLeadResponse)
async def get_leads_by_status(
    status: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return await LeadService.get_leads_by_status(
        db=db,
        status=status,
        page=page,
        page_size=page_size
    )



@router.delete("/delete/{id}")
async def delete_lead_by_id(id: int, request: Request, data: addRemarksLeads, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    lead = await LeadService.delete_the_lead(db, id, user_id, data.remarks)
    return lead


@router.delete("/permanent-delete/{id}")
async def delete_lead_by_id_permanantly(id: int, request: Request, data: addRemarksLeads, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    lead = await LeadService.permanant_delete_the_lead(db, id, user_id, data.remarks)
    return lead


@router.put("/update-status/{id}/{status}")
async def Update_the_lead_status(id: int, request: Request, data: addRemarksLeads, status: str, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await LeadService.Update_the_lead_status(db, id, status, user_id, data.remarks)
    return resp


@router.put("/assisted/{id}")
async def mark_assisted_by(id: int, request: Request, data: addRemarksLeads, db: Session = Depends(get_db)):
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await LeadService.marked_the_lead_assisted_by(db, id, user_id, data.remarks)
    return resp


@router.put("/update-assisted/{id}/{user_id}")
async def mark_assisted_by(id: int, user_id: str, request: Request, data: addRemarksLeads, db: Session = Depends(get_db)):
    id_, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    resp = await LeadService.update_marked_the_lead_assisted_by(db, id, user_id, data.remarks)
    return resp


@router.get("/by-assistant/{status}", response_model=PaginatedLeadResponse)
async def get_my_leads_by_status(
    request: Request,
    status: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    user_id = request.state.user.user_id
    role = request.state.user.role

    if role not in ["admin", "investor-assistant"]:
        raise HTTPException(403, "you are not authorised to perform this operation")

    return await LeadService.get_leads_by_attendend_id_and_status(
        db=db,
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size
    )


@router.get("/by-assistant/{user_id}/{status}", response_model=PaginatedLeadResponse)
async def get_assistant_leads_by_status(
    request: Request,
    user_id: str,
    status: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    role = request.state.user.role

    if role not in ["admin", "investor-assistant"]:
        raise HTTPException(403, "you are not authorised to perform this operation")

    return await LeadService.get_leads_by_attendend_id_and_status(
        db=db,
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size
    )


@router.get("/export/{status}")
async def export_leads(status: str, db: Session = Depends(get_db)):
    file = await LeadService.convert_to_excel_all_status_wise_leads(db, status)
    if not file:
        return {"message": "No leads found for given filters"}
    return file



@router.get("/export/{status}/{start_date}/{end_date}")
async def export_leads(status: str, start_date: datetime, end_date: datetime, db: Session = Depends(get_db)):
    file = await LeadService.convert_to_excel_status_and_date_wise_leads(
        db, status, start_date, end_date
    )
    if not file:
        return {"message": "No leads found for given filters"}
    return file


@router.post("/assign-unassigned-leads-round-robin")
async def assign_unassigned_leads_round_robin(request: Request, db: Session = Depends(get_db)):
    """
    Assign all unassigned leads to investor assistants using round-robin distribution.
    Only accessible by admin users.
    """
    user_id, role = request.state.user.user_id, request.state.user.role
    if role not in ["admin"]:
        raise HTTPException(403, "you are not authorised to perform this operation")
    try:
        result = await LeadService.assign_unassigned_leads_round_robin(db, user_id)
        return result
    except Exception as e:
        logger.error(f"Error assigning leads: {str(e)}")
        raise HTTPException(500, f"Error during lead assignment: {str(e)}")



@router.post("/upload-excel", status_code=status.HTTP_200_OK)
async def upload_leads_excel(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an Excel file (.xlsx or .xls) containing bulk leads.
    Required columns in the sheet: 'email', 'fname', 'lname'
    Optional columns: 'i_am_type', 'description', 'phone', 'consent_check'
    """
    role = request.state.user.role
    if role not in{"admin", "investor-assistant"}:
        raise HTTPException(403, "You are not authorised to bulk upload the data.")
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file format. Please upload a valid Excel file (.xlsx or .xls)"
        )
    contents = await file.read()
    result = await LeadService.import_leads_from_excel(db, contents)
    return result





