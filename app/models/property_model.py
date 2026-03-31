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

    risk_status = Column(String, nullable=False)  # low / medium / high

    purchase_price = Column(Numeric(14, 2), nullable=False)
    closing_cost = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    loan_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    market_cap_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    cap_rate_flactuation = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))

    property_type = Column(String, nullable=False)
    total_area = Column(Numeric(14, 3), nullable=False, default=Decimal("0.000"))

    total_investment_required = Column(Numeric(14, 2), nullable=False)
    available_required_for_investment = Column(Numeric(14, 2), nullable=False)

    # Pro-forma start date for 10-year projections (e.g., 2025-06-01)
    pro_forma_start_date = Column(DateTime, nullable=True)

    gp_equity_stake = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    hurdle = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    go_promote_at_hurdle = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    go_promote_above_hurdle = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    property_sheet = Column(String, nullable = True)
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
    occupied_units = Column(Integer, nullable = False, default = 0)

    # market_rent_per_unit = Column(Numeric(12, 2), nullable=False)
    # market_rent_per_sqft = Column(Numeric(12, 3), nullable=False)

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

    started_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    total_loan_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    interest_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    spread_intrest_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))

    stabilized_cap_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    ltv = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))

    origination_fee = Column(Numeric(7, 4), nullable = False, default = Decimal("0.0000"))
    
    amortization_period = Column(Integer, nullable=False)
    term = Column(Integer, nullable=False)
    no_of_payments = Column(Integer, nullable=False)

    intrest_only_period = Column(Integer, nullable=False)
    
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

    



# class AmortizationSchedule(Base):
#     __tablename__ = "amortization_schedule"

#     amortization_id = Column(String, primary_key=True, index=True)
#     property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), index=True)
#     loan_id = Column(String, ForeignKey("property_loan.loan_id", ondelete="CASCADE"), index=True)

#     year = Column(Integer, nullable=False)
#     month = Column(Integer, nullable=False)
    
#     # Specific date for this payment
#     scheduled_payment_date = Column(DateTime, nullable=True)

#     principal_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
#     payment_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))  # Renamed from PMT
#     interest = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
#     principal_paid = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
#     loan_balance = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Interest-only period flag
#     is_interest_only = Column(Boolean, default=False, nullable=False)

#     is_paid = Column(Boolean, default=False, nullable=False)
#     paid_date = Column(DateTime, nullable = True)

#     is_deleted = Column(Boolean, default=False, nullable=False)

#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, onupdate=datetime.utcnow)

#     # Relationships
#     loan = relationship("PropertyLoan", back_populates="amortization_schedule")
#     property = relationship("Property", back_populates="amortizations")



#     async def get_by_id(db, amortization_id, loan_id, property_id):
#         stmt = (select(AmortizationSchedule).where(AmortizationSchedule.amortization_id == amortization_id, 
#                                                    AmortizationSchedule.loan_id == loan_id, 
#                                                    AmortizationSchedule.property_id == property_id, AmortizationSchedule.is_deleted.is_(False)))
#         result = await db.execute(stmt)
#         return result.scalar_one_or_none()






# class PropertyUnitLease(Base):
#     __tablename__ = "property_unit_lease"

#     lease_id = Column(String, primary_key=True)
#     unit_id = Column(String, ForeignKey("property_unit.unit_id", ondelete="CASCADE"))
#     property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"))
#     tenant_name = Column(String, nullable=True)
#     tenant_phone = Column(String, nullable=True)
#     tenant_email = Column(String, nullable=True)

#     lease_start_date = Column(DateTime, nullable=False)
#     lease_end_date = Column(DateTime, nullable=False)

#     agreed_rent = Column(Numeric(12, 2), nullable=False)
    
#     # Market rent for comparison (loss-to-lease calculation)
#     market_rent = Column(Numeric(12, 2), nullable=True)
    
#     # Loss to Lease = Market Rent - Agreed Rent (positive = revenue loss)
#     loss_to_lease_amount = Column(Numeric(12, 2), nullable=True, default=Decimal("0.00"))
    
