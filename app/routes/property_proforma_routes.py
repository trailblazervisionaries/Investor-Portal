from fastapi import APIRouter, Depends
from app.config.database import get_db
from app.services.proformance_service import PerformanceService
from sqlalchemy.ext.asyncio import AsyncSession as Session
import logging 

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/get-info/{property_id}")
async def get_all_info(property_id: str, db: Session = Depends(get_db)):
    return await PerformanceService.calculate_financial_summary(db, property_id)

