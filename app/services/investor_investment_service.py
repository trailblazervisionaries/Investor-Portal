from fastapi import Request, Response, HTTPException, status
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, desc, case
from dotenv import load_dotenv
from app.models.investor_model import Investors, InvestorInvestments
from app.models.property_model import Property
from app.templates.send_template_mail import MailTemplatesService
from app.backgroundTasks.MonitorAsync import MonitorAsync
from app.models.audit_model import AuditModel
from decimal import Decimal
import traceback
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class InvestorInvestmentServices:

    async def add_new_investment(db, investor_id, data, user_id):
        property = await Property.get_by_id(db, data.property_id)
        if not property:
            raise HTTPException(404, "Property not found for the investment")

        amount: Decimal = data.invested_amount

        if property.available_required_for_investment < amount:
            raise HTTPException(
                400,
                "Insufficient available amount for this investment"
            )

        new_investment = InvestorInvestments(
            investor_id=investor_id,  
            property_id=data.property_id,
            invested_amount=amount,
            status=data.status or "activate",
        )

        db.add(new_investment)

        property.available_required_for_investment -= amount

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data,
            old_data = None,
            audit_type = "ADD",
            entity_type = "Investor Investment Management",
            object_id = new_investment.id
        )
    
        logger.info("ExpenseTypeService: Audit log recorded for new investor investment.")

        await db.commit()
        await db.refresh(new_investment)

        logger.info(
            f"InvestorInvestmentServices: New investment added successfully "
            f"(Investor={investor_id}, Property={data.property_id}, Amount={amount})"
        )

        return new_investment
    
    
    async def update_investment(db, id, investor_id, data, user_id):
        investment = await InvestorInvestments.get_by_id(db, id, investor_id)
        if not investment:
            raise HTTPException(
                404,
                "InvestorInvestmentServices: investment not found using provided id and investor_id"
            )
        old_data = InvestorInvestments.model_to_dict(investment)
        property = await Property.get_by_id(db, data.property_id or investment.property_id)
        if not property:
            raise HTTPException(404, "Property not found for the investment")


        if data.invested_amount is not None:
            old_amount: Decimal = investment.invested_amount
            new_amount: Decimal = data.invested_amount

            delta = new_amount - old_amount

            # Check availability only if increasing investment
            if delta > 0 and property.available_required_for_investment < delta:
                raise HTTPException(
                    400,
                    "Not enough available amount in property for additional investment"
                )

            property.available_required_for_investment -= delta

            investment.invested_amount = new_amount

        if data.property_id is not None and data.property_id != investment.property_id:
            investment.property_id = data.property_id

        if data.status is not None:
            investment.status = data.status

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = data,
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Investor Investment Management",
            object_id = investment.id
        )
    
        logger.info("ExpenseTypeService: Audit log recorded for this update.")
        await db.commit()
        await db.refresh(investment)

        logger.info(
            f"InvestorInvestmentServices: Investment {investment.id} updated successfully"
        )

        return investment
    

    async def update_the_investment_status(db, id, investor_id, status, user_id):
        investment = await InvestorInvestments.get_by_id(db, id, investor_id)
        if not investment:
            raise HTTPException(500, "InvestorInvestmentServices: investment not found using provided id, investor_id")
        old_data = InvestorInvestments.model_to_dict(investment)
        investment.status = status

        audit_log = await AuditModel.add_new_logs(
            db = db,
            added_by = user_id,
            new_data = {"status": status},
            old_data = old_data,
            audit_type = "UPDATE",
            entity_type = "Investor Investment Management",
            object_id = investment.id
        )
   
        logger.info("ExpenseTypeService: Audit log recorded for this status update.")
        await db.commit()
        await db.refresh(investment)
        return {
            "message": f"InvestorInvestmentServices: status updated for the id: {id}, and investor_id: {investor_id} now the updated status is {investment.status}. "
        }
    

    async def get_the_investment_info(db, id, investor_id):
        investment = await InvestorInvestments.get_by_id(db, id, investor_id)
        if not investment:
            raise HTTPException(500, "InvestorInvestmentServices: investment not found using provided id, investor_id")
        return investment
    



    async def get_all_investment_info_for_by_investor_id(db, investor_id):
        status_order = case(
            (InvestorInvestments.status == "active", 1),
            (InvestorInvestments.status == "partial", 2),
            (InvestorInvestments.status == "sold", 3),
            else_=4
        )

        stmt = (
            select(InvestorInvestments)
            .where(InvestorInvestments.investor_id == investor_id)
            .order_by(
                status_order,                          # ACTIVE → PARTIAL → SOLD
                desc(InvestorInvestments.invested_at) 
            )
        )

        result = await db.execute(stmt)
        return result.scalars().all()

