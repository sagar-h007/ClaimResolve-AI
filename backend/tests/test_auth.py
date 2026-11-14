import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    reg_payload = {
        "email": "doctor@regionalhealth.org",
        "password": "Password123!",
        "full_name": "Dr. Marcus Vance",
        "organization_name": "Regional Health Center",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "doctor@regionalhealth.org"

    # Login
    login_payload = {
        "email": "doctor@regionalhealth.org",
        "password": "Password123!",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # Get Me
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "doctor@regionalhealth.org"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    login_payload = {
        "email": "nonexistent@hospital.org",
        "password": "wrongpassword",
    }
    resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401

