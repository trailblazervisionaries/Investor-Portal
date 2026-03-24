from app.models.admin_model import AdminModel
from app.models.investor_assist_model import InvestorAssistant
from app.models.fund_assist_model import FundAssistant
from app.models.investor_model import Investors
from app.models.user_model import UploadedDocument
from sqlalchemy.ext.asyncio import AsyncSession as Session
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, UploadFile
from app.models.audit_model import AuditModel
from io import BytesIO
import uuid
import boto3
from dotenv import load_dotenv
import os

load_dotenv()

AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_REGION = os.getenv("AWS_REGION") 

s3_client = boto3.client("s3")

class FileImageProcessService:

    async def upload_profile_image(db: Session, file: UploadFile, user_id: StopAsyncIteration, role: str):
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

  