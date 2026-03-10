from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.investor_assist_service import InvestorAssistService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.investor_assist import InvestorAssistCreate, InvestorAssistUpdate, InvestorAssistResponse, InvestorAssistPaginationResponse
import logging 
import math
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model = InvestorAssistResponse)
async def add_admin(request: Request, data: InvestorAssistCreate, db: Session = Depends(get_db)):
    role = request.state.user.role
    user_id = request.state.user.user_id
    if role not in ["admin","investor-assistant"]:
        raise HTTPException(403, "You don't have permission to perform this operation")
    investor_assistant = await InvestorAssistService.create_investor_assistant(db, data, user_id)
    return InvestorAssistResponse.model_validate(investor_assistant)


@router.put("/update", response_model = InvestorAssistResponse)
async def add_admin(data: InvestorAssistUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor_assistant = await InvestorAssistService.update_investor_assistant(db, user_id, data)
    return InvestorAssistResponse.model_validate(investor_assistant)


@router.get("/me", response_model = InvestorAssistResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    investor_assist = await InvestorAssistService.get_my_info(db, user_id)
    if not investor_assist:
        raise HTTPException(404, "investor_assist data not found")
    return InvestorAssistResponse.model_validate(investor_assist)


# @router.get("/getall", response_model = list[InvestorAssistResponse])
# async def get_me(request: Request, db: Session = Depends(get_db)):
#     added_by = request.state.user.user_id
#     investors_assist = await InvestorAssistService.get_all_investor_info(db, added_by)
#     if not investors_assist:
#         # raise HTTPException(404, "Investor data not found")
#         return []
#     return [InvestorAssistResponse.model_validate(investor) for investor in investors_assist]


@router.get("/getall", response_model=InvestorAssistPaginationResponse)
async def get_me(
    request: Request, 
    deleted: bool,
    db: Session = Depends(get_db),
    page: int = 1, 
    size: int = 10
):
    skip = (max(1, page) - 1) * size
    
    investors, total_count = await InvestorAssistService.get_all_investor_info(db, skip, size, deleted)
    
    total_pages = math.ceil(total_count / size) if total_count > 0 else 0

    return {
        "items": [InvestorAssistResponse.model_validate(i) for i in investors],
        "total_count": total_count,
        "page": page,
        "size": size,
        "total_pages": total_pages
    }


@router.delete("/delete/{user_id}", response_model = InvestorAssistResponse)
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    return await InvestorAssistService.get_info_and_delete(db, user_id)

@router.post("/deactivate/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    return await InvestorAssistService.get_info_and_deactivate(db, user_id)

@router.post("/activate/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    return await InvestorAssistService.get_info_and_activate(db, user_id)


