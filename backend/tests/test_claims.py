import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_claims_crud_and_tenant_isolation(client: AsyncClient):
    # Register Org A
    reg_a = await client.post("/api/v1/auth/register", json={
        "email": "userA@hospitalA.org",
        "password": "Password123!",
        "full_name": "Admin Org A",
        "organization_name": "Hospital A Health",
    })
    token_a = reg_a.json()["access_token"]

    # Register Org B
    reg_b = await client.post("/api/v1/auth/register", json={
        "email": "userB@hospitalB.org",
        "password": "Password123!",
        "full_name": "Admin Org B",
        "organization_name": "Hospital B Health",
    })
    token_b = reg_b.json()["access_token"]

    # Create Claim in Org A
    claim_payload = {
        "payer_name": "United Healthcare",
        "policy_number_masked": "POL-****-8812",
        "procedure_codes": ["29881"],
        "diagnosis_codes": ["M23.22"],
        "claim_amount": 5400.0,
        "denied_amount": 4850.0,
        "denial_date": "2025-08-14",
        "denial_reason": "Medical necessity not established.",
        "denial_code": "CO-50",
        "patient_first_name": "Eleanor",
        "patient_last_name": "Vance",
        "patient_dob": "1974-03-12",
    }
    create_resp = await client.post(
        "/api/v1/claims",
        json=claim_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    claim_a = create_resp.json()
    claim_id = claim_a["id"]
    assert claim_a["claim_number"].startswith("CLM-2025-")

    # Get Claim as Org A -> OK
    get_a = await client.get(
        f"/api/v1/claims/{claim_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_a.status_code == 200

    # Tenant Isolation: Get Claim as Org B -> 404 NOT FOUND
    get_b = await client.get(
        f"/api/v1/claims/{claim_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_b.status_code == 404

    # Update Claim as Org A
    patch_resp = await client.patch(
        f"/api/v1/claims/{claim_id}",
        json={"notes": "Updated review notes"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["notes"] == "Updated review notes"

