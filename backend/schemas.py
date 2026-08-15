from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from backend.models import CompanyType, DiscountType, OfferStatus, PartnershipStatus, CommissionPayer, EmployeeCodeStatus


# Auth & Company Schemas
class CompanyRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_type: CompanyType = CompanyType.both


class CompanyLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    company_type: CompanyType
    created_at: datetime


# Offer Schemas
class OfferCreate(BaseModel):
    title: str
    description: Optional[str] = None
    discount_type: DiscountType = DiscountType.percent
    discount_value: str
    max_usage_per_code: int = 1
    valid_from: date
    valid_until: date
    target_partner_id: Optional[int] = None


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    provider_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: str
    max_usage_per_code: int
    valid_from: date
    valid_until: date
    status: OfferStatus
    target_partner_id: Optional[int] = None
    target_partner_name: Optional[str] = None
    created_at: datetime


class OfferRespond(BaseModel):
    status: PartnershipStatus  # accepted or rejected
    commission_payer: Optional[CommissionPayer] = CommissionPayer.provider


# Partnership Schemas
class PartnershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int
    partner_id: int
    partner_name: Optional[str] = None
    offer_title: Optional[str] = None
    provider_name: Optional[str] = None
    discount_value: Optional[str] = None
    status: PartnershipStatus
    commission_payer: CommissionPayer
    responded_at: Optional[datetime] = None
    created_at: datetime


# Employee Code Schemas
class EmployeeInput(BaseModel):
    employee_name: str
    employee_identifier: str


class GenerateCodesRequest(BaseModel):
    partnership_id: int
    employees: List[EmployeeInput]


class EmployeeCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partnership_id: int
    employee_name: str
    employee_identifier: str
    code: str
    max_usage: int
    usage_count: int
    status: EmployeeCodeStatus
    qr_image_url: str
    created_at: datetime


# Redeem Schemas
class RedeemVerifyRequest(BaseModel):
    code: str


class RedeemVerifyResponse(BaseModel):
    valid: bool
    message: str
    employee_name: Optional[str] = None
    offer_title: Optional[str] = None
    provider_name: Optional[str] = None
    partner_name: Optional[str] = None
    discount_value: Optional[str] = None
    remaining_usage: Optional[int] = None


class RedeemConfirmRequest(BaseModel):
    code: str
    amount: float
    redeemed_by_note: Optional[str] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code_id: int
    amount: float
    commission_percent: float
    commission_amount: float
    redeemed_at: datetime
    redeemed_by_note: Optional[str] = None
    employee_name: Optional[str] = None
    offer_title: Optional[str] = None


# Admin Stats Schema
class AdminStatsOut(BaseModel):
    total_companies: int
    total_providers: int
    total_partners: int
    total_offers: int
    total_accepted_partnerships: int
    total_employee_codes: int
    total_transactions: int
    total_gmv: float
    total_commission_earned: float
