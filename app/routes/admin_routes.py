from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.admin_service import AdminService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.admin import AdminCreate, AdminUpdate, AdminResponse
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
    admin = await AdminService.update_admin(db, user_id, data, request)
    return AdminResponse.model_validate(admin)

@router.get("/me", response_model = AdminResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    admin = await AdminService.get_my_info(db, user_id)
    if not admin:
        raise HTTPException(404, "Admin data not found")
    return AdminResponse.model_validate(admin)





