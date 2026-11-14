import pytest
import io
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_analysis_and_citations(client: AsyncClient):
    # Register & Login
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "ai.auditor@hospital.org",
        "password": "Password123!",
        "full_name": "Clinical Reviewer",
        "organization_name": "St. Jude Health",
    })
    token = reg_res.json()["access_token"]

    # Create Claim
    claim_res = await client.post("/api/v1/claims", json={
        "payer_name": "United Healthcare",
        "policy_number_masked": "POL-****-1029",
        "procedure_codes": ["29881"],
        "diagnosis_codes": ["M23.22"],
        "claim_amount": 5400.0,
        "denied_amount": 4850.0,
        "denial_date": "2025-08-14",
        "denial_reason": "Denied CO-50: Lack of documented conservative therapy duration.",
        "denial_code": "CO-50",
        "patient_first_name": "Eleanor",
        "patient_last_name": "Vance",
        "patient_dob": "1974-03-12",
    }, headers={"Authorization": f"Bearer {token}"})
    claim_id = claim_res.json()["id"]

    # Upload Clinical Record
    doc_content = (
        b"PHYSICAL THERAPY DISCHARGE SUMMARY\n"
        b"Patient: Eleanor Vance | DOB: 1974-03-12\n"
        b"Patient completed 16 sessions of structured physical therapy spanning 8 consecutive weeks "
        b"between 05/14/2025 and 07/09/2025 with persistent mechanical locking. Meloxicam trial failed.\n"
    )
    files = {
        "file": ("PT_Discharge_Summary_Page2.txt", io.BytesIO(doc_content), "text/plain"),
    }
    await client.post(
        "/api/v1/documents/upload",
        files=files,
        data={"category": "clinical_record", "claim_id": claim_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Run AI Analysis
    analysis_res = await client.post(
        f"/api/v1/claims/{claim_id}/analyze",
        json={"force_reanalyze": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()

    assert analysis["status"] == "completed"
    assert "evidence_strength" in analysis
    assert len(analysis["potential_appeal_arguments"]) > 0

    # Verify Citations
    citations = analysis["evidence_references"]
    assert len(citations) > 0
    first_citation = citations[0]
    assert "source_document_title" in first_citation
    assert "page_number" in first_citation
    assert "citation_text" in first_citation
    assert first_citation["relevance_score"] > 0.0

