from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import APIMiddleware
from app.config.database import create_tables
from fastapi.staticfiles import StaticFiles
from app.routes import (user_routes, admin_routes, fund_assist_routes, investor_assist_routes,
                         investor_routes, leads_routes, lease_rent_routes, loan_amort_routes,
                           property_routes, property_type_routes, propery_unit_routes, investor_assist_assign_routes,
                           investor_investment_routes, income_routes, expense_routes, property_proforma_routes)
import logging
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


app.add_middleware(APIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","http://localhost:3000", "http://127.0.0.1:3000"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],   
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    logger.info("Application started 🚀")
    await create_tables()
    # logger.info("Scheduler started")


@app.get("/")
def health():
    return {"status": "FastAPI Scheduler Running"}


@app.get("/health")
def read_root():
    return {"message": "Welcome to RMS Backend :)"} 


app.include_router(user_routes.router, prefix="/api/users", tags=["user"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])
app.include_router(fund_assist_routes.router, prefix="/api/fund-assist", tags=["fund-assistant"])
app.include_router(investor_assist_routes.router, prefix="/api/investor-assist", tags=["investor-assistant"])
app.include_router(investor_routes.router, prefix="/api/investor", tags=["investors"])

#  it will stor the data of all the new users who want to ask queries or invest using wordpress website
app.include_router(leads_routes.router, prefix="/api/lead", tags=["leads"])


app.include_router(property_routes.router, prefix="/api/property", tags=["property"])
app.include_router(property_type_routes.router, prefix="/api/property-type", tags=["property-type"])
app.include_router(propery_unit_routes.router, prefix="/api/property-unit", tags=["propery-unit"])
app.include_router(lease_rent_routes.router, prefix="/api/lease-rent", tags=["lease-rent"])

#  for the property loan and amortization schedule routes
app.include_router(loan_amort_routes.router, prefix="/api/loan-amortz", tags=["loan-amortz"])

# for investor assistant assisgn related routes
app.include_router(investor_assist_assign_routes.router, prefix="/api/investor-assist-assign", tags=["investor-assistent-assign"])

# allocate the investment to the investor against the property
app.include_router(investor_investment_routes.router, prefix="/api/investment", tags=["investor-investment"])

app.include_router(income_routes.router, prefix="/api/income", tags=["income"])
app.include_router(expense_routes.router, prefix="/api/expense", tags=["expense"])

# Property Pro-forma, Rent Roll, and Growth Assumptions (from Excel model)
app.include_router(property_proforma_routes.router, prefix="/api/property-proforma", tags=["property-proforma"])




