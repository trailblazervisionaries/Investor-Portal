from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import FileResponse
from app.config.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.services.file_img_process import FileImageProcessService, FileUploadService
from app.schemas.file_schemas import FileReturnResponse
from pathlib import Path
from urllib.parse import unquote, urlparse
import mimetypes

import logging 
logger = logging.getLogger(__name__)
router = APIRouter()
UPLOAD_ROOT = Path("uploads").resolve()


def resolve_uploaded_file_path(file_url: str) -> Path | None:
    if not file_url:
        return None

    parsed_url = urlparse(file_url)
    raw_path = unquote(parsed_url.path or file_url).replace("\\", "/")

    if "/uploads/" in raw_path:
        relative_path = raw_path.split("/uploads/", 1)[1]
    elif raw_path.startswith("uploads/"):
        relative_path = raw_path[len("uploads/"):]
    else:
        return None

    candidate_path = (UPLOAD_ROOT / Path(relative_path)).resolve()
    try:
        candidate_path.relative_to(UPLOAD_ROOT)
    except ValueError:
        return None

    return candidate_path


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
    role: str = Form(...),
    name: str = Form(...),
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


@router.get("/download-doc")
async def download_uploaded_doc(file_url: str, file_name: str | None = None):
    file_path = resolve_uploaded_file_path(file_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    media_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(
        path=str(file_path),
        filename=file_name or file_path.name,
        media_type=media_type or "application/octet-stream",
    )




