from fastapi import APIRouter, Depends, Query,Form, Request, HTTPException
from app.config.database import get_db
from app.models.audit_model import AuditModel
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.audit_log import AuditPaginationWrapper, UniqueAuditTypesResponse, DeleteAuditRecordsRequest
from typing import Optional
import logging 
from datetime import datetime
logger = logging.getLogger(__name__)


router = APIRouter()

@router.get("/audit", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    role = request.state.user.role
    if role not in ["admin","investor-assistant", "fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs(db, skip=skip, limit=size)
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }

@router.get("/get-all-types", response_model = UniqueAuditTypesResponse)
async def get_all_unique_type(request: Request, db: Session = Depends(get_db)):
    """
    Retrieves all unique audit types recorded in the system.
    """
    role = request.state.user.role
    if role not in ["admin","investor-assistant", "fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    unique_types = await AuditModel.get_all_unique_audit_types(db)
    return {
        "audit_types": unique_types
    }


@router.get("/audit-logs", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    role = request.state.user.role
    if role not in ["admin","investor-assistant", "fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    skip = (max(1, page) - 1) * size
    
    logs, total_count = await AuditModel.get_all_logs_by_date_range(
        db, 
        skip=skip, 
        limit=size, 
        start_date=start_date, 
        end_date=end_date
    )
    # print("logs", logs)
    
    return {
        "items": logs,
        "total_count": total_count,
        "page": page,
        "size": size
    }


@router.get("/audit-logs-type", response_model=AuditPaginationWrapper)
async def get_audit_logs(
    request:Request,
    entity_type: str = Form(...),
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    role = request.state.user.role
    if role not in ["admin","investor-assistant", "fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    skip = (max(1, page) - 1) * size
    # print(entity_type)
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
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    role = request.state.user.role
    if role not in ["admin","investor-assistant", "fund-assistant"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
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


@router.post("/delete-by-date")
async def delete_audit_records(
    request: Request,
    payload: DeleteAuditRecordsRequest, 
    db: Session = Depends(get_db)
):
    """
    Permanently deletes all audit logs within a specified date range.
    """
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "you are not authorise to perform this operation")
    deleted_count = await AuditModel.delete_audit_records_by_date(
        db=db, 
        start_date=payload.start_date, 
        end_date=payload.end_date
    )
    
    return {
        "status": "success",
        "message": f"Successfully deleted logs up to {payload.end_date}.",
        "deleted_count": deleted_count
    }
