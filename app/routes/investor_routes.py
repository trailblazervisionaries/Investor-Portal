from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.investor_service import InvestorService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.investor import InvestorCreate, InvestorUpdate, InvestorResponse, InvestorPaginationResponse
import logging 
import math
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model = InvestorResponse)
async def add_admin(data: InvestorCreate, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    role = request.state.user.role
    if role != "fund-assistant":
        raise HTTPException(403, "you are not authorise to perform this operation")
    investor = await InvestorService.create_investor(db, user_id, data)
    return InvestorResponse.model_validate(investor)


@router.put("/update/{user_id}", response_model = InvestorResponse)
async def add_admin(data: InvestorUpdate, user_id: str, request: Request, db: Session = Depends(get_db)):
    login_user_id = request.state.user.user_id
    role = request.state.user.role
    if role != "fund-assistant":
        raise HTTPException(403, "you are not authorise to perform this operation")
    investor = await InvestorService.update_investor(db, user_id, data)
    return InvestorResponse.model_validate(investor)


@router.get("/me", response_model = InvestorResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor = await InvestorService.get_my_info(db, user_id)
    if not investor:
        raise HTTPException(404, "Investor data not found")
    return InvestorResponse.model_validate(investor)


@router.get("/getall", response_model = list[InvestorResponse])
async def get_me(request: Request, db: Session = Depends(get_db)):
    added_by = request.state.user.user_id
    investors = await InvestorService.get_all_investor_info(db, added_by)
    if not investors:
        # raise HTTPException(404, "Investor data not found")
        return []
    return [InvestorResponse.model_validate(investor) for investor in investors]




@router.get("/getall-info", response_model=InvestorPaginationResponse)
async def get_me(
    request: Request, 
    deleted: bool,
    db: Session = Depends(get_db),
    page: int = 1, 
    size: int = 10
):
    skip = (max(1, page) - 1) * size
    
    investors, total_count = await InvestorService.get_all_investor(db, skip, size, deleted)
    
    total_pages = math.ceil(total_count / size) if total_count > 0 else 0

    return {
        "items": [InvestorResponse.model_validate(i) for i in investors],
        "total_count": total_count,
        "page": page,
        "size": size,
        "total_pages": total_pages
    }


@router.delete("/delete/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role not in ["fund-assistant","admin"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await InvestorService.get_info_and_delete(db, user_id)

@router.post("/deactivate/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role not in ["fund-assistant","admin"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await InvestorService.get_info_and_deactivate(db, user_id)

@router.post("/activate/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role not in ["fund-assistant","admin"]:
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await InvestorService.get_info_and_activate(db, user_id)

