from sqlalchemy.orm import relationship
from app.config.database import Base
from sqlalchemy import Column, Integer, Boolean, String, DateTime, select, ForeignKey
from datetime import datetime


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    address_line_1 = Column(String, nullable=False)
    address_line_2 = Column(String)
    city = Column(String, nullable=False)
    province = Column(String, nullable=False)   # e.g., ON, BC, QC
    country = Column(String, nullable=False, default="Canada")
    postal_code = Column(String, nullable=False)  # A1A 1A1
    is_deleted = Column(Boolean, default = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow)

    admin = relationship(
        "AdminModel",
        back_populates="address",
        primaryjoin="foreign(Address.user_id) == AdminModel.admin_id",
    )

    investor = relationship(
        "Investors",
        back_populates="address",
        primaryjoin="foreign(Address.user_id) == Investors.investor_id",
        overlaps="admin,investor_assistant,fund_assistant",
        viewonly=True,
    )

    investor_assistant = relationship(
        "InvestorAssistant",
        back_populates="address",
        primaryjoin="foreign(Address.user_id) == InvestorAssistant.investor_assistant_id",
        overlaps="admin,investor,fund_assistant",
        viewonly=True,
    )

    fund_assistant = relationship(
        "FundAssistant",
        back_populates="address",
        primaryjoin="foreign(Address.user_id) == FundAssistant.fund_assist_id",
        overlaps="admin,investor,investor_assistant",
        viewonly=True,
    )




