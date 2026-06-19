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
from dotenv import load_dotenv
import os
import logging
from typing import List, Optional
import aioboto3
from app.core.utils_functions import generate_image_id

load_dotenv()
logger = logging.getLogger(__name__)


S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET", "your-bucket-name")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# class FileUploadService:

#     def __init__(self, id: str):
#         self.id = id
#         self.session = aioboto3.Session()

#     async def _get_s3_client(self):
#         """Helper to yield an async S3 client context."""
#         return self.session.client("s3", region_name=AWS_REGION)

#     def _generate_s3_key(self, folder_name: str, filename: str) -> str:
#         """Helper to generate standard S3 structural keys instead of local paths."""
#         return f"uploads/{self.id}/{folder_name}/{filename}".replace("//", "/")

#     def create_folder(self, folder_name: str) -> str:
#         """
#         In S3, folders don't physically exist until a file is inside.
#         We return the virtual prefix path for consistency with your architecture.
#         """
#         virtual_path = f"uploads/{self.id}/{folder_name}/"
#         logger.info(f"FileUploadService: S3 virtual prefix defined: {virtual_path}")
#         return virtual_path

#     async def delete_file(self, file_url_or_key: str) -> bool:
#         """
#         Deletes a single object from S3 using either its full URL or S3 key.
#         Returns True if deleted or if it didn't exist.
#         """
#         try:
#             # Extract key from URL if absolute URL is passed
#             s3_key = file_url_or_key
#             if "amazonaws.com/" in file_url_or_key:
#                 s3_key = file_url_or_key.split("amazonaws.com/")[-1]

#             async with self._get_s3_client() as s3:
#                 await s3.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
#                 logger.info(f"FileUploadService: S3 object {s3_key} deleted successfully")
#                 return True
#         except Exception as e:
#             logger.error(f"Failed to delete S3 object: {file_url_or_key}. Error: {e}")
#             return False
    
#     async def delete_folder(self, folder_prefix: str) -> bool:
#         """
#         Deletes a virtual folder (prefix) and all contents inside it from S3.
#         """
#         try:
#             # Extract key from URL if absolute URL is passed
#             if "amazonaws.com/" in folder_prefix:
#                 folder_prefix = folder_prefix.split("amazonaws.com/")[-1]
            
#             # Ensure it ends with a slash to avoid deleting sibling folders
#             if not folder_prefix.endswith("/"):
#                 folder_prefix += "/"

#             async with self._get_s3_client() as s3:
#                 # Paginate and find all items under the prefix
#                 paginator = s3.get_paginator("list_objects_v2")
#                 async for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix):
#                     if "Contents" in page:
#                         objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]
#                         if objects_to_delete:
#                             await s3.delete_objects(
#                                 Bucket=S3_BUCKET_NAME,
#                                 Delete={"Objects": objects_to_delete}
#                             )
                
#                 logger.info(f"FileUploadService: S3 virtual folder {folder_prefix} deleted successfully.")
#                 return True
#         except Exception as e:
#             logger.error(f"Failed to delete S3 folder prefix: {folder_prefix}. Error: {e}")
#             return False

#     async def upload_file(self, file: UploadFile, folder: str) -> dict:
#         """
#         Uploads a single file to S3 asynchronously.
#         """
#         ext = file.filename.split(".")[-1] if "." in file.filename else ""
#         unique_name = f"{generate_image_id()}.{ext}" if ext else generate_image_id()
        
#         s3_key = self._generate_s3_key(folder, unique_name)
        
#         # Read file contents
#         content = await file.read()
        
#         async with self._get_s3_client() as s3:
#             # You can add ExtraArgs if you want them to be public or have specific ContentTypes
#             await s3.put_object(
#                 Bucket=S3_BUCKET_NAME,
#                 Key=s3_key,
#                 Body=content,
#                 ContentType=file.content_type
#             )

#         logger.info("FileUploadService: File uploaded to S3 successfully.")
#         return {
#             "filepath": s3_key,
#             "folder_path": f"uploads/{self.id}/{folder}/"
#         }

#     @staticmethod
#     def convert_to_public_url(request: Request, s3_key: Optional[str]) -> Optional[str]:
#         """
#         Converts an S3 key into its standard AWS S3 public URL format.
#         (If your bucket is private, you would generate presigned URLs here instead)
#         """
#         if not s3_key:
#             return None
#         # Standard S3 URL formulation
#         return f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

#     @staticmethod
#     async def upload_profile_image(db: Session, file: UploadFile, user_id: str, request: Request, role: str, file_type = None):
#         if role == "admin":
#             user_data = await AdminModel.get_by_id(db, user_id)
#         elif role == "investor-assistant":
#             user_data = await InvestorAssistant.get_by_id(db, user_id)
#         elif role == "fund-assistant":
#             user_data = await FundAssistant.get_by_id(db, user_id)
#         elif role == "investor":
#             user_data = await Investors.get_by_id(db, user_id)
#         else:
#             user_data = await Property.get_by_id(db, user_id)

#         if not user_data:
#             raise ValueError("User not found")
            
#         service = FileUploadService(user_id)

#         if file:
#             resp = await service.upload_file(file, f"{user_id}")
#             if not resp:
#                 logger.error("FileUploadService: S3 file upload failed")
#                 raise HTTPException(500, "File upload failed")

#             # Generate public S3 URL
#             file_url = FileUploadService.convert_to_public_url(request, resp["filepath"])

#             if role == "property":
#                 if file_type == "profile":
#                     user_data.property_image = file_url
#                 else:
#                     user_data.property_sheet = file_url
#             else:
#                 user_data.profile_image = file_url

