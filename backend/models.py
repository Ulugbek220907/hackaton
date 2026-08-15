import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    Date,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class CompanyType(str, enum.Enum):
    provider = "provider"
    partner = "partner"
    both = "both"


class DiscountType(str, enum.Enum):
    percent = "percent"
    fixed = "fixed"
    custom = "custom"


class OfferStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"


class PartnershipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class CommissionPayer(str, enum.Enum):
    provider = "provider"
    partner = "partner"
    both = "both"


class EmployeeCodeStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    used_up = "used_up"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    company_type = Column(Enum(CompanyType), nullable=False, default=CompanyType.both)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_offers = relationship("Offer", foreign_keys="Offer.provider_id", back_populates="provider")
    received_offers = relationship("Offer", foreign_keys="Offer.target_partner_id", back_populates="target_partner")
    partnerships = relationship("Partnership", back_populates="partner")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(Enum(DiscountType), nullable=False, default=DiscountType.percent)
    discount_value = Column(String(100), nullable=False)
    max_usage_per_code = Column(Integer, nullable=False, default=1)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    status = Column(Enum(OfferStatus), nullable=False, default=OfferStatus.sent)
    target_partner_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("Company", foreign_keys=[provider_id], back_populates="created_offers")
    target_partner = relationship("Company", foreign_keys=[target_partner_id], back_populates="received_offers")
    partnerships = relationship("Partnership", back_populates="offer", cascade="all, delete-orphan")


class Partnership(Base):
    __tablename__ = "partnerships"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    status = Column(Enum(PartnershipStatus), nullable=False, default=PartnershipStatus.pending)
    commission_payer = Column(Enum(CommissionPayer), nullable=False, default=CommissionPayer.provider)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    offer = relationship("Offer", back_populates="partnerships")
    partner = relationship("Company", back_populates="partnerships")
    employee_codes = relationship("EmployeeCode", back_populates="partnership", cascade="all, delete-orphan")


class EmployeeCode(Base):
    __tablename__ = "employee_codes"

    id = Column(Integer, primary_key=True, index=True)
    partnership_id = Column(Integer, ForeignKey("partnerships.id"), nullable=False)
    employee_name = Column(String(255), nullable=False)
    employee_identifier = Column(String(255), nullable=False)
    code = Column(String(255), unique=True, index=True, nullable=False)
    max_usage = Column(Integer, nullable=False, default=1)
    usage_count = Column(Integer, nullable=False, default=0)
    status = Column(Enum(EmployeeCodeStatus), nullable=False, default=EmployeeCodeStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)

    partnership = relationship("Partnership", back_populates="employee_codes")
    transactions = relationship("Transaction", back_populates="employee_code", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    employee_code_id = Column(Integer, ForeignKey("employee_codes.id"), nullable=False)
    amount = Column(Float, nullable=False)
    commission_percent = Column(Float, nullable=False, default=2.0)
    commission_amount = Column(Float, nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)
    redeemed_by_note = Column(String(255), nullable=True)

    employee_code = relationship("EmployeeCode", back_populates="transactions")
