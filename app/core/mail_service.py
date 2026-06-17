import aiosmtplib
from email.message import EmailMessage
from fastapi import HTTPException
from dotenv import load_dotenv
import os
from aiosmtplib.errors import SMTPAuthenticationError, SMTPConnectError
load_dotenv()
import logging
logger = logging.getLogger(__name__)
# safe env reads with defaults and strip
RAW_EMAIL = os.getenv("FROM_EMAIL").strip()
EMAIL_FROM = f"InvestmentPortal (no-reply) <{RAW_EMAIL}>"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com").strip()
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587").strip())
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "").strip()
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower().strip() in ("1", "true", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower().strip() in ("1", "true", "yes")

# # validate required settings early so errors are clear
# if not EMAIL_FROM:
#     raise RuntimeError("Missing EMAIL_FROM or FROM_EMAIL env var")
# if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
#     raise RuntimeError("Missing EMAIL_HOST_USER or EMAIL_HOST_PASSWORD env vars")

class MailService:
    @staticmethod
    async def send_mail(email: str, subject: str, html_message: str):
        try:
            message = EmailMessage()
            message["From"] = EMAIL_FROM
            message["To"] = email
            message["Subject"] = subject
            message.set_content(html_message, subtype="html")

            # choose start_tls (port 587) or use_tls (port 465)
            start_tls = False
            use_tls = False
            if EMAIL_PORT == 465 or EMAIL_USE_SSL:
                use_tls = True
            elif EMAIL_PORT == 587 or EMAIL_USE_TLS:
                start_tls = True

            await aiosmtplib.send(
                message,
                hostname=EMAIL_HOST,
                port=EMAIL_PORT,
                start_tls=start_tls,
                use_tls=use_tls,
                username=EMAIL_HOST_USER,
                password=EMAIL_HOST_PASSWORD,
            )
            logger.info(f"email sent to {email} successfully")
            return {"message": "Email sent successfully :)"}

        except SMTPAuthenticationError:
            logger.error("SMTP authentication failed", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=(
                    "SMTP authentication failed. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD. "
                    "If using Gmail enable 2-Step Verification and create an App Password."
                ),
            )
        except SMTPConnectError as e:
            logger.error("SMTP connection failed", exc_info=True)
            raise HTTPException(status_code=500, detail=f"SMTP connection failed: {e}")
        except Exception as e:
            logger.error("Email sending failed", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")



# import os
# import logging
# from email.message import EmailMessage
# from fastapi import HTTPException
# from dotenv import load_dotenv
# import aioboto3
# from botocore.exceptions import ClientError

# load_dotenv()
# logger = logging.getLogger(__name__)

# # Safe env reads
# RAW_EMAIL = os.getenv("FROM_EMAIL", "").strip()
# EMAIL_FROM = f"InvestmentPortal (no-reply) <{RAW_EMAIL}>"
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1").strip()
# AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
# AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()

# class MailService:
#     @staticmethod
#     async def send_mail(email: str, subject: str, html_message: str):
#         try:
#             # Build the standard email message
#             message = EmailMessage()
#             message["From"] = EMAIL_FROM
#             message["To"] = email
#             message["Subject"] = subject
#             message.set_content(html_message, subtype="html")

#             # Initialize asynchronous boto3 session
#             session = aioboto3.Session(
#                 aws_access_key_id=AWS_ACCESS_KEY,
#                 aws_secret_access_key=AWS_SECRET_KEY,
#                 region_name=AWS_REGION
#             )

#             # Send using SES SendRawEmail to support standard email formatting
#             async with session.client("ses") as ses_client:
#                 response = await ses_client.send_raw_email(
#                     Source=EMAIL_FROM,
#                     Destinations=[email],
#                     RawMessage={"Data": message.as_bytes()}
#                 )
            
#             logger.info(f"SES email sent to {email} successfully. MessageId: {response.get('MessageId')}")
#             return {"message": "Email sent successfully :)"}

#         except ClientError as e:
#             error_code = e.response['Error']['Code']
#             error_message = e.response['Error']['Message']
#             logger.error(f"AWS SES ClientError [{error_code}]: {error_message}", exc_info=True)
            
#             # Handle sandbox mode or unverified email issues gracefully
#             if error_code == "MessageRejected":
#                 raise HTTPException(
#                     status_code=400, 
#                     detail=f"Email rejected by SES. Ensure the sender/recipient is verified in sandbox mode: {error_message}"
#                 )
            
#             raise HTTPException(status_code=500, detail=f"AWS SES error: {error_message}")
            
#         except Exception as e:
#             logger.error("Email sending failed", exc_info=True)
#             raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


