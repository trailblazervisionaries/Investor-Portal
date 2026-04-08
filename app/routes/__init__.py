from fastapi import Request, HTTPException,Depends
from typing import Optional, Dict, List
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from fastapi.responses import JSONResponse
from app.models.user_model import Users
from app.config.database import get_db, AsyncSessionLocal
from dotenv import load_dotenv
import os
import logging
logger = logging.getLogger(__name__)
load_dotenv()
secret_key = os.getenv("SECRET_KEY")

class APIMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):
        try:
            if request.method == "OPTIONS" or self.should_skip_auth(request.url.path):
                return await call_next(request)
            token = await self.get_token(request)
            if not token:
                logger.warning("APIMiddleware: Token not found in request")
                raise HTTPException(status_code=401, detail="Token not found")

            user = await self.verify_token(token)
            # print("user : ", user)
            # print("expired: ", expired)
            if not user:
                logger.warning("APIMiddleware: Invalid token provided")
                raise HTTPException(status_code=401, detail="Invalid token")
            request.state.user = user
            # request.state.expired = expired
            response = await call_next(request)
            return response

        except HTTPException as e:
            logger.error("APIMiddleware: HTTPException occurred: %s", e.detail)
            return self.error_response(e.status_code, e.detail)
        except Exception as e:
            logger.error("APIMiddleware: Unexpected error occurred: %s", str(e))
            return self.error_response(500, str(e))

    def should_skip_auth(self, path: str) -> bool:
        # Add paths that don't need authentication
        skip_paths = [
            "/api/admin/public",
            "/api/user/public",
            "/api/users",
            "/api/lead/add",
            "/send-test-email",
            "/docs",
            "/health",
            "/uploads/",
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    async def get_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        token = request.cookies.get("auth")
        if token:
            return token
        logger.warning("APIMiddleware: No token found in headers or cookies")
        return None
    
    async def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            userEmail: str = payload.get("sub")
            userRole: str = payload.get("role")
            if userEmail is None or userRole is None:
                print("Payload is None")
                logger.warning("APIMiddleware: No Payload found in jwt token")
                return None
            print("user token data : ", userEmail, userRole)
            db = AsyncSessionLocal()
            try:
                user_data = await Users.get_by_email(db, userEmail)
                print("user_data  ", user_data)
                return user_data  
            finally:
                await db.close()

        except ExpiredSignatureError:
            logger.warning("APIMiddleware: Token has expired :(")
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError:
            logger.warning("APIMiddleware: Invalid token provided :(")
            raise HTTPException(status_code=401, detail="Invalid token")


    def error_response(self, status_code: int, detail: str):
        time = datetime.now().isoformat()
        logger.error(f"ApiMiddleWare: error in response see the detials : {detail}, at time: {time}")
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "detail": f"{detail} :(",
                "timestamp": time
            }
        )
    

    


   