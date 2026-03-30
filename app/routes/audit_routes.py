from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.models.audit_model import AuditModel
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.audit_log import AuditPaginationWrapper
from typing import List, Optional
import logging 
from datetime import datetime
import math
logger = logging.getLogger(__name__)


router = APIRouter()

@router.get("/audit", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20
):
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs(db, skip=skip, limit=size)
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }



@router.get("/audit-logs", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs_by_date_range(
        db, 
        skip=skip, 
        limit=size, 
        start_date=start_date, 
        end_date=end_date
    )
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }


@router.get("/audit-logs/{entity_type}", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    entity_type: str,
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs_by_date_range_and_entiry_type(
        db, 
        entity_type = entity_type,
        skip=skip, 
        limit=size, 
        start_date=start_date, 
        end_date=end_date
    )
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }


@router.get("/audit-logs/{user_id}", response_model=AuditPaginationWrapper)
async def get_audit_logs_using_user_id(
    user_id: str,
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs_by_date_range_and_added_by(
        db, 
        user_id = user_id,
        skip=skip, 
        limit=size, 
        start_date=start_date, 
        end_date=end_date
    )
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }



