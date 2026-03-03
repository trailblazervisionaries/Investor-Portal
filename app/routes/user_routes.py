from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.user_service import UserServices
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.users import UserLogin, PasswordChange, ForgetPassword, ResetPassword
import logging 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/public/login")
async def login(data: UserLogin, response:Response, db: Session = Depends(get_db)):
    return await UserServices.UserLogin(db, data.email, data.password, response)


# routes related to password change ot forget----------------------------------------
@router.put("/change-password")
async def change_user_password(request: Request, data: PasswordChange, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    user = await UserServices.update_user_password(db, user_id, data.new_password)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Password updated successfully"}

@router.post("/public/forgot-password")
async def user_forget_password(data: ForgetPassword, db: Session = Depends(get_db)):
    user = await UserServices.forgot_password(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return {"message": "OTP sent to your email"}

@router.post("/public/reset-password")
async def user_reset_password( data: ResetPassword, db: Session = Depends (get_db)):
    user = await UserServices.reset_password(db, data.email, data.otp, data.new_password)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Password reset successfully"}

#  user logout routes =====================================
@router.post("/logout")
def logout(request: Request, response: Response):
    return UserServices.logout(request, response)







