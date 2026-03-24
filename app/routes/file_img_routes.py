from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File
from app.config.database import get_db
from app.services.user_service import UserServices
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.services.file_img_process import FileImageProcessService
from app.schemas.users import UserLogin, PasswordChange, ForgetPassword, ResetPassword
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-profile/{user_id}/{role}")
async def upload_profile(
    user_id: str,
    role: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await FileImageProcessService.upload_profile_image(db, file, user_id, role)


@router.get("/profile-image/{user_id}/{role}")
async def get_profile_image(
    user_id: str,
    role: str,
    db: Session = Depends(get_db),
):
    response = await FileImageProcessService.get_profile_image_buffer(db, user_id, role)
    if not response:
        raise HTTPException(status_code=404, detail="Image not found in storage")
    return response






