from sqlalchemy.orm import relationship, joinedload
from app.config.database import Base
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Column, Integer, String, DateTime, Boolean, select, ForeignKey
from datetime import datetime


class InvestorAssistant(Base):
    __tablename__ = "investor_assistant"

    investor_assistant_id = Column(String, primary_key=True, index=True)

    user_id = Column(
        String,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    sirname = Column(String)
    fname = Column(String, nullable=False)
    mname = Column(String)
    lname = Column(String)

    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=False)

    role = Column(String, nullable = False, default = "investor-assistant")
    profile_image = Column(String)

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    user = relationship("Users", back_populates="investor_assistant")

    address = relationship(
        "Address",
        back_populates="investor_assistant",
        uselist=False,
        primaryjoin="InvestorAssistant.investor_assistant_id == foreign(Address.user_id)",
        overlaps="address",
        viewonly=True,
    )

    assigned_investors = relationship(
        "InvestorAssignments",
        back_populates="investor_assistant",
        cascade="all, delete-orphan"
    )

    
    @staticmethod
    async def get_by_user_id(db, user_id: str):
        stmt = (
            select(InvestorAssistant)
            .options(joinedload(InvestorAssistant.address))
            .where(
                InvestorAssistant.user_id == user_id,
                InvestorAssistant.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    
    @staticmethod
    async def get_by_email(db, email: str):
        stmt = (
            select(InvestorAssistant)
            .options(joinedload(InvestorAssistant.address))
            .where(
                InvestorAssistant.email == email,
                InvestorAssistant.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    

    @staticmethod
    async def by_email(db, email):
        stmt = (select(InvestorAssistant).where(InvestorAssistant.email == email))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_investor_assistant_user_id(db, user_id: str):
        stmt = (
            select(InvestorAssistant)
            .options(
                joinedload(InvestorAssistant.address),
                joinedload(InvestorAssistant.user)
            )
            .where(
                InvestorAssistant.user_id == user_id,
                InvestorAssistant.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()





class InvestorAssignments(Base):
    __tablename__ = "investor_assignments"

    id = Column(Integer, primary_key=True, index=True)

    investor_id = Column(
        String,
        ForeignKey("investor.investor_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    investor_assistant_id = Column(
        String,
        ForeignKey("investor_assistant.investor_assistant_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    is_deleted = Column(Boolean, default=False, nullable=False)

    assigned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    investor = relationship("Investors", back_populates="assistant_assignment")
    investor_assistant = relationship("InvestorAssistant", back_populates="assigned_investors")


    @staticmethod
    async def get_all_assignment_data_by_investor_id(db, investor_id: str):
        stmt = (
            select(InvestorAssignments)
            .options(
                joinedload(InvestorAssignments.investor_assistant)
            )
            .where(
                InvestorAssignments.investor_id == investor_id,
            )
        )

        result = await db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def get_all_assignment_data_by_investor_assistant_id(db, investor_assistant_id: str):
        stmt = (
            select(InvestorAssignments)
            .options(
                joinedload(InvestorAssignments.investor)
            )
            .where(
                InvestorAssignments.investor_assistant_id == investor_assistant_id,
            )
        )

        result = await db.execute(stmt)
        return result.scalars().first()
    
    
    @staticmethod
    async def get_active_assignment_by_investor(db, investor_id: str, investor_assistant_id: str):
        stmt = (
            select(InvestorAssignments)
            .options(
                joinedload(InvestorAssignments.investor_assistant)
            )
            .where(
                InvestorAssignments.investor_id == investor_id,
                InvestorAssignments.investor_assistant_id == investor_assistant_id,
                InvestorAssignments.is_deleted.is_(False)
            )
        )

        result = await db.execute(stmt)
        return result.scalars().first()
    

    @staticmethod
    async def get_active_assign_assist_by_investor_id(db, investor_id: str):
        stmt = (
            select(InvestorAssignments)
            .options(
                joinedload(InvestorAssignments.investor_assistant)
            )
            .where(
                InvestorAssignments.investor_id == investor_id,
                InvestorAssignments.is_deleted.is_(False)
            )
        )

        result = await db.execute(stmt)
        return result.scalars().first()


    @staticmethod
    async def get_active_assign_investor_by_investor_assistant_id(db, investor_assistant_id: str):
        stmt = (
            select(InvestorAssignments)
            .options(
                joinedload(InvestorAssignments.investor)
            )
            .where(
                InvestorAssignments.investor_assistant_id == investor_assistant_id,
                InvestorAssignments.is_deleted.is_(False)
            )
        )

        result = await db.execute(stmt)
        return result.scalars().first()
    


