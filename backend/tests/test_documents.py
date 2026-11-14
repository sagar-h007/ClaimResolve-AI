import pytest
import io
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_upload_and_chunking(client: AsyncClient):
    # Register Org & User
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "docs@hospital.org",
        "password": "Password123!",
        "full_name": "Records Specialist",
        "organization_name": "Memorial Records Hospital",
    })
    token = reg_res.json()["access_token"]

    # Create Claim
    claim_res = await client.post("/api/v1/claims", json={
        "payer_name": "Aetna",
        "policy_number_masked": "POL-****-4920",
        "procedure_codes": ["43239"],
        "diagnosis_codes": ["K21.9"],
        "claim_amount": 3200.0,
        "denied_amount": 1450.0,
        "patient_first_name": "Sophia",
        "patient_last_name": "Rodriguez",
        "patient_dob": "1968-07-09",
    }, headers={"Authorization": f"Bearer {token}"})
    claim_id = claim_res.json()["id"]

    # Upload mock clinical document
    doc_content = (
        b"PATIENT PROGRESS NOTE & CLINICAL ENDOSCOPY REPORT\n\n"
        b"Patient: Sophia Rodriguez | Date: 2025-06-12\n"
        b"Indication: Persistent GERD refractory to 8 weeks omeprazole 40mg daily.\n"
        b"Endoscopic biopsy demonstrated active esophagitis with intestinal metaplasia.\n\n"
        b"Plan: Targeted medical necessity established for procedure CPT 43239."
    )
    files = {
        "file": ("Sophia_Rodriguez_Clinical_Note.txt", io.BytesIO(doc_content), "text/plain"),
    }
    data = {
        "category": "clinical_record",
        "claim_id": claim_id,
    }
    upload_res = await client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["status"] == "processed"
    assert doc_data["chunk_count"] >= 1
    doc_id = doc_data["id"]

    # Check status endpoint
    status_res = await client.get(
        f"/api/v1/documents/{doc_id}/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "processed"

