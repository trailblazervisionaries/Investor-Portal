from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from dotenv import load_dotenv
import os
import logging
logger = logging.getLogger(__name__)
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY", "NIWFNWIETNPFNKOFomefemtkmkpmewfwf")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def create_auth_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes = 25)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        logger.info("Token decoded successfully")
        return payload
    except ExpiredSignatureError:
        logger.error("Token has expired", exc_info=True)
        raise HTTPException(status_code=401, detail="Token has expired")

    except JWTError:
        logger.error("Invalid token", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid token")


