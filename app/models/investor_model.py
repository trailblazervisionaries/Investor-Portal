from sqlalchemy.orm import relationship, joinedload
from app.config.database import Base
from sqlalchemy import Column, Integer, Numeric, String, DateTime, Boolean, select, ForeignKey, func
from app.models.investor_assist_model import InvestorAssignments
from datetime import datetime, date
from decimal import Decimal

class Investors(Base):
    __tablename__ = "investor"

    investor_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True,unique=True)
    added_by = Column(String, nullable = False)
    sirname = Column(String)
    fname = Column(String, nullable=False)
    mname = Column(String)
    lname = Column(String)

    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=False)

    role = Column(String, nullable = False, default = "investor")
    profile_image = Column(String)

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    user = relationship("Users", back_populates="investor")

    address = relationship(
        "Address",
        back_populates="investor",
        uselist=False,
        primaryjoin="Investors.investor_id == foreign(Address.user_id)",
        overlaps="address,admin,investor_assistant,fund_assistant",
        viewonly=True,
        lazy="selectin"
    )

    investments = relationship(
        "InvestorInvestments",
        back_populates="investor",
        cascade="all, delete-orphan"
    )

    assistant_assignment = relationship(
        "InvestorAssignments",
        back_populates="investor",
        lazy="selectin"
    )

    def model_to_dict(obj):
        data = {}
        for c in obj.__table__.columns:
            value = getattr(obj, c.name)
            
            if isinstance(value, (datetime, date)):
                data[c.name] = value.isoformat()
                
            elif isinstance(value, Decimal):
                data[c.name] = float(value) 
                
            else:
                data[c.name] = value
                
        return data
    

    @staticmethod
    async def get_by_user_id(db, user_id: str):
        stmt = (
            select(Investors)
            .options(joinedload(Investors.address))
            .where(
                Investors.user_id == user_id,
                Investors.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    
    @staticmethod
    async def get_by_email(db, email: str):
        stmt = (
            select(Investors)
            .options(joinedload(Investors.address))
            .where(
                Investors.email == email,
                Investors.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    

    @staticmethod
    async def by_email(db, email):
        stmt = (select(Investors).where(Investors.email == email))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_id(db, user_id):
        stmt = (select(Investors).where(Investors.user_id == user_id, Investors.is_deleted == False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_investor_id(db, investor_id):
        stmt = (select(Investors).where(Investors.investor_id == investor_id, Investors.is_deleted == False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_investor_user_id(db, user_id: str):
        stmt = (
            select(Investors)
            .options(
                joinedload(Investors.address),
                joinedload(Investors.user)
            )
            .where(
                Investors.user_id == user_id,
                Investors.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    

    @staticmethod
    async def get_by_added_by_id(db, id: str):
        stmt = (
            select(Investors)
            .options(
                joinedload(Investors.address),
                joinedload(Investors.user)
            )
            .where(
                # Investors.added_by == id,
                Investors.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        return result.scalars().all()


    # @staticmethod
    # async def get_all_info_investors(db, skip: int = 0, limit: int = 10, deleted: bool = False):
    #     stmt = (
    #         select(Investors)
    #         .options(joinedload(Investors.address), joinedload(Investors.user))
    #         .where(Investors.is_deleted == deleted)
    #         .offset(skip)
    #         .limit(limit)
    #     )
        
    #     count_stmt = (
    #         select(func.count())
    #         .select_from(Investors)
    #         .where(Investors.is_deleted == deleted)
    #     )

    #     result = await db.execute(stmt)
    #     total_res = await db.execute(count_stmt)
        
    #     return result.scalars().all(), total_res.scalar() or 0


    @staticmethod
    async def get_all_info_investors(db, skip: int = 0, limit: int = 10, deleted: bool = False):
        stmt = (
            select(Investors)
            .options(
                joinedload(Investors.address), 
                joinedload(Investors.user),
                joinedload(Investors.assistant_assignment).options(
                    joinedload(InvestorAssignments.investor_assistant)
                )
            )
            .where(Investors.is_deleted == deleted)
            .offset(skip)
            .limit(limit)
        )
        
        count_stmt = (
            select(func.count())
            .select_from(Investors)
            .where(Investors.is_deleted == deleted)
        )

        result = await db.execute(stmt)
        total_res = await db.execute(count_stmt)
        
        # Using unique() is recommended when using joinedload on collections 
        # to avoid duplicate parent rows in the result set.
        return result.scalars().unique().all(), total_res.scalar() or 0




class InvestorInvestments(Base):
    __tablename__ = "investor_investments"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(String, ForeignKey("investor.investor_id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), nullable=False, index=True)

    invested_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    status = Column(String)  # ACTIVE / PARTIAL / SOLD

    invested_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # units_purchased = Column(Integer, nullable = True)
    # purchase_price_per_unit = Column(Numeric(12, 2), nullable=False)

    investor = relationship("Investors", back_populates="investments")
    property = relationship("Property", back_populates="investments")

    def model_to_dict(obj):
        data = {}
        for c in obj.__table__.columns:
            value = getattr(obj, c.name)
            
            if isinstance(value, (datetime, date)):
                data[c.name] = value.isoformat()
                
            elif isinstance(value, Decimal):
                data[c.name] = float(value) 
                
            else:
                data[c.name] = value
                
        return data
    

    async def get_by_id(db, id, investor_id):
        stmt = (select(InvestorInvestments).where(InvestorInvestments.id == id, InvestorInvestments.investor_id == investor_id))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()







