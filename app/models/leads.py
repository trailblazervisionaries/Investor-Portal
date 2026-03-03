from sqlalchemy.orm import relationship
from app.config.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select, ForeignKey, desc, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

class Leads(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False)
    email = Column(String, nullable = False)
    description = Column(String, nullable = True)
    phone = Column(String, nullable = True)
    assisted_by = Column(String, nullable = True)
    status = Column(String, nullable = False, default = "pending")  # pending, stage1, stage2, stage3, onboard or decline
    updated_by = Column(String, nullable = True)
    is_deleted = Column(Boolean, default = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    remarks = relationship(
        "LeadRemark",
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by=lambda: desc(LeadRemark.created_at)
    )


    async def get_all_leads(db):
        stmt = (
            select(Leads)
            .options(selectinload(Leads.remarks))
            .where(
                Leads.is_deleted.is_(False),
                Leads.status != "onboard"
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    

    async def get_all_leads_by_attendend_id_and_status(db, user_id, status):
        stmt = (
            select(Leads)
            .options(selectinload(Leads.remarks))
            .where(
                Leads.is_deleted.is_(False),
                Leads.status == status,
                or_(
                    Leads.updated_by == user_id,
                    Leads.assisted_by == user_id,
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
        
    async def get_all_leads_by_status(db, status):
        stmt = (
            select(Leads)
            .options(selectinload(Leads.remarks))
            .where(
                Leads.is_deleted.is_(False),
                Leads.status == status
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

        
    async def get_lead_by_id(db, id):
        stmt = (
            select(Leads)
            # .options(selectinload(Leads.remarks))
            .where(Leads.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    @staticmethod
    async def get_leads_by_status_and_date_range(
        db,
        status: str,
        start_date: datetime,
        end_date: datetime,
    ):
        end_date = end_date + timedelta(days=1)
        stmt = (
            select(Leads)
            .options(selectinload(Leads.remarks))
            .where(
                Leads.is_deleted.is_(False),
                Leads.status == status,
                Leads.created_at >= start_date,
                Leads.created_at < end_date,
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()





class LeadRemark(Base):
    __tablename__ = "lead_remarks"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"))

    remark = Column(String, nullable=False)

    created_by = Column(String, nullable=False)  # assisted_by / updated_by
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Leads", back_populates="remarks")