#             await db.commit()
#             await db.refresh(user_data)

#             return {
#                 "message": "Profile image uploaded successfully",
#                 "profile_image": file_url,
#             }

#     @staticmethod
#     async def upload_other_docs(db: Session, file: UploadFile, logged_user_id: str, user_id: str, name: str, request: Request, role: str):
#         if role == "investor":
#             user_data = await Investors.get_by_id(db, user_id)
#         else:
#             user_data = await Property.get_by_id(db, user_id)

#         if not user_data:
#             raise ValueError("User not found")
            
#         service = FileUploadService(user_id)

#         if file:
#             resp = await service.upload_file(file, f"{user_id}")
#             if not resp:
#                 logger.error("FileUploadService: S3 file upload failed")
#                 raise HTTPException(500, "File upload failed")

#             file_url = FileUploadService.convert_to_public_url(request, resp["filepath"])
            
#             upload_docs = UploadedDocument(
#                 file_type_name = name,
#                 file_url = file_url,
#                 added_by = logged_user_id,
#                 added_for = user_id
#             )
#             db.add(upload_docs)
#             logger.info("FileUploadService: file uploaded to S3 and info stored into database.")
#             await db.commit()
#             await db.refresh(upload_docs)
            
#             return {
#                 "message": f"{name} Document uploaded successfully",
#                 "name": upload_docs.file_type_name,
#                 "doc_url": upload_docs.file_url,
#                 "added_for": upload_docs.added_for,
#                 "added_by": upload_docs.added_by
#             }

#     @staticmethod
#     async def upload_multiple_files(db: Session, request: Request, files: List[UploadFile], property_id: str, folder: str):
#         property_data = await Property.get_by_id(db, property_id)
#         if not property_data:
#             raise HTTPException(status_code=404, detail="Property Not Found")

#         service = FileUploadService(property_id)
#         folder_prefix = f"uploads/{property_id}/{folder}/"
        
#         # Simulating clearing out an S3 prefix namespace safely before overwriting
#         await service.delete_folder(folder_prefix)
        
#         uploaded_metadata = []

#         for file in files:
#             resp = await service.upload_file(file, folder)
#             uploaded_metadata.append({
#                 "original_name": file.filename,
#                 "filepath": resp["filepath"]
#             })
            
#         # Storing the directory path prefix context or the primary updated link
#         property_data.property_image = folder_prefix
#         logger.info("FileUploadService: Multiple files uploaded to S3 namespaces successfully.")
#         await db.commit()
#         await db.refresh(property_data)
        
#         public_links = await FileUploadService.get_folder_public_links(request, folder_prefix)
#         return {
#             "folder_path": folder_prefix,
#             "files_count": len(uploaded_metadata),
#             "public_urls": public_links,
#             "files": uploaded_metadata
#         }

#     @staticmethod
#     async def get_all_uploaded_docs(db: Session, added_for_id: str):
#         return await UploadedDocument.get_by_uploaded_for(db, added_for_id)

#     @staticmethod
#     async def get_folder_public_links(request: Request, folder_prefix: str) -> List[str]:
#         """
#         Queries S3 via aioboto3 to list items under a prefix and returns public URLs.
#         """
#         if not folder_prefix:
#             return []

#         if "amazonaws.com/" in folder_prefix:
#             folder_prefix = folder_prefix.split("amazonaws.com/")[-1]

#         public_urls = []
#         session = aioboto3.Session()
        
#         async with session.client("s3", region_name=AWS_REGION) as s3:
#             paginator = s3.get_paginator("list_objects_v2")
#             async for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=folder_prefix):
#                 if "Contents" in page:
#                     for obj in page["Contents"]:
#                         # Exclude any directory placeholders if they exist
#                         if not obj["Key"].endswith("/"):
#                             public_urls.append(FileUploadService.convert_to_public_url(request, obj["Key"]))
                            
#         logger.info("FileUploadService: Generated public S3 object links dynamically via prefix scanner.")
#         return public_urls


#    async def get_profile_image_buffer(db, request, user_id, role):
#       if role == "admin":
#            admin = await AdminModel.get_by_id(db, user_id)
#            return FileUploadService.convert_to_public_url(request, admin.profile_image)
#        elif role == "investor-assistant":
#            inv_assist = await InvestorAssistant.get_by_id(db, user_id)
#            return FileUploadService.convert_to_public_url(request, inv_assist.profile_image)
#        elif role == "fund-assistant":
#            fund_assist = await FundAssistant.get_by_id(db, user_id)
#           return FileUploadService.convert_to_public_url(request, fund_assist.profile_image)
#        else:
#            investor = await Investors.get_by_id(db, user_id)
#            return FileUploadService.convert_to_public_url(request, investor.profile_image)



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
    

    async def get_profile_image_buffer(db, request, user_id, role):
        if role == "admin":
            admin = await AdminModel.get_by_id(db, user_id)
            return FileUploadService.convert_to_public_url(request, admin.profile_image)
        elif role == "investor-assistant":
            inv_assist = await InvestorAssistant.get_by_id(db, user_id)
            return FileUploadService.convert_to_public_url(request, inv_assist.profile_image)
        elif role == "fund-assistant":
            fund_assist = await FundAssistant.get_by_id(db, user_id)
            return FileUploadService.convert_to_public_url(request, fund_assist.profile_image)
        else:
            investor = await Investors.get_by_id(db, user_id)
            return FileUploadService.convert_to_public_url(request, investor.profile_image)