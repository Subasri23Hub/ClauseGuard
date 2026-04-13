"""
parser.py — Safely parse the structured JSON response from the LLM.
Handles common issues like markdown code fences, trailing commas, etc.
"""

import json
import re
from typing import Dict, Any, Tuple

# Keys we expect in a valid analysis response
REQUIRED_KEYS = {
    "risk_score",
    "risk_level",
    "financial_risks",
    "privacy_risks",
    "unfair_clauses",
    "auto_renewal_risks",
    "refund_cancellation_issues",
    "data_sharing_concerns",
    "plain_english_summary",
    "final_verdict",
    "important_clauses_to_review",
}

DEFAULT_RESPONSE: Dict[str, Any] = {
    "risk_score": 0,
    "risk_level": "Unknown",
    "financial_risks": [],
    "privacy_risks": [],
    "unfair_clauses": [],
    "auto_renewal_risks": [],
    "refund_cancellation_issues": [],
    "data_sharing_concerns": [],
    "plain_english_summary": "Analysis could not be parsed.",
    "final_verdict": "Unknown",
    "important_clauses_to_review": [],
}


def _clean_raw_text(raw: str) -> str:
    """Strip markdown fences and leading/trailing whitespace."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def parse_analysis(raw_response: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse LLM response into a structured analysis dict.
    Returns (analysis_dict, error_message).
    error_message is empty on success.
    """
    if not raw_response or not raw_response.strip():
        return DEFAULT_RESPONSE.copy(), "The model returned an empty response."

    cleaned = _clean_raw_text(raw_response)

    # Try to find the first JSON object in the response
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return DEFAULT_RESPONSE.copy(), f"Failed to parse JSON from model response: {e}"

    # Validate and fill missing keys with safe defaults
    result = DEFAULT_RESPONSE.copy()
    for key in REQUIRED_KEYS:
        if key in data:
            result[key] = data[key]

    # Coerce risk_score to int within [0, 100]
    try:
        result["risk_score"] = max(0, min(100, int(result["risk_score"])))
    except (ValueError, TypeError):
        result["risk_score"] = 0

    # Ensure list fields are actually lists
    list_fields = [
        "financial_risks", "privacy_risks", "unfair_clauses",
        "auto_renewal_risks", "refund_cancellation_issues",
        "data_sharing_concerns", "important_clauses_to_review",
    ]
    for field in list_fields:
        if not isinstance(result[field], list):
            result[field] = [str(result[field])] if result[field] else []

    return result, ""
