import pytest
import io
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_appeal_generation_versions_and_pdf_export(client: AsyncClient):
    # Register & Login
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "appeals.officer@hospital.org",
        "password": "Password123!",
        "full_name": "Appeals Officer",
        "organization_name": "Apex Healthcare Partners",
    })
    token = reg_res.json()["access_token"]

    # Create Claim
    claim_res = await client.post("/api/v1/claims", json={
        "payer_name": "Anthem Blue Cross",
        "policy_number_masked": "POL-****-8391",
        "procedure_codes": ["22551"],
        "diagnosis_codes": ["M50.20"],
        "claim_amount": 24800.0,
        "denied_amount": 19200.0,
        "denial_date": "2025-08-15",
        "denial_reason": "Denied CO-16: Operative records missing.",
        "denial_code": "CO-16",
        "patient_first_name": "Marcus",
        "patient_last_name": "Chen",
        "patient_dob": "1982-11-25",
    }, headers={"Authorization": f"Bearer {token}"})
    claim_id = claim_res.json()["id"]

    # Upload Doc
    doc_content = b"ACDF Operative Report C5-C6 with intervertebral cage. Verified neuro-monitoring attached."
    await client.post(
        "/api/v1/documents/upload",
        files={"file": ("ACDF_Operative_Report.txt", io.BytesIO(doc_content), "text/plain")},
        data={"category": "clinical_record", "claim_id": claim_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Run Analysis
    await client.post(
        f"/api/v1/claims/{claim_id}/analyze",
        json={"force_reanalyze": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Generate Appeal Letter
    gen_res = await client.post(
        f"/api/v1/claims/{claim_id}/appeal/generate",
        json={"tone": "formal_assertive"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gen_res.status_code == 200
    appeal = gen_res.json()
    appeal_id = appeal["id"]
    assert appeal["status"] == "draft"
    assert appeal["current_version"] == 1
    assert "full_letter_text" in appeal
    assert len(appeal["full_letter_text"]) > 100

    # Edit Appeal Letter (creates Version 2)
    new_text = appeal["full_letter_text"] + "\n\nAddendum: Physician peer-to-peer discussion requested."
    update_res = await client.patch(
        f"/api/v1/appeals/{appeal_id}",
        json={"full_letter_text": new_text, "status": "approved", "change_summary": "Added addendum and approved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    updated_appeal = update_res.json()
    assert updated_appeal["status"] == "approved"
    assert updated_appeal["current_version"] == 2
    assert len(updated_appeal["versions"]) == 2

    # Export PDF
    pdf_res = await client.get(
        f"/api/v1/appeals/{appeal_id}/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

