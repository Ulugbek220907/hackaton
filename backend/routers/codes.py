import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Company,
    Partnership,
    PartnershipStatus,
    EmployeeCode,
    EmployeeCodeStatus,
)
from backend.schemas import GenerateCodesRequest, EmployeeCodeOut
from backend.auth import get_current_company
from backend.qr_utils import generate_qr_code_image

router = APIRouter(prefix="/codes", tags=["Employee QR Codes"])


@router.post("/generate", response_model=List[EmployeeCodeOut])
def generate_codes(
    req: GenerateCodesRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    partnership = (
        db.query(Partnership).filter(Partnership.id == req.partnership_id).first()
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    if (
        partnership.partner_id != current_company.id
        and partnership.offer.provider_id != current_company.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this partnership",
        )

    if partnership.status != PartnershipStatus.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partnership is not accepted yet",
        )

    max_usage = partnership.offer.max_usage_per_code
    created_codes = []

    for emp in req.employees:
        unique_token = str(uuid.uuid4())
        qr_url = generate_qr_code_image(unique_token)

        emp_code = EmployeeCode(
            partnership_id=partnership.id,
            employee_name=emp.employee_name,
            employee_identifier=emp.employee_identifier,
            code=unique_token,
            max_usage=max_usage,
            usage_count=0,
            status=EmployeeCodeStatus.active,
        )
        db.add(emp_code)
        db.commit()
        db.refresh(emp_code)

        created_codes.append(
            EmployeeCodeOut(
                id=emp_code.id,
                partnership_id=emp_code.partnership_id,
                employee_name=emp_code.employee_name,
                employee_identifier=emp_code.employee_identifier,
                code=emp_code.code,
                max_usage=emp_code.max_usage,
                usage_count=emp_code.usage_count,
                status=emp_code.status,
                qr_image_url=qr_url,
                created_at=emp_code.created_at,
            )
        )

    return created_codes


@router.get("/{partnership_id}", response_model=List[EmployeeCodeOut])
def get_codes_for_partnership(
    partnership_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    partnership = (
        db.query(Partnership).filter(Partnership.id == partnership_id).first()
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    codes = (
        db.query(EmployeeCode)
        .filter(EmployeeCode.partnership_id == partnership_id)
        .all()
    )

    results = []
    for code_obj in codes:
        qr_url = generate_qr_code_image(code_obj.code)
        results.append(
            EmployeeCodeOut(
                id=code_obj.id,
                partnership_id=code_obj.partnership_id,
                employee_name=code_obj.employee_name,
                employee_identifier=code_obj.employee_identifier,
                code=code_obj.code,
                max_usage=code_obj.max_usage,
                usage_count=code_obj.usage_count,
                status=code_obj.status,
                qr_image_url=qr_url,
                created_at=code_obj.created_at,
            )
        )

    return results
