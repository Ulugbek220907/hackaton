from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import (
    Company,
    CompanyType,
    Offer,
    Partnership,
    PartnershipStatus,
    EmployeeCode,
    Transaction,
)
from backend.schemas import AdminStatsOut

router = APIRouter(prefix="/admin", tags=["Admin Statistics"])


@router.get("/stats", response_model=AdminStatsOut)
def get_admin_stats(db: Session = Depends(get_db)):
    total_companies = db.query(Company).count()
    total_providers = (
        db.query(Company)
        .filter(Company.company_type.in_([CompanyType.provider, CompanyType.both]))
        .count()
    )
    total_partners = (
        db.query(Company)
        .filter(Company.company_type.in_([CompanyType.partner, CompanyType.both]))
        .count()
    )

    total_offers = db.query(Offer).count()

    total_accepted_partnerships = (
        db.query(Partnership)
        .filter(Partnership.status == PartnershipStatus.accepted)
        .count()
    )

    total_employee_codes = db.query(EmployeeCode).count()

    total_transactions = db.query(Transaction).count()

    gmv_res = db.query(func.sum(Transaction.amount)).scalar()
    total_gmv = float(gmv_res) if gmv_res is not None else 0.0

    comm_res = db.query(func.sum(Transaction.commission_amount)).scalar()
    total_commission_earned = float(comm_res) if comm_res is not None else 0.0

    return AdminStatsOut(
        total_companies=total_companies,
        total_providers=total_providers,
        total_partners=total_partners,
        total_offers=total_offers,
        total_accepted_partnerships=total_accepted_partnerships,
        total_employee_codes=total_employee_codes,
        total_transactions=total_transactions,
        total_gmv=round(total_gmv, 2),
        total_commission_earned=round(total_commission_earned, 2),
    )
