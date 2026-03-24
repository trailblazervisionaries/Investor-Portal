from sqlalchemy.orm import relationship, joinedload
from app.config.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, select, ForeignKey
from datetime import datetime

class AdminModel(Base):
    __tablename__ = "admin"

    admin_id = Column(String, primary_key = True, index = True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete = "CASCADE"), nullable = False, index = True,)
    sirname = Column(String, nullable = True)
    fname = Column(String, nullable = False)
    mname = Column(String, nullable = True)
    lname = Column(String, nullable = True)
    email = Column(String, nullable = False, unique = True, index = True)
    phone = Column(String, nullable = False)
    role = Column(String, nullable = False, default = "admin")
    profile_image = Column(String, nullable = True)
    is_active = Column(Boolean, default = True)
    is_deleted = Column(Boolean, default = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, nullable = True, onupdate = datetime.utcnow)

    user = relationship("Users", back_populates="admin")

    address = relationship(
        "Address",
        back_populates="admin",
        uselist=False,
        primaryjoin="AdminModel.admin_id == foreign(Address.user_id)",
    )

    @staticmethod
    async def get_by_user_id(db, user_id: str):
        stmt = (
            select(AdminModel)
            .options(joinedload(AdminModel.address))
            .where(
                AdminModel.user_id == user_id,
                AdminModel.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    
    @staticmethod
    async def get_by_email(db, email: str):
        stmt = (
            select(AdminModel)
            .options(joinedload(AdminModel.address))
            .where(
                AdminModel.email == email,
                AdminModel.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin
    
    @staticmethod
    async def by_email(db, email):
        stmt = (select(AdminModel).where(AdminModel.email == email))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db, user_id):
        stmt = (select(AdminModel).where(AdminModel.user_id == user_id, AdminModel.is_deleted == False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_admin_user_id(db, user_id: str):
        stmt = (
            select(AdminModel)
            .options(
                joinedload(AdminModel.address),
                joinedload(AdminModel.user)
            )
            .where(
                AdminModel.user_id == user_id,
                AdminModel.is_deleted == False
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()