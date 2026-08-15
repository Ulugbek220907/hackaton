from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    EmployeeCode,
    EmployeeCodeStatus,
    Transaction,
    PartnershipStatus,
)
from backend.schemas import (
    RedeemVerifyRequest,
    RedeemVerifyResponse,
    RedeemConfirmRequest,
    TransactionOut,
)

router = APIRouter(prefix="/redeem", tags=["Redeem / Scanner"])


@router.post("/verify", response_model=RedeemVerifyResponse)
def verify_code(req: RedeemVerifyRequest, db: Session = Depends(get_db)):
    emp_code = (
        db.query(EmployeeCode).filter(EmployeeCode.code == req.code).first()
    )
    if not emp_code:
        return RedeemVerifyResponse(
            valid=False, message="QR-kod topilmadi (Invalid Code)"
        )

    partnership = emp_code.partnership
    offer = partnership.offer

    today = date.today()
    if offer.valid_from > today or offer.valid_until < today:
        emp_code.status = EmployeeCodeStatus.expired
        db.commit()
        return RedeemVerifyResponse(
            valid=False, message="Taklif amal qilish muddati o'tgan (Offer Expired)"
        )

    if emp_code.usage_count >= emp_code.max_usage:
        emp_code.status = EmployeeCodeStatus.used_up
        db.commit()
        return RedeemVerifyResponse(
            valid=False, message="QR-kod ishlatish limiti tugagan (Usage limit reached)"
        )

    if emp_code.status != EmployeeCodeStatus.active:
        return RedeemVerifyResponse(
            valid=False, message=f"QR-kod holati: {emp_code.status.value}"
        )

    remaining = emp_code.max_usage - emp_code.usage_count

    return RedeemVerifyResponse(
        valid=True,
        message="QR-kod tasdiqlandi (Valid Code)",
        employee_name=emp_code.employee_name,
        offer_title=offer.title,
        provider_name=offer.provider.name,
        partner_name=partnership.partner.name,
        discount_value=offer.discount_value,
        remaining_usage=remaining,
    )


@router.post("/confirm", response_model=TransactionOut)
def confirm_redemption(req: RedeemConfirmRequest, db: Session = Depends(get_db)):
    emp_code = (
        db.query(EmployeeCode).filter(EmployeeCode.code == req.code).first()
    )
    if not emp_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found"
        )

    if req.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction amount must be greater than zero",
        )

    partnership = emp_code.partnership
    offer = partnership.offer

    today = date.today()
    if offer.valid_from > today or offer.valid_until < today:
        emp_code.status = EmployeeCodeStatus.expired
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Offer expired"
        )

    if emp_code.usage_count >= emp_code.max_usage:
        emp_code.status = EmployeeCodeStatus.used_up
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usage limit reached"
        )

    if emp_code.status != EmployeeCodeStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code is not active: {emp_code.status.value}",
        )

    # 2% Commission Calculation
    commission_percent = 2.0
    commission_amount = round(req.amount * (commission_percent / 100.0), 2)

    emp_code.usage_count += 1
    if emp_code.usage_count >= emp_code.max_usage:
        emp_code.status = EmployeeCodeStatus.used_up

    txn = Transaction(
        employee_code_id=emp_code.id,
        amount=req.amount,
        commission_percent=commission_percent,
        commission_amount=commission_amount,
        redeemed_at=datetime.utcnow(),
        redeemed_by_note=req.redeemed_by_note,
    )

    db.add(txn)
    db.commit()
    db.refresh(txn)

    return TransactionOut(
        id=txn.id,
        employee_code_id=txn.employee_code_id,
        amount=txn.amount,
        commission_percent=txn.commission_percent,
        commission_amount=txn.commission_amount,
        redeemed_at=txn.redeemed_at,
        redeemed_by_note=txn.redeemed_by_note,
        employee_name=emp_code.employee_name,
        offer_title=offer.title,
    )
