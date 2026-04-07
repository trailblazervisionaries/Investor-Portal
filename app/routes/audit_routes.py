from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query,Form
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
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
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
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")

):
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs_by_date_range(
        db, 
        skip=skip, 
        limit=size, 
        start_date=start_date, 
        end_date=end_date
    )
    print("logs", logs)
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }


@router.get("/audit-logs-type", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    entity_type: str = Form(...),
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    skip = (max(1, page) - 1) * size
    print(entity_type)
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
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
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



