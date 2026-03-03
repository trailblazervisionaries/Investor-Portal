"""
Audit Log Service Module
=========================

This module provides utilities and helper functions for creating and managing audit logs.
It should be imported and used throughout the application to track all user actions and data changes.

Usage Example:
    from app.services.audit_service import AuditService
    
    # Log a property creation
    await AuditService.log_create(
        db=db,
        user_id=user_id,
        entity_type="PROPERTY",
        entity_id=property_id,
        entity_name=property_name,
        new_values=property_data,
        request=request,
        is_critical=False
    )
    
    # Log a property update
    await AuditService.log_update(
        db=db,
        user_id=user_id,
        entity_type="PROPERTY",
        entity_id=property_id,
        old_values=old_property_data,
        new_values=new_property_data,
        request=request,
        is_critical=True
    )
"""

import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import Request


class AuditService:
    """
    Service class for managing audit logs.
    All audit logging operations should go through this service.
    """

    @staticmethod
    def generate_audit_id() -> str:
        """Generate a unique audit log ID"""
        return f"AUD_{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def extract_request_info(request: Request) -> Dict[str, str]:
        """Extract relevant information from HTTP request"""
        return {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_method": request.method,
            "request_path": request.url.path,
        }

    @staticmethod
    def get_changed_fields(old_values: Dict, new_values: Dict) -> tuple:
        """
        Compare old and new values and return list of changed fields and summary.
        
        Returns:
            tuple: (changed_fields_list, changes_summary_dict)
        """
        changed_fields = []
        changes_summary = {}

        if not old_values:
            old_values = {}
        if not new_values:
            new_values = {}

        # Find changed fields
        all_keys = set(old_values.keys()) | set(new_values.keys())
        
        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)
            
            if old_val != new_val:
                changed_fields.append(key)
                changes_summary[key] = {
                    "old_value": old_val,
                    "new_value": new_val
                }

        return changed_fields, changes_summary

    @staticmethod
    async def log_create(
        db,
        user_id: str,
        entity_type: str,
        entity_id: str,
        entity_name: Optional[str] = None,
        new_values: Optional[Dict] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_critical: bool = False,
        affected_records_count: int = 1,
    ) -> str:
        """
        Log a CREATE operation (new record creation)
        
        Args:
            db: Database session
            user_id: ID of user performing the action
            entity_type: Type of entity being created (from EntityType enum)
            entity_id: ID of the entity
            entity_name: Human-readable name of entity
            new_values: Dictionary of new values
            request: FastAPI request object
            description: Optional description of the action
            tags: List of tags for categorization
            is_critical: Whether this is a critical operation
            affected_records_count: Number of records affected
            
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog, OperationType

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            operation_type=OperationType.CREATE.value,
            operation_status="SUCCESS",
            new_values=new_values,
            changed_fields=list(new_values.keys()) if new_values else [],
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or f"Created {entity_type}",
            tags=tags,
            is_critical=is_critical,
            affected_records_count=affected_records_count,
        )

        db.add(audit_log)
        await db.commit()
        return audit_id

    @staticmethod
    async def log_update(
        db,
        user_id: str,
        entity_type: str,
        entity_id: str,
        entity_name: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_critical: bool = False,
        affected_records_count: int = 1,
    ) -> str:
        """
        Log an UPDATE operation (record modification)
        
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog, OperationType

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}
        
        changed_fields, changes_summary = AuditService.get_changed_fields(
            old_values or {}, new_values or {}
        )

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            operation_type=OperationType.UPDATE.value,
            operation_status="SUCCESS",
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            changes_summary=json.dumps(changes_summary),
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or f"Updated {entity_type}: {', '.join(changed_fields)}",
            tags=tags,
            is_critical=is_critical,
            affected_records_count=affected_records_count,
        )

        db.add(audit_log)
        await db.commit()
        return audit_id

    @staticmethod
    async def log_delete(
        db,
        user_id: str,
        entity_type: str,
        entity_id: str,
        entity_name: Optional[str] = None,
        old_values: Optional[Dict] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_critical: bool = True,  # Deletions are critical by default
        affected_records_count: int = 1,
    ) -> str:
        """
        Log a DELETE operation (record deletion/soft-delete)
        Deletions are marked as critical operations by default.
        
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog, OperationType

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            operation_type=OperationType.DELETE.value,
            operation_status="SUCCESS",
            old_values=old_values,
            changed_fields=["is_deleted"] if old_values else [],
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or f"Deleted {entity_type}",
            tags=tags,
            is_critical=is_critical,
            affected_records_count=affected_records_count,
        )

        db.add(audit_log)
        await db.commit()
        return audit_id

    @staticmethod
    async def log_approval(
        db,
        user_id: str,
        entity_type: str,
        entity_id: str,
        entity_name: Optional[str] = None,
        approval_data: Optional[Dict] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Log an APPROVE operation (property approval, investment approval, etc.)
        
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog, OperationType

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            operation_type=OperationType.APPROVE.value,
            operation_status="SUCCESS",
            new_values=approval_data,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or f"Approved {entity_type}",
            tags=tags,
            is_critical=True,  # Approvals are always critical
        )

        db.add(audit_log)
        await db.commit()
        return audit_id

    @staticmethod
    async def log_auth_event(
        db,
        user_id: Optional[str],
        operation_type: str,  # LOGIN, LOGOUT, AUTH_FAILED, etc.
        user_email: Optional[str] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        is_critical: bool = False,
    ) -> str:
        """
        Log authentication events (login, logout, failed attempts, etc.)
        
        Args:
            operation_type: LOGIN, LOGOUT, AUTH_FAILED, PASSWORD_CHANGED, etc.
            
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            user_email=user_email,
            entity_type="AUTHENTICATION",
            entity_id=user_id or user_email or "unknown",
            operation_type=operation_type,
            operation_status="SUCCESS",
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or operation_type,
            is_critical=is_critical,
        )

        db.add(audit_log)
        await db.commit()
        return audit_id

    @staticmethod
    async def log_failed_operation(
        db,
        user_id: str,
        entity_type: str,
        entity_id: str,
        operation_type: str,
        error_message: str,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Log a failed operation attempt
        
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=operation_type,
            operation_status="FAILED",
            status_message=error_message,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or f"Failed {operation_type} on {entity_type}",
            tags=tags,
            is_critical=True,  # Failed operations are marked critical for review
        )

        db.add(audit_log)
        await db.commit()
        return audit_id

    @staticmethod
    async def log_bulk_operation(
        db,
        user_id: str,
        entity_type: str,
        operation_type: str,
        affected_count: int,
        request: Optional[Request] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Log bulk operations (e.g., batch update, batch delete)
        
        Returns:
            audit_id: ID of the created audit log
        """
        from app.models.audit_model import AuditLog

        audit_id = AuditService.generate_audit_id()
        request_info = AuditService.extract_request_info(request) if request else {}

        audit_log = AuditLog(
            audit_id=audit_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=f"BULK_{operation_type}",
            operation_type=operation_type,
            operation_status="SUCCESS",
            affected_records_count=affected_count,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            request_method=request_info.get("request_method"),
            request_path=request_info.get("request_path"),
            description=description or f"Bulk {operation_type} on {affected_count} {entity_type} records",
            tags=tags,
            is_critical=True,  # Bulk operations are critical
        )

        db.add(audit_log)
        await db.commit()
        return audit_id


# Example usage in routes/services:
# 
# @router.post("/properties")
# async def create_property(property_data: PropertySchema, request: Request, db: AsyncSession = Depends(get_db)):
#     user = await get_current_user(request)
#     
#     # Create property
#     property = Property(**property_data.dict())
#     db.add(property)
#     await db.commit()
#     
#     # Log the creation
#     await AuditService.log_create(
#         db=db,
#         user_id=user.user_id,
#         entity_type="PROPERTY",
#         entity_id=property.property_id,
#         entity_name=property.name,
#         new_values=property_data.dict(),
#         request=request,
#         is_critical=False
#     )
#     
#     return property
#
#
# @router.put("/properties/{property_id}")
# async def update_property(property_id: str, updates: PropertyUpdateSchema, request: Request, db: AsyncSession = Depends(get_db)):
#     user = await get_current_user(request)
#     
#     property = await db.get(Property, property_id)
#     old_values = property.dict()
#     
#     # Update property
#     for key, value in updates.dict().items():
#         if value is not None:
#             setattr(property, key, value)
#     await db.commit()
#     
#     # Log the update
#     await AuditService.log_update(
#         db=db,
#         user_id=user.user_id,
#         entity_type="PROPERTY",
#         entity_id=property.property_id,
#         old_values=old_values,
#         new_values=property.dict(),
#         request=request,
#         is_critical=True
#     )
#     
#     return property








