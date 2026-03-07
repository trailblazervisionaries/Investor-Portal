from pydantic import BaseModel
from datetime import datetime
from typing import Any, List, Optional

class AuditLogResponse(BaseModel):
    id: int
    added_by: str
    new_data: Optional[dict] = None
    old_data: Optional[dict] = None
    audit_type: str
    entity_type: str
    object_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class AuditPaginationWrapper(BaseModel):
    items: List[AuditLogResponse]
    total_count: int
    page: int
    size: int