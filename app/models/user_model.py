from sqlalchemy.orm import relationship
from app.config.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select
from datetime import datetime, timedelta

class Users(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key = True, index = True)
    # name = Column(String, nullable = False)
    role = Column(String, nullable = False)
    email = Column(String, nullable = False, unique = True, index = True)
    password = Column(String, nullable = False)
    is_deleted = Column(Boolean, default = False)
    is_active = Column(Boolean, default = True)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    admin = relationship(
        "AdminModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    investor = relationship(
        "Investors",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    investor_assistant = relationship(
        "InvestorAssistant",
        back_populates="user",
        uselist=False
    )

    fund_assistant = relationship(
        "FundAssistant",
        back_populates="user",
        uselist=False
    )


    async def get_by_email(db, email):
        stmt = select(Users).where(Users.email == email, Users.is_deleted == False, Users.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id(db, user_id):
        stmt = select(Users).where(Users.user_id == user_id, Users.is_deleted == False, Users.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
   
    
    async def by_email(db, email):
        stmt = (select(Users).where(Users.email == email))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    



class OtpModel(Base):
    __tablename__ = "otp_table"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    otp_code = Column(String, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)



    async def get_by_email(db, email):
        stmt = select(OtpModel).where(
        OtpModel.email == email,
        OtpModel.is_used.is_(False),
        )
        result = await db.execute(stmt)
        otp_data = result.scalar_one_or_none()
        return otp_data
    
    async def by_email(db, email):
        stmt = select(OtpModel).where(
        OtpModel.email == email,
        )
        result = await db.execute(stmt)
        otp_data = result.scalar_one_or_none()
        return otp_data




class UploadedDocument(Base):
    __tablename__ = "uploaded_docs"
    id = Column(Integer, primary_key=True)
    file_type_name = Column(String, nullable = False)
    file_url = Column(String, nullable = False)
    added_by = Column(String, nullable = False)
    added_for = Column(String, nullable = False)
    created_at = Column(DateTime, default=datetime.utcnow)


    async def get_by_uploaded_for(db, added_for_id):
        stmt = (select(UploadedDocument).where(UploadedDocument.added_for == added_for_id))
        result = db.execute(stmt)
        return db.scalars().all()