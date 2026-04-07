from sqlalchemy.orm import relationship, selectinload, joinedload
from app.config.database import Base
from sqlalchemy import Column, Integer, Numeric, String, DateTime, Boolean, select, ForeignKey, extract, func
from datetime import datetime, date
from decimal import Decimal


class Property(Base):
    __tablename__ = "property"

    property_id = Column(String, primary_key=True, index=True)

    added_by = Column(String, ForeignKey("fund_assistant.user_id", ondelete="CASCADE"))
    updated_by = Column(String, ForeignKey("fund_assistant.user_id"), nullable=True)

    name = Column(String, nullable=False)
    description = Column(String)

    # risk_status = Column(String, nullable=False)  # low / medium / high

    purchase_price = Column(Numeric(14, 2), nullable=False)
    # closing_cost = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    loan_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    going_cap_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    # cap_rate_flactuation = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))

    property_type = Column(String, nullable=False)
    total_area = Column(Numeric(14, 3), nullable=False, default=Decimal("0.000"))

    total_investment_required = Column(Numeric(14, 2), nullable=False)
    available_required_for_investment = Column(Numeric(14, 2), nullable=False)

    # Pro-forma start date for 10-year projections (e.g., 2025-06-01)
    # pro_forma_start_date = Column(DateTime, nullable=True)

    # gp_equity_stake = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    # hurdle = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    # go_promote_at_hurdle = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    # go_promote_above_hurdle = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    property_sheet = Column(String, nullable = True)
    property_image = Column(String, nullable = True)
    #  addresses fileds
    address_line_1 = Column(String, nullable=False)
    address_line_2 = Column(String, nullable = True)
    city = Column(String, nullable=False)
    province = Column(String, nullable=False)   # e.g., ON, BC, QC
    country = Column(String, nullable=False, default="Canada")
    postal_code = Column(String, nullable=False)  # A1A 1A1

    is_approved = Column(Boolean, default=False)
    is_open_for_investment = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    units = relationship("PropertyUnit", back_populates="property", cascade="all, delete-orphan")
    unit_types = relationship("PropertyUnitType", back_populates="property", cascade="all, delete-orphan")
    loans = relationship("PropertyLoan", back_populates="property", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="property", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="property", cascade="all, delete-orphan")
    # amortizations = relationship("AmortizationSchedule", back_populates="property", cascade="all, delete-orphan")
    investments = relationship("InvestorInvestments", back_populates="property", cascade="all, delete-orphan")


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

    async def get_by_id(db, property_id):
        stmt = (select(Property).where(Property.property_id == property_id, Property.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_info_related_rent(db, property_id: str):
        
        result = await db.execute(
            select(Property)
            .where(
                Property.property_id == property_id,
                Property.is_deleted == False
            )
            .options(
                selectinload(Property.units),
                selectinload(Property.unit_types)
            )
        )

        property_obj = result.scalars().first()

        return property_obj



class PropertyUnitType(Base):
    __tablename__ = "property_unit_type"

    id = Column(Integer, primary_key=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"))

    name = Column(String, nullable=False)  # 1BHK / 2BHK / Office / Shop
    unit_type = Column(String, nullable=False)  # residential / commercial

    total_units =  Column(Integer, nullable=False, default = 0 )
    # occupied_units = Column(Integer, nullable = False, default = 0)

    max_rent_per_unit = Column(Numeric(12, 3), nullable=False)
    min_rent_per_unit = Column(Numeric(12, 3), nullable=False)

    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="unit_types")
    units = relationship("PropertyUnit", back_populates="unit_type")

    # incomes = relationship("Income", back_populates="income_type")


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
        stmt = (select(PropertyUnitType).where(PropertyUnitType.id == id, PropertyUnitType.property_id == property_id, PropertyUnitType.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class PropertyUnit(Base):
    __tablename__ = "property_unit"

    unit_id = Column(String, primary_key=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"))
    unit_type_id = Column(Integer, ForeignKey("property_unit_type.id", ondelete="CASCADE"))

    area_sqft = Column(Numeric(14, 3), nullable=False)
    # Unit status: 'Active', 'Vacant', 'Inactive'
    unit_status = Column(String, nullable = False, default = "Vacant")
    
    market_lease_rent = Column(Numeric(12, 2), nullable=True, default=Decimal("0.00"))
    actual_lease_rent = Column(Numeric(12, 2), nullable=True, default=Decimal("0.00"))
    
    lease_start_date = Column(DateTime, nullable=True)
    lease_end_date = Column(DateTime, nullable=True)
    
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="units")
    unit_type = relationship("PropertyUnitType", back_populates="units")
    # leases = relationship("PropertyUnitLease", back_populates="unit", cascade="all, delete-orphan")

    async def get_by_id(db, unit_id, unit_type_id, property_id):
        stmt = (select(PropertyUnit).where(PropertyUnit.unit_id == unit_id, PropertyUnit.unit_type_id == unit_type_id, PropertyUnit.property_id == property_id, PropertyUnit.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

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
    
    async def get_all_available_by_ids(db, property_id, unit_type_id):
        stmt = (select(func.count(PropertyUnit.unit_id)).where(PropertyUnit.unit_type_id == unit_type_id, PropertyUnit.property_id == property_id, PropertyUnit.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar() 




class PropertyLoan(Base):
    __tablename__ = "property_loan"

    loan_id = Column(String, primary_key=True, index=True)
    property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), index=True)

    started_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    total_loan_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    interest_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    spread_intrest_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))

    # stabilized_cap_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    ltv = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))

    origination_fee = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    
    amortization_period = Column(Integer, nullable=False)
    term = Column(Integer, nullable=False)
    no_of_payments = Column(Integer, nullable=False)

    # intrest_only_period = Column(Integer, nullable=False)
    
    monthly_payments = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_annual_payment = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    is_active = Column(Boolean, default = True, nullable = False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    property = relationship("Property", back_populates="loans")
    # amortization_schedule = relationship(
    #     "AmortizationSchedule",
    #     back_populates="loan",
    #     cascade="all, delete-orphan"
    # )


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

    async def get_by_id(db, loan_id, property_id):
        stmt = (select(PropertyLoan).where(PropertyLoan.loan_id == loan_id, PropertyLoan.property_id == property_id, PropertyLoan.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_property_id(db, property_id):
        stmt = (select(PropertyLoan).where(PropertyLoan.property_id == property_id, PropertyLoan.is_deleted.is_(False)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_property_by_id(db, loan_id, property_id):
        stmt = (
            select(PropertyLoan)
            .options(joinedload(PropertyLoan.property)) 
            .where(
                PropertyLoan.loan_id == loan_id,
                PropertyLoan.property_id == property_id,
                PropertyLoan.is_active.is_(True), 
                PropertyLoan.is_deleted.is_(False)
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    

