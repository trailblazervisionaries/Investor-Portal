from app.models.admin_model import AdminModel
from app.models.investor_assist_model import InvestorAssistant
from app.models.fund_assist_model import FundAssistant
from app.models.investor_model import Investors
from app.models.user_model import UploadedDocument
from app.models.property_model import Property
from sqlalchemy.ext.asyncio import AsyncSession as Session
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, UploadFile, Request
from app.models.audit_model import AuditModel
from io import BytesIO
from typing import List
import uuid
import boto3
from dotenv import load_dotenv
import os

load_dotenv()

AWS_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION") 

s3_client = boto3.client("s3")

class FileImageProcessService:

    async def upload_profile_image(db: Session, file: UploadFile, user_id: str, request: Request, role: str):
        if role == "admin":
            user_data = await AdminModel.get_by_id(db, user_id)
        elif role == "investor-assistant":
            user_data = await InvestorAssistant.get_by_id(db, user_id)
        elif role == "fund-assistant":
            user_data = await FundAssistant.get_by_id(db, user_id)
        else:
            user_data = await Investors.get_by_id(db, user_id)

        if not user_data:
            raise ValueError("User not found")
        

        # Delete old image if exists
        if user_data.profile_image:
            try:
                old_key = user_data.profile_image.split(".amazonaws.com/")[-1]
                s3_client.delete_object(Bucket=AWS_BUCKET, Key=old_key)
            except Exception as e:
                print(f"Warning: failed to delete old image: {e}")

            # Generate unique filename
            file_ext = file.filename.split(".")[-1]
            unique_filename = f"profile/{role}/{user_id}/{uuid.uuid4()}.{file_ext}"

            file_content = await file.read()

        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=unique_filename,
            Body=file_content,
            ContentType=file.content_type,
            ACL="public-read",  # remove if bucket is private
        )

        # Generate public URL
        file_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"

        user_data.profile_image = file_url

        db.add(user_data)
        await db.commit()
        await db.refresh(user_data)

        return {
            "message": "Profile image uploaded successfully",
            "profile_image": file_url,
        }


#  upload any type file ----------------
    async def upload_file(db, file, user_id, id, name, role):
        
        file_ext = file.filename.split(".")[-1]
        unique_filename = f"profile/{role}/{id}/{uuid.uuid4()}.{file_ext}"

        file_content = await file.read()

        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=unique_filename,
            Body=file_content,
            ContentType=file.content_type,
            ACL="public-read",  # remove if bucket is private
        )

        # Generate public URL
        file_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        upload_docs = UploadedDocument(
            file_type_name = name,
            file_url = file_url,
            added_by = user_id,
            added_for = id
        )
        db.add(upload_docs)
        await db.flush(upload_docs)
        await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"file_type_name": name, "file_url": file_url, "added_by": user_id, "added_for": id},
            old_data = None,
            audit_type = "ADD",
            entity_type = "file Management",
            object_id = str(upload_docs.id)
        )

        await db.commit()
        return upload_docs



    async def get_profile_image_buffer(db: Session, role: str, user_id: str):
        """
        Fetch image from S3 and return as streaming buffer.
        file_key example: profile/fund-assistant/12/abc.jpg
        """
        if role == "admin":
            user = await AdminModel.get_by_id(db, user_id)
        elif role == "investor-assistant":
            user = await InvestorAssistant.get_by_id(db, user_id)
        elif role == "fund-assistant":
            user = await FundAssistant.get_by_id(db, user_id)
        else:
            user = await Investors.get_by_id(db, user_id)

        if not user or not user.profile_image:
            raise HTTPException(status_code=404, detail="Image not found")

        file_key = user.profile_image.split(".amazonaws.com/")[-1]

        try:
            s3_response = s3_client.get_object(
                Bucket=AWS_BUCKET,
                Key=file_key
            )
        except s3_client.exceptions.NoSuchKey:
            return None

        file_stream = BytesIO(s3_response["Body"].read())
        content_type = s3_response["ContentType"]

        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": "inline"
            }
        )



import os
import shutil
from app.core.utils_functions import generate_image_id
UPLOAD_BASE = "uploads"
import logging
logger = logging.getLogger(__name__)

