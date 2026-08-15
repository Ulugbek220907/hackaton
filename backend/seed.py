from datetime import date, timedelta
from backend.database import SessionLocal, engine, Base
from backend.models import (
    Company,
    CompanyType,
    Offer,
    OfferStatus,
    DiscountType,
    Partnership,
    PartnershipStatus,
    CommissionPayer,
    EmployeeCode,
    EmployeeCodeStatus,
    Transaction,
)
from backend.auth import get_password_hash
from backend.qr_utils import generate_qr_code_image


def seed_data(force: bool = False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if database is already populated
        existing_companies = db.query(Company).count()
        if existing_companies > 0 and not force:
            print("Database already contains data. Skipping seed.")
            return

        if force:
            print("Force clearing existing data...")
            db.query(Transaction).delete()
            db.query(EmployeeCode).delete()
            db.query(Partnership).delete()
            db.query(Offer).delete()
            db.query(Company).delete()
            db.commit()

        print("Seeding Companies...")
        provider1 = Company(
            name="Coffee House",
            email="coffee@provider.com",
            password_hash=get_password_hash("password123"),
            company_type=CompanyType.provider,
        )
        provider2 = Company(
            name="FitZone Fitness",
            email="fitzone@provider.com",
            password_hash=get_password_hash("password123"),
            company_type=CompanyType.provider,
        )
        partner1 = Company(
            name="Hamkorbank",
            email="hr@hamkorbank.com",
            password_hash=get_password_hash("password123"),
            company_type=CompanyType.partner,
        )
        partner2 = Company(
            name="IT Park Uzbekistan",
            email="hr@itpark.uz",
            password_hash=get_password_hash("password123"),
            company_type=CompanyType.partner,
        )

        db.add_all([provider1, provider2, partner1, partner2])
        db.commit()
        for c in [provider1, provider2, partner1, partner2]:
            db.refresh(c)

        print("Seeding Offers...")
        offer1 = Offer(
            provider_id=provider1.id,
            title="20% Chegirma Qahva va Shirinliklarga",
            description="Hamkorbank va IT Park xodimlari uchun barcha kofe va desertlarga 20% chegirma.",
            discount_type=DiscountType.percent,
            discount_value="20%",
            max_usage_per_code=5,
            valid_from=date.today() - timedelta(days=10),
            valid_until=date.today() + timedelta(days=60),
            status=OfferStatus.sent,
            target_partner_id=partner1.id,
        )
        offer2 = Offer(
            provider_id=provider2.id,
            title="30% Chegirma Yillik Fitnes Abonementga",
            description="Barcha hamkor xodimlarga FitZone zallariga yillik pass uchun 30% discount.",
            discount_type=DiscountType.percent,
            discount_value="30%",
            max_usage_per_code=2,
            valid_from=date.today() - timedelta(days=5),
            valid_until=date.today() + timedelta(days=90),
            status=OfferStatus.sent,
            target_partner_id=None,  # General offer
        )

        db.add_all([offer1, offer2])
        db.commit()
        db.refresh(offer1)
        db.refresh(offer2)

        print("Seeding Partnerships...")
        p1 = Partnership(
            offer_id=offer1.id,
            partner_id=partner1.id,
            status=PartnershipStatus.accepted,
            commission_payer=CommissionPayer.provider,
        )
        p2 = Partnership(
            offer_id=offer2.id,
            partner_id=partner2.id,
            status=PartnershipStatus.accepted,
            commission_payer=CommissionPayer.provider,
        )

        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        print("Seeding Employee Codes...")
        employees_data = [
            (p1, "Alisher Navoiy", "alisher@hamkorbank.uz", "HAMKOR-QR-101"),
            (p1, "Zilola Mahmudova", "zilola@hamkorbank.uz", "HAMKOR-QR-102"),
            (p2, "Bobur Karimov", "bobur@itpark.uz", "ITPARK-QR-201"),
            (p2, "Madina Umarova", "madina@itpark.uz", "ITPARK-QR-202"),
        ]

        emp_codes = []
        for partnership, name, email, code in employees_data:
            qr_url = generate_qr_code_image(code)
            emp_code = EmployeeCode(
                partnership_id=partnership.id,
                employee_name=name,
                employee_identifier=email,
                code=code,
                max_usage=partnership.offer.max_usage_per_code,
                usage_count=1,
                status=EmployeeCodeStatus.active,
            )
            db.add(emp_code)
            emp_codes.append(emp_code)

        db.commit()
        for ec in emp_codes:
            db.refresh(ec)

        print("Seeding Sample Transactions...")
        txn1 = Transaction(
            employee_code_id=emp_codes[0].id,
            amount=150000.0,
            commission_percent=2.0,
            commission_amount=3000.0,
            redeemed_by_note="Kassir: Javohir",
        )
        txn2 = Transaction(
            employee_code_id=emp_codes[2].id,
            amount=2500000.0,
            commission_percent=2.0,
            commission_amount=50000.0,
            redeemed_by_note="Kassir: Nigora",
        )

        db.add_all([txn1, txn2])
        db.commit()

        print("Database seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
