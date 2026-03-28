from sqlalchemy.orm import relationship
from app.config.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey, Index, select, desc, func, and_
from datetime import datetime
from enum import Enum






class AuditModel(Base):
    __tablename__ = "auditmodel"

    id = Column(Integer, primary_key = True)
    added_by = Column(String, nullable = False)
    new_data = Column(JSON, nullable = True)
    old_data = Column(JSON, nullable = True)
    audit_type = Column(String, nullable = False)
    entity_type = Column(String, nullable = False)
    object_id = Column(String, nullable = False)
    created_at = Column(DateTime, nullable = False, default = datetime.utcnow)


    @staticmethod
    async def add_new_logs(db, added_by, new_data, old_data, audit_type, entity_type, object_id):
        new_log = AuditModel(
            added_by = added_by,
            new_data = new_data,
            old_data = old_data,
            audit_type = audit_type,
            entity_type = entity_type,
            object_id = object_id
        )
        db.add(new_log)


    @staticmethod
    async def get_all_logs(db, skip: int = 0, limit: int = 10):
        stmt = (
            select(AuditModel)
            .order_by(desc(AuditModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        count_stmt = select(func.count()).select_from(AuditModel)

        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        
        return result.scalars().all(), total_res.scalar() or 0



    @staticmethod
    async def get_all_logs_by_date_range(
        db, 
        skip: int = 0, 
        limit: int = 10, 
        start_date: datetime = None, 
        end_date: datetime = None
    ):
        stmt = select(AuditModel).order_by(desc(AuditModel.created_at))
        count_stmt = select(func.count()).select_from(AuditModel)
        filters = []
        if start_date:
            filters.append(AuditModel.created_at >= start_date)
        if end_date:
            filters.append(AuditModel.created_at <= end_date)

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        
        return result.scalars().all(), total_res.scalar() or 0
    


    @staticmethod
    async def get_all_logs_by_date_range_and_entiry_type(
        db, 
        entity_type: str,
        skip: int = 0, 
        limit: int = 10, 
        start_date: datetime = None, 
        end_date: datetime = None
    ):
        stmt = select(AuditModel).order_by(desc(AuditModel.created_at))
        count_stmt = select(func.count()).select_from(AuditModel)
        filters = []
        if start_date:
            filters.append(AuditModel.created_at >= start_date)
        if end_date:
            filters.append(AuditModel.created_at <= end_date)
        if entity_type:
            filters.append(AuditModel.entity_type == entity_type)

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        
        return result.scalars().all(), total_res.scalar() or 0
    



    
# class OperationType(str, Enum):
#     """Enum for types of operations that can be audited"""
#     CREATE = "CREATE"
#     READ = "READ"
#     UPDATE = "UPDATE"
#     DELETE = "DELETE"
#     APPROVE = "APPROVE"
#     REJECT = "REJECT"
#     EXPORT = "EXPORT"
#     IMPORT = "IMPORT"
#     LOGIN = "LOGIN"
#     LOGOUT = "LOGOUT"


# class EntityType(str, Enum):
#     """Enum for entity types that can be audited"""
#     # User Management
#     USER = "USER"
#     ADMIN = "ADMIN"
#     INVESTOR = "INVESTOR"
#     INVESTOR_ASSISTANT = "INVESTOR_ASSISTANT"
#     FUND_ASSISTANT = "FUND_ASSISTANT"
#     ADDRESS = "ADDRESS"
    
#     # Property Management
#     PROPERTY = "PROPERTY"
#     PROPERTY_UNIT_TYPE = "PROPERTY_UNIT_TYPE"
#     PROPERTY_UNIT = "PROPERTY_UNIT"
#     PROPERTY_LOAN = "PROPERTY_LOAN"
#     AMORTIZATION_SCHEDULE = "AMORTIZATION_SCHEDULE"
#     PROPERTY_UNIT_LEASE = "PROPERTY_UNIT_LEASE"
#     PROPERTY_UNIT_RENT_COLLECTION = "PROPERTY_UNIT_RENT_COLLECTION"
    
#     # Income & Expense
#     INCOME_TYPE = "INCOME_TYPE"
#     INCOME = "INCOME"
#     INCOME_GROWTH = "INCOME_GROWTH"
#     EXPENSE_TYPE = "EXPENSE_TYPE"
#     EXPENSE = "EXPENSE"
#     EXPENSE_GROWTH = "EXPENSE_GROWTH"
    
#     # Investment
#     INVESTOR_INVESTMENT = "INVESTOR_INVESTMENT"
#     INVESTOR_ASSIGNMENT = "INVESTOR_ASSIGNMENT"
    
#     # Authentication
#     AUTHENTICATION = "AUTHENTICATION"
#     OTP = "OTP"


# class AuditLog(Base):
#     """
#     Comprehensive audit log table that tracks all changes made in the system.
#     This model records every transaction, update, deletion, and significant action
#     taken by users in the application.
#     """
#     __tablename__ = "audit_log"

#     # Primary Key
#     audit_id = Column(String, primary_key=True, index=True)

#     # User Information
#     user_id = Column(String, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
#     user_email = Column(String, nullable=True, index=True)  # Cached email for deleted users
#     user_role = Column(String, nullable=True)  # Cached role (admin, investor, etc.)

#     # Entity Information
#     entity_type = Column(String, nullable=False, index=True)  # Using EntityType enum values
#     entity_id = Column(String, nullable=False, index=True)  # ID of the affected entity
#     entity_name = Column(String, nullable=True)  # Human-readable name of the entity (property name, etc.)

#     # Operation Details
#     operation_type = Column(String, nullable=False, index=True)  # Using OperationType enum values
#     operation_status = Column(String, default="SUCCESS")  # SUCCESS, FAILED, PENDING
#     status_message = Column(Text, nullable=True)  # Error message if operation failed
    
#     # Data Change Tracking
#     old_values = Column(JSON, nullable=True)  # Previous state of the entity (for UPDATE/DELETE)
#     new_values = Column(JSON, nullable=True)  # New state of the entity (for CREATE/UPDATE)
#     changed_fields = Column(JSON, nullable=True)  # List of fields that were changed
#     changes_summary = Column(Text, nullable=True)  # Human-readable summary of changes
    
#     # Request Information
#     ip_address = Column(String, nullable=True, index=True)  # IP address of the requester
#     user_agent = Column(String, nullable=True)  # Browser/app user agent
#     request_method = Column(String, nullable=True)  # HTTP method (GET, POST, PUT, DELETE, etc.)
#     request_path = Column(String, nullable=True)  # API endpoint that was called
#     request_id = Column(String, nullable=True, index=True)  # Unique request identifier for correlation
    
#     # Impact Information
#     affected_records_count = Column(Integer, default=1)  # Number of records affected (useful for bulk operations)
#     related_entities = Column(JSON, nullable=True)  # List of other entities affected by this operation
    
#     # Additional Context
#     description = Column(Text, nullable=True)  # Manual description or notes about the operation
#     tags = Column(JSON, nullable=True)  # Tags for categorizing audit events (e.g., ['property_update', 'investment_change'])
    
#     # Timestamp
#     created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
#     # Flags
#     is_critical = Column(Boolean, default=False, index=True)  # Flag for critical operations (deletions, approvals, etc.)
#     requires_review = Column(Boolean, default=False)  # Flag if operation needs manager review
#     reviewed_by = Column(String, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
#     reviewed_at = Column(DateTime, nullable=True)
#     review_notes = Column(Text, nullable=True)

#     # Relationships
#     user = relationship("Users", foreign_keys=[user_id], primaryjoin="AuditLog.user_id == Users.user_id")
#     reviewer = relationship("Users", foreign_keys=[reviewed_by], primaryjoin="AuditLog.reviewed_by == Users.user_id")

#     def __repr__(self):
#         return (
#             f"<AuditLog(audit_id='{self.audit_id}', entity_type='{self.entity_type}', "
#             f"operation_type='{self.operation_type}', user_id='{self.user_id}', "
#             f"created_at='{self.created_at}')>"
#         )


# class AuditLogSummary(Base):
#     """
#     Summary/aggregated view of audit logs for performance and reporting.
#     Stores daily summaries of operations grouped by entity type and user.
#     Useful for generating reports and analytics without querying millions of audit records.
#     """
#     __tablename__ = "audit_log_summary"

#     # Primary Key
#     id = Column(Integer, primary_key=True, index=True)

#     # Summary Information
#     summary_date = Column(DateTime, nullable=False, index=True)  # Date of the summary
#     entity_type = Column(String, nullable=False, index=True)
#     operation_type = Column(String, nullable=False, index=True)
#     user_id = Column(String, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)

#     # Aggregated Counts
#     total_operations = Column(Integer, default=0)  # Total number of operations
#     successful_operations = Column(Integer, default=0)
#     failed_operations = Column(Integer, default=0)
#     total_records_affected = Column(Integer, default=0)

#     # Critical Operations
#     critical_operations_count = Column(Integer, default=0)
#     requires_review_count = Column(Integer, default=0)

#     # Metadata
#     created_at = Column(DateTime, default=datetime.utcnow, index=True)
#     updated_at = Column(DateTime, onupdate=datetime.utcnow)

#     # Relationship
#     user = relationship("Users", foreign_keys=[user_id])

#     def __repr__(self):
#         return (
#             f"<AuditLogSummary(summary_date='{self.summary_date}', entity_type='{self.entity_type}', "
#             f"operation_type='{self.operation_type}', total_operations={self.total_operations})>"
#         )


# class AuditLogArchive(Base):
#     """
#     Archive table for old audit logs (older than 1-2 years).
#     Keeps main audit_log table optimized while maintaining historical data.
#     Queries should check both audit_log and audit_log_archive tables for complete history.
#     """
#     __tablename__ = "audit_log_archive"

#     # Primary Key
#     archive_id = Column(String, primary_key=True, index=True)

#     # User Information
#     user_id = Column(String, nullable=True, index=True)
#     user_email = Column(String, nullable=True, index=True)
#     user_role = Column(String, nullable=True)

#     # Entity Information
#     entity_type = Column(String, nullable=False, index=True)
#     entity_id = Column(String, nullable=False, index=True)
#     entity_name = Column(String, nullable=True)

#     # Operation Details
#     operation_type = Column(String, nullable=False, index=True)
#     operation_status = Column(String, default="SUCCESS")
#     status_message = Column(Text, nullable=True)

#     # Data Change Tracking
#     old_values = Column(JSON, nullable=True)
#     new_values = Column(JSON, nullable=True)
#     changed_fields = Column(JSON, nullable=True)
#     changes_summary = Column(Text, nullable=True)

#     # Request Information
#     ip_address = Column(String, nullable=True)
#     user_agent = Column(String, nullable=True)
#     request_method = Column(String, nullable=True)
#     request_path = Column(String, nullable=True)
#     request_id = Column(String, nullable=True, index=True)

#     # Impact Information
#     affected_records_count = Column(Integer, default=1)
#     related_entities = Column(JSON, nullable=True)

#     # Additional Context
#     description = Column(Text, nullable=True)
#     tags = Column(JSON, nullable=True)
#     is_critical = Column(Boolean, default=False)

#     # Original Timestamp
#     created_at = Column(DateTime, index=True)
    
#     # Archive Metadata
#     archived_at = Column(DateTime, default=datetime.utcnow, index=True)
#     original_audit_id = Column(String, nullable=True, index=True)  # Reference to original audit_log.audit_id

#     def __repr__(self):
#         return (
#             f"<AuditLogArchive(archive_id='{self.archive_id}', entity_type='{self.entity_type}', "
#             f"operation_type='{self.operation_type}', created_at='{self.created_at}')>"
#         )


# # Indexes for Performance Optimization
# __table_args__ = (
#     Index('idx_audit_log_user_created', 'user_id', 'created_at'),
#     Index('idx_audit_log_entity_created', 'entity_type', 'entity_id', 'created_at'),
#     Index('idx_audit_log_operation_created', 'operation_type', 'created_at'),
#     Index('idx_audit_log_critical_review', 'is_critical', 'requires_review', 'created_at'),
#     Index('idx_audit_log_search', 'user_id', 'entity_type', 'operation_type', 'created_at'),
# )

