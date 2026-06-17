from sqlalchemy.orm import relationship
from app.config.database import Base
from sqlalchemy import Column, Integer, String, DateTime, JSON, select, desc, func, and_, distinct, delete
from datetime import datetime, date, time
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException


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
    

    @staticmethod
    async def get_all_logs_by_date_range_and_added_by(
        db, 
        user_id: str,
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
        if user_id:
            filters.append(AuditModel.added_by == user_id)

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        
        return result.scalars().all(), total_res.scalar() or 0

    async def get_all_unique_audit_types(db):
        """
        Fetches all distinct audit_type values from the auditmodel table.
        """
        try:
            query = select(distinct(AuditModel.audit_type))
            result = await db.execute(query)
            unique_types = result.scalars().all()
            
            return unique_types

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=500, 
                detail="Database error while retrieving unique audit types."
            )


    @staticmethod
    async def delete_audit_records_by_date(db, start_date: date | None, end_date: date) -> int:
        try:
            end_datetime = datetime.combine(end_date, time.max)
        
            query = delete(AuditModel).where(AuditModel.created_at <= end_datetime)
            if start_date:
                start_datetime = datetime.combine(start_date, time.min)
                query = query.where(AuditModel.created_at >= start_datetime)
            
            result = await db.execute(query)
            await db.commit()
            deleted_rows = result.rowcount
            return deleted_rows

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, 
                detail="Database error while executing audit logs cleanup."
            )
        
        