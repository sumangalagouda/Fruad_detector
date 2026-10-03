import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.user import User


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_register_and_login(client):
    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "username": "investigator_alice",
        "email": "alice@fintelligence.org",
        "password": "SecurePassword123!",
        "full_name": "Alice Smith",
        "role": "investigator",
    })
    assert reg_resp.status_code == 201
    reg_data = reg_resp.get_json()
    assert reg_data["success"] is True
    assert "token" in reg_data["data"]

    # 2. Login
    login_resp = client.post("/api/auth/login", json={
        "username": "investigator_alice",
        "password": "SecurePassword123!",
    })
    assert login_resp.status_code == 200
    login_data = login_resp.get_json()
    token = login_data["data"]["token"]
    assert token is not None

    # 3. Access authenticated me endpoint
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.get_json()["data"]["user"]["username"] == "investigator_alice"
