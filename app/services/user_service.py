from fastapi import Request, Response, HTTPException
from app.models.user_model import Users, OtpModel
from app.core.hash import hash_password, verify_password
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.core.auth import create_auth_token
from app.core.utils_functions import generate_id, generate_otp
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.templates.send_template_mail import MailTemplatesService
from datetime import timedelta
from dotenv import load_dotenv
import os
import logging
logger = logging.getLogger(__name__)

load_dotenv()
DOMAIN = os.getenv("DOMAIN", "localhost")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

class UserServices:
    @staticmethod
    async def add_new_user(db, role: str, email: str, password: str):
        allowed_roles = {"admin", "investor-assistant", "fund-assistant", "investor"}
        if role not in allowed_roles:
            logger.error("UserService: Invalid role provided")
            raise HTTPException(
                status_code=400,
                detail="UserService: Invalid role provided"
            )
        existing_user = await Users.by_email(db, email)
        if existing_user:
            logger.error("UserService: User email already exists")
            raise HTTPException(
                status_code=400,
                detail="UserService: User email already exists"
            )
        hashed_password = hash_password(password)
        new_user = Users(
            user_id=generate_id("user"),
            role=role,
            email=email,
            password=hashed_password,
        )
        db.add(new_user)
        await db.flush()  
        logger.info(
            "UserService: new user credentials recorded (not committed yet)"
        )
        return new_user



    async def UserLogin(db: Session, email: str, password: str, response: Response):
        user = await Users.get_by_email(db, email)

        if not user:
            logger.error("UserService: User with this email not found or user deactivated or deleted")
            raise HTTPException(404, "UserService: User with this email not found or user deactivated or deleted")
        
        if not verify_password(password, user.password):
            logger.error("UserService: User password verification failed due to password mismatch please enter correct password")
            raise HTTPException(403, "UserService: User password verification failed due to password mismatch please enter correct password")
        access_token = create_auth_token(
            data = {'sub': user.email, 'user_id': user.user_id, 'role': user.role},
            expires_delta= timedelta(hours = ACCESS_TOKEN_EXPIRE_HOURS),
        )

        token_expiry = timedelta(hours = ACCESS_TOKEN_EXPIRE_HOURS)
        expiry_seconds = int(token_expiry.total_seconds())
        cookie_domain = None if DOMAIN in ("localhost", "127.0.0.1", "") else DOMAIN
        response.set_cookie(
                    key="auth",
                    value=access_token,
                    samesite="Lax",
                    secure=False,
                    max_age=expiry_seconds,
                    expires=expiry_seconds,
                    domain=cookie_domain,
                    path='/'
                )
        return {
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role,
            "access_token": access_token,
            "token_type": "bearer",
        }
    
  
    async def update_user_password(db: Session, user_id: str, new_password: str):
        user = await Users.get_by_id(db, user_id)
        if not user:
            return None
        hashed_pw = hash_password(new_password)
        user.password = hashed_pw
        await db.commit()
        await db.refresh(user)
        # MonitorAsync.deferred(MailTemplatesService.send_notif_password_change, user.email)
        logger.info("UserServices: Password updated successfully :)")
        return user


    async def forgot_password(db: Session, email: str):
        user = await Users.get_by_email(db, email)
        if not user:
            return None
        new_otp = generate_otp()
        existing = await OtpModel.by_email(db, email)
        if existing and existing.is_used == True:
            existing.otp_code = new_otp
            existing.is_used = False
        elif existing and existing.is_used == False:
            existing.otp_code = new_otp
        else:
            new_record = OtpModel(email=email,otp_code=new_otp)
            db.add(new_record)
        await db.commit()  
        MonitorAsync.deferred(MailTemplatesService.send_otp_template,email, new_otp)
        return {"message": "OTP sent successfully"}


    async def reset_password(db: Session, email: str, otp_code: str, new_password: str):
        user = await Users.get_by_email(db, email)
        if not user:
            return None
        existing = await OtpModel.get_by_email(db, email)
        if not existing:
            logger.error("UserService: OTP not found with this email or already used")
            raise HTTPException(status_code=400, detail="UserService: OTP not found or already used")
        if existing.otp_code != otp_code:
            logger.error("UserService: Invalid OTP provided by the user")
            raise HTTPException(status_code=400, detail="UserService: Invalid OTP")
        existing.is_used = True
        hashed_pw = hash_password(new_password)
        user.password = hashed_pw
        await db.commit()       
        await db.refresh(user)
        MonitorAsync.deferred(MailTemplatesService.send_notif_password_change, email)
        logger.info("AdminAuthService: Password changed successfully")
        return {"message": "Password changed successfully"}


    def logout(request: Request, response: Response):   
        try:
            response.delete_cookie(
                    key="auth",
                    samesite="Lax",
                    secure=False,
                    domain=DOMAIN,
                    path='/'
                )
            logger.info("UserService: Logged out successfully")
            return {"message": "UserService: Logged out successfully"}
        except Exception as e:
                logger.error("UserService: Error during logout: %s", e)
                raise HTTPException(status_code=500, detail="UserService: Internal server error")
        

# @router.post("/refresh")
# async def refresh_token(request: Request, response: Response, db: Session):
#     refresh_token = request.cookies.get("refresh_token")

#     if not refresh_token:
#         raise HTTPException(401, "Refresh token missing")

#     payload = verify_refresh_token(refresh_token)
#     user_id = payload.get("user_id")

#     user = await Users.get_by_id(db, user_id)
#     if not user or user.is_deleted:
#         raise HTTPException(401, "Invalid refresh token")

#     new_access_token = create_auth_token(
#         data={"sub": user.email, "user_id": user.user_id, "role": user.role},
#         expires_delta=timedelta(hours=24),
#     )

#     return {"access_token": new_access_token}
