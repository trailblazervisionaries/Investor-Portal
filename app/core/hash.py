from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")


def hash_password(plain_password: str) -> str :
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password) -> bool :
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        logger.error("Password verification is failed", exc_info=True)
        return False