#     security_deposit = Column(Numeric(12, 2), default=Decimal("0.00"))
    
#     # Lease status: 'Active', 'Expired', 'Terminated'
#     lease_status = Column(String, default='Active', nullable=False)

#     is_active = Column(Boolean, default=True)
#     is_deleted = Column(Boolean, default=False)

#     created_at = Column(DateTime, default=datetime.utcnow)

#     unit = relationship("PropertyUnit", back_populates="leases")
#     rent_collections = relationship(
#         "PropertyUnitRentCollection",
#         back_populates="lease",
#         cascade="all, delete-orphan"
#     )


#     async def get_by_id(db, lease_id, unit_id, property_id):
#         stmt = (select(PropertyUnitLease).where(PropertyUnitLease.lease_id == lease_id, 
#                                                 PropertyUnitLease.unit_id == unit_id, PropertyUnitLease.property_id == property_id, PropertyUnitLease.is_deleted.is_(False)))
#         result = await db.execute(stmt)
#         return result.scalar_one_or_none()


# class PropertyUnitRentCollection(Base):
#     __tablename__ = "property_unit_rent_collection"

#     id = Column(Integer, primary_key=True)
#     lease_id = Column(String, ForeignKey("property_unit_lease.lease_id", ondelete="CASCADE"))
#     property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"))

#     rent_month = Column(DateTime, nullable=False)  # e.g. 2026-01-01
#     rent_amount = Column(Numeric(12, 2), nullable=False)

#     is_paid = Column(Boolean, default=False)
#     paid_on = Column(DateTime, nullable=True)

#     is_deleted = Column(Boolean, default=False)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     lease = relationship("PropertyUnitLease", back_populates="rent_collections")


#     async def get_by_id(db, id, lease_id, property_id):
#         stmt = (select(PropertyUnitRentCollection).where(PropertyUnitRentCollection.id == id, 
#                                                          PropertyUnitRentCollection.lease_id == lease_id, 
#                                                          PropertyUnitRentCollection.property_id == property_id, 
#                                                          PropertyUnitRentCollection.is_deleted.is_(False)))
#         result = await db.execute(stmt)
#         return result.scalar_one_or_none()
    

#     @staticmethod
#     async def is_rent_paid_for_month(db, lease_id: str, property_id: str, date_str: str) -> bool:
#         date_obj = datetime.strptime(date_str, "%Y-%m-%d")

#         year = date_obj.year
#         month = date_obj.month
        
#         stmt = (
#             select(PropertyUnitRentCollection.id)
#             .where(
#                 PropertyUnitRentCollection.lease_id == lease_id,
#                 PropertyUnitRentCollection.property_id == property_id,
#                 PropertyUnitRentCollection.is_paid.is_(True),
#                 PropertyUnitRentCollection.is_deleted.is_(False),
#                 extract("year", PropertyUnitRentCollection.rent_month) == year,
#                 extract("month", PropertyUnitRentCollection.rent_month) == month,
#             )
#             .limit(1)
#         )

#         result = await db.execute(stmt)
#         return result.scalar_one_or_none() is not None


# class ProFormaCalculation(Base):
#     """
#     Stores 10-year pro-forma calculations
#     One record per month × 10 years = 120 rows per property
#     """
#     __tablename__ = "pro_forma_calculation"

#     proforma_id = Column(String, primary_key=True, index=True)
#     property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), index=True)

#     # Year 1-10 and Month 1-12
#     year = Column(Integer, nullable=False)
#     month = Column(Integer, nullable=False)
    
#     # Specific date for this projection
#     date_point = Column(DateTime, nullable=False, index=True)
    
#     # Cap rate for valuation
#     market_cap_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    
#     # Calculated projections
#     projected_income = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
#     projected_expense = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Net Operating Income = Income - Expense
#     noi = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Debt Service (loan payments for all active loans)
#     debt_service = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Cash Flow = NOI - Debt Service
#     cash_flow = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Occupancy rate (%)
#     occupancy_rate = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    
#     # Loss to Lease for this period
#     loss_to_lease = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Flag if calculated
#     is_calculated = Column(Boolean, default=False, nullable=False)
    
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, onupdate=datetime.utcnow)

