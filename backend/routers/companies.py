from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Company, CompanyType
from backend.schemas import CompanyRegister, CompanyOut, Token
from backend.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_company,
)

router = APIRouter(prefix="", tags=["Auth & Companies"])


@router.post("/auth/register", response_model=CompanyOut)
def register_company(data: CompanyRegister, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with this email already exists",
        )

    company = Company(
        name=data.name,
        email=data.email,
        password_hash=get_password_hash(data.password),
        company_type=data.company_type,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/auth/login", response_model=Token)
def login_company(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.email == form_data.username).first()
    if not company or not verify_password(form_data.password, company.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(company.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/companies/me", response_model=CompanyOut)
def get_me(current_company: Company = Depends(get_current_company)):
    return current_company


@router.get("/companies/partners", response_model=List[CompanyOut])
def get_partners(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    # Returns companies that can act as partners
    partners = (
        db.query(Company)
        .filter(Company.company_type.in_([CompanyType.partner, CompanyType.both]))
        .filter(Company.id != current_company.id)
        .all()
    )
    return partners
