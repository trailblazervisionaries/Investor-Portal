from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from app.config.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.services.file_img_process import FileImageProcessService, FileUploadService
from app.schemas.file_schemas import FileReturnResponse

import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


# @router.post("/upload-profile/{user_id}/{role}")
# async def upload_profile(
#     request: Request,
#     user_id: str,
#     role: str,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
# ):
#     return await FileUploadService.upload_profile_image(db, file, user_id, request, role)


@router.post("/upload-docs/{user_id}")
async def upload_profile(
    request: Request,
    user_id: str,
    role: str,
    name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    logged_user_id = request.state.user.user_id
    return await FileUploadService.upload_other_docs(db, file, logged_user_id, user_id, name, request, role)


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


@router.get("/get-uploaded-doc/{added_for_id}", response_model=list[FileReturnResponse])
async def get_all_uploaded_doc(
    added_for_id: str,
    db: Session = Depends(get_db),
):
    response = await FileUploadService.get_all_uploaded_docs(db, added_for_id)
    if not response:
        return []
        # raise HTTPException(status_code=404, detail="Image not found in storage")
    return [FileReturnResponse.model_validate(res) for res in response]