#     property = relationship("Property", foreign_keys=[property_id])

#     async def get_by_id(db, proforma_id, property_id):
#         stmt = (select(ProFormaCalculation).where(
#             ProFormaCalculation.proforma_id == proforma_id, 
#             ProFormaCalculation.property_id == property_id
#         ))
#         result = await db.execute(stmt)
#         return result.scalar_one_or_none()

#     async def get_10_year_projection(db, property_id):
#         """Get full 10-year monthly projection (120 rows)"""
#         stmt = (
#             select(ProFormaCalculation)
#             .where(ProFormaCalculation.property_id == property_id)
#             .order_by(ProFormaCalculation.year.asc(), ProFormaCalculation.month.asc())
#         )
#         result = await db.execute(stmt)
#         return result.scalars().all()

#     async def get_annual_summary(db, property_id, year):
#         """Get annual summary for a specific year"""
#         stmt = (
#             select(ProFormaCalculation)
#             .where(
#                 ProFormaCalculation.property_id == property_id,
#                 ProFormaCalculation.year == year
#             )
#             .order_by(ProFormaCalculation.month.asc())
#         )
#         result = await db.execute(stmt)
#         return result.scalars().all()


# class RentRollAnalysisSummary(Base):
#     """
#     Stores aggregated rent roll summary by unit type
#     Pre-calculated summaries for quick retrieval
#     """
#     __tablename__ = "rent_roll_analysis_summary"

#     summary_id = Column(String, primary_key=True, index=True)
#     property_id = Column(String, ForeignKey("property.property_id", ondelete="CASCADE"), index=True)
#     unit_type_id = Column(Integer, ForeignKey("property_unit_type.id", ondelete="CASCADE"), index=True)

#     # Calculation timestamp
#     calculation_date = Column(DateTime, default=datetime.utcnow, nullable=False)

#     # Unit counts
#     total_units = Column(Integer, nullable=False, default=0)
#     occupied_units = Column(Integer, nullable=False, default=0)
#     vacant_units = Column(Integer, nullable=False, default=0)
    
#     # Occupancy percentage (0-100)
#     occupancy_percentage = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

#     # Market rent totals (what should be collected)
#     market_rent_monthly = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
#     market_rent_annual = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

#     # Actual rent totals (what is collected)
#     actual_rent_monthly = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
#     actual_rent_annual = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))

#     # Loss to Lease (opportunity for revenue recovery)
#     loss_to_lease_total = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
#     loss_to_lease_monthly = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
#     # Loss to Lease percentage
#     loss_to_lease_percentage = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, onupdate=datetime.utcnow)

#     property = relationship("Property", foreign_keys=[property_id])
#     unit_type = relationship("PropertyUnitType", foreign_keys=[unit_type_id])

#     async def get_by_id(db, summary_id, property_id):
#         stmt = (select(RentRollAnalysisSummary).where(
#             RentRollAnalysisSummary.summary_id == summary_id,
#             RentRollAnalysisSummary.property_id == property_id
#         ))
#         result = await db.execute(stmt)
#         return result.scalar_one_or_none()

#     async def get_property_summary(db, property_id):
#         """Get latest rent roll summary for all unit types"""
#         stmt = (
#             select(RentRollAnalysisSummary)
#             .where(RentRollAnalysisSummary.property_id == property_id)
#             .order_by(RentRollAnalysisSummary.calculation_date.desc())
#         )
#         result = await db.execute(stmt)
#         return result.scalars().all()

#     async def get_summaries_by_unit_type(db, property_id, unit_type_id):
#         """Get summaries for specific unit type"""
#         stmt = (
#             select(RentRollAnalysisSummary)
#             .where(
#                 RentRollAnalysisSummary.property_id == property_id,
#                 RentRollAnalysisSummary.unit_type_id == unit_type_id
#             )
#             .order_by(RentRollAnalysisSummary.calculation_date.desc())
#             .limit(1)
#         )
#         result = await db.execute(stmt)
#         return result.scalar_one_or_none()





