from sqlalchemy.orm import relationship, joinedload
from app.config.database import Base
from sqlalchemy import Column, Integer, Numeric, String, DateTime, Boolean, select, ForeignKey, UniqueConstraint, CheckConstraint
from datetime import datetime
from decimal import Decimal


class IncomeType(Base):

    __tablename__ = "income_type"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default = False, nullable = False)

    incomes = relationship("Income", back_populates="income_type")


    async def get_by_id(db, id, property_id):
        stmt = (select(IncomeType).where(IncomeType.id == id, IncomeType.property_id == property_id, IncomeType.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    
    async def get_by_name(db, name, property_id):
        stmt = (select(IncomeType).where(IncomeType.name == name, IncomeType.property_id == property_id, IncomeType.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_income_types(db, property_id):
        stmt = (select(IncomeType).where(IncomeType.property_id == property_id, IncomeType.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()
    

    async def get_property_income_details(db, property_id: str):
        stmt = (
            select(IncomeType)
            .options(
                joinedload(IncomeType.incomes)
                .joinedload(Income.income_growth_rates)
            )
            .where(
                IncomeType.property_id == property_id,
                IncomeType.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        income_types = result.scalars().unique().all()

        response = []

        for income_type in income_types:
            income_list = []

            for income in income_type.incomes:
                if income.is_deleted:
                    continue

                growth_list = [
                    {
                        "id": growth.id,
                        "year": growth.year,
                        "growth_percentage": float(growth.growth_percentage),
                        "created_at": growth.created_at,
                        "updated_at": growth.update_at
                    }
                    for growth in income.income_growth_rates
                    if not growth.is_deleted
                ]

                income_list.append({
                    "income_id": income.income_id,
                    "current_income": float(income.current_income),
                    "pro_forma_income": float(income.pro_forma_income),
                    "created_at": income.created_at,
                    "updated_at": income.updated_at,
                    "income_growth": growth_list
                })

            response.append({
                "income_type_id": income_type.id,
                "income_type_name": income_type.name,
                "incomes": income_list
            })

        return response


class Income(Base):
     
    __tablename__ = "income"

    income_id = Column(String, primary_key=True, index=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), nullable=False, index=True)
    income_type_id = Column(Integer, ForeignKey("income_type.id"), nullable=False, index=True)

    current_income = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    pro_forma_income = Column( Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    is_deleted = Column(Boolean, nullable = False, default = False)

    property = relationship("Property", back_populates="incomes")
    income_type = relationship("IncomeType", back_populates="incomes")

    income_growth_rates = relationship(
        "IncomeGrowth",
        back_populates="income",
        cascade="all, delete-orphan"
    )


    async def get_income_data_by_property_id_and_income_type_id(db, type_id, property_id):
        stmt = (select(Income).where(Income.property_id == property_id, Income.income_type_id == type_id, Income.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_income_data_by_property_id(db, property_id):
        stmt = select(Income).where(
            Income.property_id == property_id,
            Income.is_deleted.is_(False)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(db, income_id, type_id, property_id):
        stmt = (select(Income).where(Income.income_id == income_id, Income.income_type_id == type_id, Income.property_id == property_id, Income.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    

class IncomeGrowth(Base):
    __tablename__ = "income_growth"

    id = Column(Integer, primary_key=True, index=True)
    income_id = Column(String, ForeignKey("income.income_id", ondelete="CASCADE"), nullable=False, index=True)

    year = Column(Integer, nullable=False)  # 1,2,3,...,10 (max 10 years)
    growth_percentage = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000")) # e.g. 0.0750 = 7.5%

    created_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    is_deleted = Column(Boolean, nullable = False, default = False)

    income = relationship("Income", back_populates="income_growth_rates")
    
    # Ensure unique year per income (no duplicate years)
    __table_args__ = (
        UniqueConstraint('income_id', 'year', name='uq_income_year'),
        CheckConstraint('year >= 1 AND year <= 11', name='ck_year_range'),
    )



    async def get_by_id(db, id, income_id):
        stmt = (select(IncomeGrowth).where(IncomeGrowth.id == id, IncomeGrowth.income_id == income_id, IncomeGrowth.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_all_income_growth(db, income_id):
        stmt = (select(IncomeGrowth).where(IncomeGrowth.income_id == income_id, IncomeGrowth.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()




