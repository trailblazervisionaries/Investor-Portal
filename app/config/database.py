from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base
import importlib
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")

if DATABASE_URL is None:
    logger.error("POSTGRES_URL environment variable is not set.")
    raise RuntimeError("Missing POSTGRES_URL env var")

# Convert sync URL → async URL
# postgresql:// → postgresql+asyncpg://
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency: yields an async DB session and ensures it's closed.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    """
    Import model modules at runtime so they register with Base.metadata.
    """
    modules = [
        "app.models.address_model",
        "app.models.admin_model",
        "app.models.audit_model",
        "app.models.expenses_model",
        "app.models.fund_assist_model",
        "app.models.income_model",
        "app.models.investor_assist_model",
        "app.models.investor_model",
        "app.models.property_model",
        "app.models.user_model",
        "app.models.leads"
    ]

    for m in modules:
        importlib.import_module(m)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)





