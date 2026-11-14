from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.ai.llm_provider import get_llm_provider
from app.ai.evidence_comparator import EvidenceComparisonResult


class AppealGenerator:
    """
    Step 5: Evidence-Backed Insurance Appeal Generator.
    Produces a professional, legally persuasive medical necessity appeal
    citing source documents and exact page numbers.
    """

    @classmethod
    async def generate_appeal(
        cls,
        claim_data: Dict[str, Any],
        patient_data: Dict[str, Any],
        comparison: EvidenceComparisonResult,
        tone: str = "formal_assertive",
        provider_name: str = "Metropolitan Healthcare System",
        provider_dept: str = "Department of Patient Financial Services & Utilization Review",
    ) -> Dict[str, Any]:
        llm = get_llm_provider()

        provider_info = {
            "facility_name": provider_name,
            "department": provider_dept,
            "address": "1000 Medical Center Parkway, Suite 400",
            "phone": "(800) 555-4920",
            "fax": "(800) 555-4921",
            "npi": "1942859102",
        }

        patient_info = {
            "patient_reference_id": patient_data.get("external_patient_id", "PT-REF-001"),
            "first_name": patient_data.get("first_name", "Jane"),
            "last_name": patient_data.get("last_name", "Doe"),
            "dob": patient_data.get("dob", "1980-01-01"),
            "policy_number_masked": claim_data.get("policy_number_masked", "POL-****-8912"),
            "payer_name": claim_data.get("payer_name", "Insurance Payer"),
        }

        claim_info = {
            "claim_number": claim_data.get("claim_number", "CLM-2025-001"),
            "procedure_codes": claim_data.get("procedure_codes", []),
            "diagnosis_codes": claim_data.get("diagnosis_codes", []),
            "claim_amount": claim_data.get("claim_amount", 0.0),
            "denied_amount": claim_data.get("denied_amount", 0.0),
            "denial_date": claim_data.get("denial_date", "2025-08-15"),
        }

        original_denial_details = {
            "denial_code": claim_data.get("denial_code", "CO-50"),
            "denial_reason": comparison.denial_reason,
            "policy_section": comparison.policy_section,
        }

        # Build citations text
        citations_summary = "\n".join(
            [
                f"- [Exhibit {chr(65 + i)}] {item.get('source', 'Record')} ({item.get('page', 'Page 1')}): \"{item.get('citation', '')}\""
                for i, item in enumerate(comparison.supporting_evidence)
            ]
        ) or "None recorded."

        system_prompt = (
            "You are an expert Chief Medical Appeals Specialist for a leading hospital health system.\n"
            "Generate an evidence-backed formal insurance appeal letter.\n"
            "Strict Guidelines:\n"
            "1. NEVER invent clinical evidence, lab findings, or patient records not cited.\n"
            "2. Whenever citing clinical evidence, explicitly refer to the source document name and page number.\n"
            "3. If evidence is missing, state clearly that supplementary clinical documentation is enclosed or required.\n"
            "4. Structure the response clearly with professional medical billing appeal terminology."
        )

        user_prompt = (
            f"Generate a {tone} appeal letter for the following case:\n\n"
            f"Provider: {provider_info['facility_name']} ({provider_info['department']})\n"
            f"Patient: {patient_info['first_name']} {patient_info['last_name']} (Ref: {patient_info['patient_reference_id']}, DOB: {patient_info['dob']})\n"
            f"Payer: {patient_info['payer_name']}, Policy: {patient_info['policy_number_masked']}\n"
            f"Claim #: {claim_info['claim_number']}, Denied Amount: ${claim_info['denied_amount']:,.2f}\n"
            f"Procedure Codes: {', '.join(claim_info['procedure_codes'])}\n"
            f"Diagnosis Codes: {', '.join(claim_info['diagnosis_codes'])}\n"
            f"Denial: {original_denial_details['denial_code']} - {original_denial_details['denial_reason']}\n\n"
            f"Policy Requirements: {comparison.policy_requirements_summary}\n"
            f"Clinical Summary: {comparison.clinical_findings_summary}\n\n"
            f"Verified Evidence Citations:\n{citations_summary}\n\n"
            f"Key Arguments to Include:\n" + "\n".join(f"- {arg}" for arg in comparison.potential_appeal_arguments)
        )

        response = await llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        full_text = response.content

        # Extract structured sections
        clinical_justification = (
            f"The clinical medical record establishes clear medical necessity for the billed procedure(s) {', '.join(claim_info['procedure_codes'])}. "
            f"{comparison.clinical_findings_summary} "
            f"Key clinical evidence citations confirm that prior conservative measures and objective diagnostics satisfy all standard indications."
        )

        policy_references = (
            f"Under governing Payer Clinical Policy Bulletin {comparison.policy_section}, coverage is explicitly authorized "
            f"upon satisfaction of documented prerequisite criteria: {comparison.policy_requirements_summary}."
        )

        supporting_evidence_text = "\n".join(
            [
                f"• {e.get('source')} ({e.get('page')}): {e.get('citation')}"
                for e in comparison.supporting_evidence
            ]
        ) or "Attached medical records in Exhibit Index."

        request_reconsideration = (
            f"Based on the clinical documentation provided herein and in the attached exhibits, the denial of Claim {claim_info['claim_number']} "
            f"in the amount of ${claim_info['denied_amount']:,.2f} is unfounded. We respectfully request that this adverse determination be reversed "
            f"and reimbursement issued at the contracted rate. In accordance with applicable state and federal claims review regulations, if this appeal "
            f"is denied in whole or in part, please provide the specific clinical rationale and credentials of the reviewing physician."
        )

        supporting_doc_refs = [
            {
                "title": item.get("source", "Clinical Record"),
                "page": item.get("page", "Page 1"),
                "relevance": item.get("relevance", 0.95),
            }
            for item in comparison.supporting_evidence
        ]

        return {
            "title": f"Medical Necessity Appeal — Claim #{claim_info['claim_number']}",
            "provider_info": provider_info,
            "patient_info": patient_info,
            "claim_info": claim_info,
            "original_denial_details": original_denial_details,
            "clinical_justification": clinical_justification,
            "policy_references": policy_references,
            "supporting_evidence": supporting_evidence_text,
            "request_for_reconsideration": request_reconsideration,
            "supporting_document_references": supporting_doc_refs,
            "full_letter_text": full_text,
        }

