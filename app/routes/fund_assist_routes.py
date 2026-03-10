from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.config.database import get_db
from app.services.fund_assist_service import FundAssistService
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.schemas.fund_assist import FundAssistCreate, FundAssistUpdate, FundAssistResponse, FundAssistPaginationResponse
import logging 
import math
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/add", response_model = FundAssistResponse)
async def add_admin(data: FundAssistCreate, request: Request, db: Session = Depends(get_db)):
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "you are not authorise to perform this operation")
    fund_assistant = await FundAssistService.create_fund_assistant(db, data)
    return FundAssistResponse.model_validate(fund_assistant)


@router.put("/update/{user_id}", response_model = FundAssistResponse)
async def add_admin(data: FundAssistUpdate, user_id:str, request: Request, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "you are not authorise to perform this operation")
    fund_assistant = await FundAssistService.update_fund_assistant(db, user_id, data)
    return FundAssistResponse.model_validate(fund_assistant)



@router.get("/me", response_model = FundAssistResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.user_id
    fund_assist = await FundAssistService.get_my_info(db, user_id)
    if not fund_assist:
        raise HTTPException(404, "investor_assist data not found")
    return FundAssistResponse.model_validate(fund_assist)




@router.get("/getall", response_model=FundAssistPaginationResponse)
async def get_me(
    request: Request, 
    deleted: bool,
    db: Session = Depends(get_db),
    page: int = 1, 
    size: int = 10
):
    skip = (max(1, page) - 1) * size
    
    investors, total_count = await FundAssistService.get_info_all_fund_assistant(db, skip, size, deleted)
    
    total_pages = math.ceil(total_count / size) if total_count > 0 else 0

    return {
        "items": [FundAssistResponse.model_validate(i) for i in investors],
        "total_count": total_count,
        "page": page,
        "size": size,
        "total_pages": total_pages
    }


@router.delete("/delete/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await FundAssistService.get_info_and_delete(db, user_id)

@router.post("/deactivate/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await FundAssistService.get_info_and_deactivate(db, user_id)

@router.post("/activate/{user_id}")
async def get_me(request: Request, user_id: str, db: Session = Depends(get_db)):
    id = request.state.user.user_id
    role = request.state.user.role
    if role != "admin":
        raise HTTPException(403, "you are not authorise to perform this operation")
    return await FundAssistService.get_info_and_activate(db, user_id)


