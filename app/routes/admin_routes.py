from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from app.config.database import get_db
from app.services.admin_service import AdminService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.admin import AdminCreate, AdminUpdate, AdminResponse
from app.services.file_img_process import FileUploadService
from app.services.fund_assist_service import FundAssistService
from app.services.property_service import PropertyService
from app.services.investor_assist_service import InvestorAssistService
from app.services.investor_service import InvestorService
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/public/add", response_model = AdminResponse)
async def add_admin(data: AdminCreate, request: Request, db: Session = Depends(get_db)):
    admin = await AdminService.create_admin(db, data, request)
    return AdminResponse.model_validate(admin)


@router.put("/update", response_model = AdminResponse)
async def add_admin(data: AdminUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "You are not authorised to perform this operation")
    admin = await AdminService.update_admin(db, user_id, data, request)
    return AdminResponse.model_validate(admin)


@router.get("/me", response_model = AdminResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    admin = await AdminService.get_my_info(db, user_id)
    if not admin:
        raise HTTPException(404, "Admin data not found")
    return AdminResponse.model_validate(admin)


@router.post("/upload-profile/{user_id}/{role}")
async def upload_profile(
    request: Request,
    user_id: str,
    role: str = "admin",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "You are not authorised to perform this operation")
    return await FileUploadService.upload_profile_image(db, file, user_id, request, role)


@router.get("/dashboard-info")
async def get_all_info(db: Session = Depends(get_db)):
    fund_assist = await FundAssistService.get_total_count(db)
    properties = await PropertyService.get_property_statistics(db)
    inv_assist = await InvestorAssistService.get_total_count(db)
    inv = await InvestorService.get_total_count(db)
    return{
        "total_fund_assistant" : fund_assist,
        "total_properties" : properties,
        "total_investor_assistant": inv_assist,
        "total_investor":inv
    }



