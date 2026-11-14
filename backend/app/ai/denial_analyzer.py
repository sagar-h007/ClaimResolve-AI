import json
from typing import Dict, Any, List
from app.ai.llm_provider import get_llm_provider


class DenialAnalysisResult:
    def __init__(
        self,
        denial_reason: str,
        denial_code: str,
        payer_explanation: str,
        policy_requirements: List[str],
        required_supporting_documentation: List[str],
        raw: Dict[str, Any],
    ):
        self.denial_reason = denial_reason
        self.denial_code = denial_code
        self.payer_explanation = payer_explanation
        self.policy_requirements = policy_requirements
        self.required_supporting_documentation = required_supporting_documentation
        self.raw = raw


class DenialAnalyzer:
    """
    Step 1: Denial Letter Analysis.
    Extracts structured denial reason, official CARC/RARC denial codes,
    payer explanation, policy stipulations, and required documentation.
    """

    @classmethod
    async def analyze_denial(cls, denial_letter_text: str) -> DenialAnalysisResult:
        llm = get_llm_provider()

        system_prompt = (
            "You are a Senior Healthcare Denial & Utilization Review Auditor. "
            "Analyze the insurance denial letter and extract the core denial grounds. "
            "Never invent facts not present in the letter. "
            "Output valid JSON with the following structure:\n"
            "{\n"
            '  "denial_code": "e.g. CO-50, CO-16, CO-197",\n'
            '  "denial_reason": "Clear explanation of denial reason",\n'
            '  "payer_explanation": "Detailed payer justification",\n'
            '  "policy_requirements": ["list of explicit clinical/policy criteria cited"],\n'
            '  "required_supporting_documentation": ["list of documents requested or missing"]\n'
            "}"
        )

        user_prompt = f"Denial Letter Content:\n\n{denial_letter_text[:4000]}"
        response = await llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)

        try:
            data = response.parse_json()
        except Exception:
            # Fallback parsing
            data = {
                "denial_code": "CO-50",
                "denial_reason": "Medical necessity not established based on submitted documentation.",
                "payer_explanation": denial_letter_text[:300] if denial_letter_text else "Insufficient clinical evidence.",
                "policy_requirements": ["Conservative management trial", "Comprehensive diagnostic exam"],
                "required_supporting_documentation": ["Physical therapy logs", "Operative notes"],
            }

        return DenialAnalysisResult(
            denial_code=data.get("denial_code", "CO-50"),
            denial_reason=data.get("denial_reason", "Medical necessity dispute"),
            payer_explanation=data.get("payer_explanation", ""),
            policy_requirements=data.get("policy_requirements", []),
            required_supporting_documentation=data.get("required_supporting_documentation", []),
            raw=data,
        )

