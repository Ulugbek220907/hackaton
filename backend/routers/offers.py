from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Company,
    CompanyType,
    Offer,
    OfferStatus,
    Partnership,
    PartnershipStatus,
)
from backend.schemas import OfferCreate, OfferOut, OfferRespond, PartnershipOut
from backend.auth import get_current_company

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.post("", response_model=OfferOut)
def create_offer(
    offer_in: OfferCreate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    if current_company.company_type not in [CompanyType.provider, CompanyType.both]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only providers can create offers",
        )

    target_partner_name = None
    if offer_in.target_partner_id:
        target = db.query(Company).filter(Company.id == offer_in.target_partner_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target partner company not found",
            )
        target_partner_name = target.name

    offer = Offer(
        provider_id=current_company.id,
        title=offer_in.title,
        description=offer_in.description,
        discount_type=offer_in.discount_type,
        discount_value=offer_in.discount_value,
        max_usage_per_code=offer_in.max_usage_per_code,
        valid_from=offer_in.valid_from,
        valid_until=offer_in.valid_until,
        status=OfferStatus.sent,
        target_partner_id=offer_in.target_partner_id,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)

    # If sent directly to a target partner, automatically create a pending partnership entry
    if offer_in.target_partner_id:
        partnership = Partnership(
            offer_id=offer.id,
            partner_id=offer_in.target_partner_id,
            status=PartnershipStatus.pending,
        )
        db.add(partnership)
        db.commit()

    return OfferOut(
        id=offer.id,
        provider_id=offer.provider_id,
        provider_name=current_company.name,
        title=offer.title,
        description=offer.description,
        discount_type=offer.discount_type,
        discount_value=offer.discount_value,
        max_usage_per_code=offer.max_usage_per_code,
        valid_from=offer.valid_from,
        valid_until=offer.valid_until,
        status=offer.status,
        target_partner_id=offer.target_partner_id,
        target_partner_name=target_partner_name,
        created_at=offer.created_at,
    )


@router.get("/sent", response_model=List[OfferOut])
def get_sent_offers(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    offers = db.query(Offer).filter(Offer.provider_id == current_company.id).all()
    results = []
    for offer in offers:
        target_name = offer.target_partner.name if offer.target_partner else "All Partners"
        results.append(
            OfferOut(
                id=offer.id,
                provider_id=offer.provider_id,
                provider_name=current_company.name,
                title=offer.title,
                description=offer.description,
                discount_type=offer.discount_type,
                discount_value=offer.discount_value,
                max_usage_per_code=offer.max_usage_per_code,
                valid_from=offer.valid_from,
                valid_until=offer.valid_until,
                status=offer.status,
                target_partner_id=offer.target_partner_id,
                target_partner_name=target_name,
                created_at=offer.created_at,
            )
        )
    return results


@router.get("/received", response_model=List[OfferOut])
def get_received_offers(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    if current_company.company_type not in [CompanyType.partner, CompanyType.both]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only partners can receive offers",
        )

    # Offers targeted specifically to this partner OR general offers (target_partner_id IS NULL)
    offers = (
        db.query(Offer)
        .filter(
            (Offer.target_partner_id == current_company.id)
            | (Offer.target_partner_id.is_(None))
        )
        .filter(Offer.provider_id != current_company.id)
        .all()
    )

    results = []
    for offer in offers:
        results.append(
            OfferOut(
                id=offer.id,
                provider_id=offer.provider_id,
                provider_name=offer.provider.name,
                title=offer.title,
                description=offer.description,
                discount_type=offer.discount_type,
                discount_value=offer.discount_value,
                max_usage_per_code=offer.max_usage_per_code,
                valid_from=offer.valid_from,
                valid_until=offer.valid_until,
                status=offer.status,
                target_partner_id=offer.target_partner_id,
                target_partner_name=current_company.name if offer.target_partner_id else "All Partners",
                created_at=offer.created_at,
            )
        )
    return results


@router.post("/{offer_id}/respond", response_model=PartnershipOut)
def respond_to_offer(
    offer_id: int,
    respond_data: OfferRespond,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found"
        )

    partnership = (
        db.query(Partnership)
        .filter(
            Partnership.offer_id == offer_id,
            Partnership.partner_id == current_company.id,
        )
        .first()
    )

    if not partnership:
        partnership = Partnership(
            offer_id=offer_id,
            partner_id=current_company.id,
            status=respond_data.status,
            commission_payer=respond_data.commission_payer,
            responded_at=datetime.utcnow(),
        )
        db.add(partnership)
    else:
        partnership.status = respond_data.status
        partnership.commission_payer = respond_data.commission_payer
        partnership.responded_at = datetime.utcnow()

    db.commit()
    db.refresh(partnership)

    return PartnershipOut(
        id=partnership.id,
        offer_id=partnership.offer_id,
        partner_id=partnership.partner_id,
        partner_name=current_company.name,
        offer_title=offer.title,
        provider_name=offer.provider.name,
        discount_value=offer.discount_value,
        status=partnership.status,
        commission_payer=partnership.commission_payer,
        responded_at=partnership.responded_at,
        created_at=partnership.created_at,
    )


@router.get("/partnerships", response_model=List[PartnershipOut])
def get_my_partnerships(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    partnerships = (
        db.query(Partnership)
        .filter(
            (Partnership.partner_id == current_company.id)
            | (Partnership.offer.has(provider_id=current_company.id))
        )
        .all()
    )

    results = []
    for p in partnerships:
        results.append(
            PartnershipOut(
                id=p.id,
                offer_id=p.offer_id,
                partner_id=p.partner_id,
                partner_name=p.partner.name,
                offer_title=p.offer.title,
                provider_name=p.offer.provider.name,
                discount_value=p.offer.discount_value,
                status=p.status,
                commission_payer=p.commission_payer,
                responded_at=p.responded_at,
                created_at=p.created_at,
            )
        )
    return results
