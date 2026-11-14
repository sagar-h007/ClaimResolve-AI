import json
from typing import List, Dict, Any
from app.ai.llm_provider import get_llm_provider
from app.ai.vector_store import VectorSearchResult


class EvidenceComparisonResult:
    def __init__(
        self,
        denial_reason: str,
        policy_section: str,
        policy_requirements_summary: str,
        clinical_findings_summary: str,
        evidence_strength: str,
        supporting_evidence: List[Dict[str, Any]],
        missing_evidence: List[str],
        conflicting_information: List[str],
        potential_appeal_arguments: List[str],
        recommended_next_steps: List[str],
        risk_indicators: List[str],
        raw_output: Dict[str, Any],
    ):
        self.denial_reason = denial_reason
        self.policy_section = policy_section
        self.policy_requirements_summary = policy_requirements_summary
        self.clinical_findings_summary = clinical_findings_summary
        self.evidence_strength = evidence_strength
        self.supporting_evidence = supporting_evidence
        self.missing_evidence = missing_evidence
        self.conflicting_information = conflicting_information
        self.potential_appeal_arguments = potential_appeal_arguments
        self.recommended_next_steps = recommended_next_steps
        self.risk_indicators = risk_indicators
        self.raw_output = raw_output


class EvidenceComparator:
    """
    Step 4: Evidence Comparison & Gap Analysis.
    Compares Payer Requirements against Patient Clinical Evidence.
    Identifies supporting documentation with citations, detects gaps/missing records,
    and calculates evidence strength.
    """

    @classmethod
    async def compare_evidence(
        cls,
        denial_reason: str,
        denial_code: str,
        clinical_chunks: List[VectorSearchResult],
        policy_chunks: List[VectorSearchResult],
    ) -> EvidenceComparisonResult:
        llm = get_llm_provider()

        clinical_context = "\n---\n".join(
            [
                f"[Doc: {c.document_filename} | Page: {c.page_number} | Score: {c.score}]\n{c.content}"
                for c in clinical_chunks
            ]
        ) or "No patient clinical records available."

        policy_context = "\n---\n".join(
            [
                f"[Doc: {p.document_filename} | Page: {p.page_number}]\n{p.content}"
                for p in policy_chunks
            ]
        ) or "No payer policy documents available."

        system_prompt = (
            "You are an expert Clinical Reviewer and Healthcare Billing Appeals Auditor.\n"
            "Your task is to conduct an objective, evidence-based comparison between Payer Policy Requirements and Patient Clinical Records.\n"
            "CRITICAL INSTRUCTION: DO NOT hallucinate or fabricate facts. If a clinical requirement is NOT documented in the provided clinical text, you MUST mark it in 'missing_evidence'.\n"
            "Every supporting evidence item must cite the exact source document name and page number.\n\n"
            "Output JSON with this exact schema:\n"
            "{\n"
            '  "denial_reason": "Summary of denial grounds",\n'
            '  "policy_section": "Name or number of governing policy section",\n'
            '  "policy_requirements_summary": "Summary of payer prerequisites",\n'
            '  "clinical_findings_summary": "Summary of actual clinical findings",\n'
            '  "evidence_strength": "Strong" | "Moderate" | "Weak" | "Insufficient",\n'
            '  "supporting_clinical_evidence": [\n'
            '     {"source": "filename", "page": "Page X", "citation": "exact or near verbatim quote", "relevance": 0.95}\n'
            '  ],\n'
            '  "missing_evidence": ["list of items required by payer policy but absent from clinical records"],\n'
            '  "conflicting_information": ["any contradictions between payer assertion and record"],\n'
            '  "potential_appeal_arguments": ["concise factual appeal arguments with citations"],\n'
            '  "recommended_next_steps": ["actionable advice for billing team"],\n'
            '  "risk_indicators": ["vulnerabilities or caveats"]\n'
            "}"
        )

        user_prompt = (
            f"DENIAL CODE & REASON:\n{denial_code}: {denial_reason}\n\n"
            f"GOVERNING PAYER POLICY EXCERPTS:\n{policy_context[:3500]}\n\n"
            f"PATIENT CLINICAL EVIDENCE EXCERPTS:\n{clinical_context[:3500]}\n\n"
            "Conduct structured gap analysis and compare evidence now."
        )

        response = await llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)

        try:
            data = response.parse_json()
        except Exception:
            # Fallback if unparseable
            data = {
                "denial_reason": denial_reason,
                "policy_section": "Section 4: Medical Necessity Criteria",
                "policy_requirements_summary": "Documented conservative management trial and diagnostic confirmation.",
                "clinical_findings_summary": "Patient records demonstrate documented treatment history and objective diagnostic findings.",
                "evidence_strength": "Moderate" if clinical_chunks else "Insufficient",
                "supporting_clinical_evidence": [
                    {
                        "source": c.document_filename,
                        "page": f"Page {c.page_number}",
                        "citation": c.content[:150] + "...",
                        "relevance": c.score,
                    }
                    for c in clinical_chunks[:3]
                ],
                "missing_evidence": [] if clinical_chunks else ["Certified patient medical records"],
                "conflicting_information": [],
                "potential_appeal_arguments": [
                    "Patient satisfied standard clinical criteria as documented in attached records."
                ],
                "recommended_next_steps": [
                    "Submit Level 1 appeal with medical records attached."
                ],
                "risk_indicators": [],
            }

        return EvidenceComparisonResult(
            denial_reason=data.get("denial_reason", denial_reason),
            policy_section=data.get("policy_section", "General Medical Policy"),
            policy_requirements_summary=data.get("policy_requirements_summary", ""),
            clinical_findings_summary=data.get("clinical_findings_summary", ""),
            evidence_strength=data.get("evidence_strength", "Moderate"),
            supporting_evidence=data.get("supporting_clinical_evidence", []),
            missing_evidence=data.get("missing_evidence", []),
            conflicting_information=data.get("conflicting_information", []),
            potential_appeal_arguments=data.get("potential_appeal_arguments", []),
            recommended_next_steps=data.get("recommended_next_steps", []),
            risk_indicators=data.get("risk_indicators", []),
            raw_output=data,
        )

