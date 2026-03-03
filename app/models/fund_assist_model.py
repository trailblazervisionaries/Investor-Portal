from sqlalchemy.orm import relationship, joinedload
from app.config.database import Base
from sqlalchemy import Column, Integer, Numeric, String, DateTime, Boolean, select, ForeignKey
from datetime import datetime


class FundAssistant(Base):
    __tablename__ = "fund_assistant"

    fund_assist_id = Column(String, unique = True, index = True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete = "CASCADE"), nullable = False, index = True, primary_key=True)
    sirname = Column(String, nullable = True)
    fname = Column(String, nullable = False)
    mname = Column(String, nullable = True)
    lname = Column(String, nullable = True)
    email = Column(String, nullable = False, unique = True, index = True)
    phone = Column(String, nullable = False)
    role = Column(String, nullable = False, default = "fund-assistant")
    profile_image = Column(String, nullable = True)
    is_active = Column(Boolean, default = True)
    is_deleted = Column(Boolean, default = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    user = relationship("Users", back_populates="fund_assistant")
    
    address = relationship(
        "Address",
        back_populates="fund_assistant",
        uselist=False,
        primaryjoin="FundAssistant.fund_assist_id == foreign(Address.user_id)",
        overlaps="address",
        viewonly=True,
    )


    @staticmethod
    async def get_by_user_id(db, user_id: str):
        stmt = (
            select(FundAssistant)
            .options(joinedload(FundAssistant.address))
            .where(
                FundAssistant.user_id == user_id,
                FundAssistant.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    
    @staticmethod
    async def get_by_email(db, email: str):
        stmt = (
            select(FundAssistant)
            .options(joinedload(FundAssistant.address))
            .where(
                FundAssistant.email == email,
                FundAssistant.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    
    @staticmethod
    async def by_email(db, email):
        stmt = (select(FundAssistant).where(FundAssistant.email == email))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_fund_assist_user_id(db, user_id: str):
        stmt = (
            select(FundAssistant)
            .options(
                joinedload(FundAssistant.address),
                joinedload(FundAssistant.user)
            )
            .where(
                FundAssistant.user_id == user_id,
                FundAssistant.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()