class FileUploadService:

    def __init__(self, id: str):
        self.id = id

    def create_folder(self, folder_name: str):

        path = os.path.join(UPLOAD_BASE, self.id, folder_name)
        os.makedirs(path, exist_ok=True)
        logger.info("FileUploadService: Folder created successfully")
        return path

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes a single file safely.
        Returns True if deleted or file doesn't exist.
        """
        try:
            # File exists?
            if file_path and os.path.isfile(file_path):
                os.remove(file_path)
                logger.info("FileUploadService: File deleted successfully")
                return True

            # File does not exist — treat as "successful delete"
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {file_path}. Error:{e}")
            print(f"[ERROR] Failed to delete file: {file_path}. Error: {e}")
            return False
    
    def delete_folder(self, folder_path: str) -> bool:
        """
        Deletes the entire folder safely.
        Returns True if deleted or folder doesn't exist.
        """
        try:
            # Folder exists?
            if folder_path and os.path.exists(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)
                logger.info("FileUpoadService: Folder Deleted Successfully.")
                return True

            # Folder does not exist — treat as "successful delete"
            return True

        except Exception as e:
            logger.error(f"Failed to delete folder: {folder_path}. Error:{e}")
            print(f"[ERROR] Failed to delete folder: {folder_path}. Error: {e}")
            return False
        

    async def upload_profile_image(db: Session, file: UploadFile, user_id: str, request: Request, role: str, file_type = None):
        if role == "admin":
            user_data = await AdminModel.get_by_id(db, user_id)
        elif role == "investor-assistant":
            user_data = await InvestorAssistant.get_by_id(db, user_id)
        elif role == "fund-assistant":
            user_data = await FundAssistant.get_by_id(db, user_id)
        elif role == "investor":
            user_data = await Investors.get_by_id(db, user_id)
        else:
            user_data = await Property.get_by_id(db, user_id)  # here user_id is equal to Property_id  only here ok

        if not user_data:
            raise ValueError("User not found")
        service = FileUploadService(user_id)

        if file:
            resp = await service.upload_file(file, f"{user_id}")
            if not resp:
                logger.error("AdminAuthService: file upload failed")
                raise HTTPException(500, "File upload failed")
            print("response  : ", resp)

        # Generate public URL
        file_url = FileUploadService.convert_to_public_url(request, resp["filepath"])
        # print("file-url ", file_url)

        if role == "property":
            if file_type == "profile":
                user_data.property_image = file_url
            else:
                user_data.property_sheet = file_url
        else:
            user_data.profile_image = file_url

        await db.commit()
        await db.refresh(user_data)

        return {
            "message": "Profile image uploaded successfully",
            "profile_image": file_url,
        }

    def convert_to_public_url(request: Request, local_path: str | None):
        if not local_path:
            return None
        BASE_URL = str(request.base_url).rstrip("/") 
        web_path = local_path.replace("\\", "/")
        return f"{BASE_URL}/{web_path}"

    async def upload_file(self, file, folder: str):

        # Folder path
        folder_path = os.path.join(UPLOAD_BASE, self.id, folder)
        os.makedirs(folder_path, exist_ok=True)

        # Unique filename
        ext = file.filename.split(".")[-1]
        unique_name = f"{generate_image_id()}.{ext}"
        final_path = os.path.join(folder_path, unique_name)
        folder_path = os.path.join(folder_path)
        # Save file
        with open(final_path, "wb") as buffer:
            buffer.write(await file.read())

        logger.info("FileUploadService: File uploaded successfully.")
        # return metadata
        return {
            "filepath": final_path,
            "folder_path":folder_path
        }
    

    
    async def upload_other_docs(db: Session, file: UploadFile, logged_user_id:str, user_id: str, name: str, request: Request, role: str):
        if role == "investor":
            user_data = await Investors.get_by_id(db, user_id)
        else:
            user_data = await Property.get_by_id(db, user_id)  # here user_id is equal to Property_id  only here ok

        if not user_data:
            raise ValueError("User not found")
        service = FileUploadService(user_id)

        if file:
            resp = await service.upload_file(file, f"{user_id}")
            if not resp:
                logger.error("AdminAuthService: file upload failed")
                raise HTTPException(500, "File upload failed")
            print("response  : ", resp)

        # Generate public URL
        file_url = FileUploadService.convert_to_public_url(request, resp["filepath"])
        # print("file-url ", file_url)
        upload_docs = UploadedDocument(
            file_type_name = name,
            file_url = file_url,
            added_by = logged_user_id,
            added_for = user_id
        )
        db.add(upload_docs)
        logger.info("FileUploadService: file uploaded successfully and their info also stored into the database.")
        await db.commit()
        await db.refresh(upload_docs)
        return {
            "message": f"{name} Document uploaded successfully",
            "name": upload_docs.file_type_name,
            "doc_url":upload_docs.file_url,
            "added_for": upload_docs.added_for,
            "added_by":upload_docs.added_by
        }



    async def upload_multiple_files(db, request, files: List[UploadFile], property_id: str, folder: str):
        property_data = await Property.get_by_id(db, property_id)
        if not property_data:
            raise HTTPException(status_code=404, detail="Property Not Found")

        folder_path = os.path.join(UPLOAD_BASE, str(property_id), folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)  

        os.makedirs(folder_path, exist_ok=True)
        
        uploaded_metadata = []

        for file in files:
            ext = file.filename.split(".")[-1]
            unique_name = f"{generate_image_id()}.{ext}"
            final_path = os.path.join(folder_path, unique_name)

            with open(final_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            uploaded_metadata.append({
                "original_name": file.filename,
                "filepath": final_path
            })
        property_data.property_image = folder_path
        logger.info("FileUploadService: Multiple files uploaded successfully and their info also stored into the database.")
        await db.commit()
        await db.refresh(property_data)
        public_links = FileUploadService.get_folder_public_links(request, folder_path)
        return {
            "folder_path": folder_path,
            "files_count": len(uploaded_metadata),
            "public_urls":public_links,
            "files": uploaded_metadata
        }




    async def get_all_uploaded_docs(db: Session, added_for_id: str):

        return await UploadedDocument.get_by_uploaded_for(db, added_for_id)
      


    def get_folder_public_links(request: Request, folder_path: str):
        if not folder_path or not os.path.exists(folder_path):
            return []

        public_urls = []
        # Loop through all files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            # Check if it's a file (not a subfolder)
            if os.path.isfile(file_path):
                public_urls.append(FileUploadService.convert_to_public_url(request, file_path))
        logger.info("FileUploadServices: Generated public links for the folder which is availabe on local disk.")
        return public_urls
    

    