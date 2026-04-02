from sqlalchemy.orm import relationship, joinedload
from app.config.database import Base
from sqlalchemy import Column, Integer, Numeric, String, DateTime, Boolean, select, ForeignKey, UniqueConstraint, CheckConstraint
from datetime import datetime, date
from decimal import Decimal


class ExpenseTypes(Base):
    __tablename__ = "expense_type"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default = False, nullable = False)
    expenses = relationship("Expense", back_populates="expense_type")

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

    async def get_by_id(db, id, property_id):
        stmt = (select(ExpenseTypes).where(ExpenseTypes.id == id, ExpenseTypes.property_id == property_id, ExpenseTypes.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    
    async def get_by_name(db, name, property_id):
        stmt = (select(ExpenseTypes).where(ExpenseTypes.name == name, ExpenseTypes.property_id == property_id, ExpenseTypes.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_expense_types(db, property_id):
        stmt = (select(ExpenseTypes).where(ExpenseTypes.property_id == property_id, ExpenseTypes.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalars().all()
    

    async def get_property_expense_details(db, property_id: str):
        stmt = (
            select(ExpenseTypes)
            .options(
                joinedload(ExpenseTypes.expenses)
                .joinedload(Expense.expense_growth_rates)
            )
            .where(
                ExpenseTypes.property_id == property_id,
                ExpenseTypes.is_deleted.is_(False)
            )
        )

        result = await db.execute(stmt)
        expense_types = result.scalars().unique().all()

        response = []

        for expense_type in expense_types:
            expense_list = []

            for expense in expense_type.expenses:
                if expense.is_deleted:
                    continue

                growth_list = [
                    {
                        "id": growth.id,
                        "year": growth.year,
                        "growth_percentage": float(growth.growth_percentage),
                        "created_at": growth.created_at,
                        "updated_at": growth.updated_at
                    }
                    for growth in expense.expense_growth_rates
                    if not growth.is_deleted
                ]

                expense_list.append({
                    "expense_id": expense.expense_id,
                    "current_expense": float(expense.current_expense),
                    "created_at": expense.created_at,
                    "updated_at": expense.updated_at,
                    "expense_growth": growth_list
                })

            response.append({
                "expense_type_id": expense_type.id,
                "expense_type_name": expense_type.name,
                "expenses": expense_list
            })

        return response





class Expense(Base):
    __tablename__ = "expense"

    expense_id = Column(String, primary_key=True, index=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), nullable=False, index=True)
    expense_type_id = Column(Integer, ForeignKey("expense_type.id"), nullable=False, index=True)

    current_expense = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    # pro_forma_expense = Column( Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    is_deleted = Column(Boolean, nullable = False, default = False)

    property = relationship("Property", back_populates="expenses")
    expense_type = relationship("ExpenseTypes", back_populates="expenses")

    expense_growth_rates = relationship(
        "ExpenseGrowth",
        back_populates="expense",
        cascade="all, delete-orphan"
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

    async def get_expense_data_by_property_id_and_expense_type_id(db, type_id, property_id):
        stmt = (select(Expense).where(Expense.property_id == property_id, Expense.expense_type_id == type_id, Expense.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_expense_data_by_property_id(db, property_id):
        stmt = select(Expense).options(joinedload(Expense.expense_type)).where(
            Expense.property_id == property_id,
            Expense.is_deleted.is_(False)
        )
        result = await db.execute(stmt)
        expenses = result.scalars().all()
        for exp in expenses:
            if exp.expense_type:
                exp.name = exp.expense_type.name
        return expenses

    

    async def get_by_id(db, expense_id, type_id, property_id):
        stmt = (select(Expense).where(Expense.expense_id == expense_id, Expense.expense_type_id == type_id, Expense.property_id == property_id, Expense.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()





class ExpenseGrowth(Base):
    __tablename__ = "expense_growth"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(String, ForeignKey("expense.expense_id", ondelete="CASCADE"), nullable=False, index=True)

    year = Column(Integer, nullable=False)  # 1,2,3,...,10 (max 10 years)
    growth_percentage = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    is_deleted = Column(Boolean, nullable=False, default=False)

    expense = relationship(
        "Expense",
        back_populates="expense_growth_rates"
    )
    
    # Ensure unique year per expense (no duplicate years)
    __table_args__ = (
        UniqueConstraint('expense_id', 'year', name='uq_expense_year'),
        CheckConstraint('year >= 1 AND year <= 11', name='ck_expense_year_range'),
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


    async def get_by_id(db, id, expense_id):
        stmt = (select(ExpenseGrowth).where(ExpenseGrowth.id == id, ExpenseGrowth.expense_id == expense_id, ExpenseGrowth.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_all_expense_growth(db, expense_id):
        stmt = (select(ExpenseGrowth).where(
            ExpenseGrowth.expense_id == expense_id,
            ExpenseGrowth.is_deleted.is_(False)
            ).order_by(ExpenseGrowth.id.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()





