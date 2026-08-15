import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.seed import seed_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    seed_data()
    yield


def test_seed_and_admin_stats():
    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_companies"] == 4
    assert data["total_offers"] == 2
    assert data["total_accepted_partnerships"] == 2
    assert data["total_employee_codes"] == 4
    assert data["total_transactions"] == 2
    assert data["total_gmv"] == 2650000.0
    assert data["total_commission_earned"] == 53000.0


def test_auth_and_me():
    # Login as Coffee House
    login_resp = client.post(
        "/auth/login",
        data={"username": "coffee@provider.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Get profile
    me_resp = client.get(
        "/companies/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "coffee@provider.com"


def test_qr_verification_and_redemption():
    # Verify valid code
    verify_resp = client.post("/redeem/verify", json={"code": "HAMKOR-QR-101"})
    assert verify_resp.status_code == 200
    res = verify_resp.json()
    assert res["valid"] is True
    assert res["employee_name"] == "Alisher Navoiy"

    # Confirm redemption
    confirm_resp = client.post(
        "/redeem/confirm",
        json={
            "code": "HAMKOR-QR-101",
            "amount": 100000.0,
            "redeemed_by_note": "Test Kassir",
        },
    )
    assert confirm_resp.status_code == 200
    txn_data = confirm_resp.json()
    assert txn_data["amount"] == 100000.0
    assert txn_data["commission_amount"] == 2000.0  # 2% of 100,000
