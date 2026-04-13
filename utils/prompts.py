"""
prompts.py — Prompt templates for the T&C Risk Scanner.
"""

SYSTEM_PROMPT = """You are a senior legal-risk analyst specializing in consumer protection.
Your job is to read Terms & Conditions or Privacy Policy documents and produce a structured 
risk assessment that helps everyday users understand what they are agreeing to.

RULES:
- Use plain, simple English. Avoid legalese in your explanations.
- Be honest about ambiguity — if a clause is unclear, say so explicitly.
- Never fabricate legal certainty; flag things as "potentially risky" rather than making 
  definitive legal claims.
- Identify predatory, one-sided, or hidden clauses that disadvantage the user.
- Be concise but thorough in each section.
- Return ONLY a valid JSON object — no markdown fences, no preamble, no trailing text.

RISK SCORE GUIDE:
  0–30   → Low risk (standard, fair terms)
  31–60  → Medium risk (some concerning clauses, proceed carefully)
  61–100 → High risk (multiple red flags, significant user disadvantage)

FINAL VERDICT OPTIONS:
  "Proceed"                    → Terms are reasonable, risks are minimal
  "Proceed with caution"       → Notable risks exist; read the flagged sections carefully
  "Avoid unless necessary"     → Heavily one-sided, predatory, or unusually risky terms
"""

def build_analysis_prompt(text: str, max_chars: int = 18000) -> str:
    """
    Build the full user-turn prompt for T&C analysis.
    Truncates safely if the text is too large.
    """
    truncated = text[:max_chars]
    truncation_note = ""
    if len(text) > max_chars:
        truncation_note = (
            "\n[NOTE: The document was truncated to the first "
            f"{max_chars} characters due to length constraints. "
            "Analyse the available portion only and flag that the full document was not reviewed.]\n"
        )

    return f"""Analyse the following Terms & Conditions / legal document and return a JSON object 
that strictly follows the schema below. Do not include anything outside the JSON.
{truncation_note}
--- DOCUMENT START ---
{truncated}
--- DOCUMENT END ---

Required JSON schema:
{{
  "risk_score": <integer 0-100>,
  "risk_level": "<Low|Medium|High>",
  "financial_risks": [<list of concise strings>],
  "privacy_risks": [<list of concise strings>],
  "unfair_clauses": [<list of concise strings>],
  "auto_renewal_risks": [<list of concise strings>],
  "refund_cancellation_issues": [<list of concise strings>],
  "data_sharing_concerns": [<list of concise strings>],
  "plain_english_summary": "<2-4 sentence plain-language overview>",
  "final_verdict": "<Proceed|Proceed with caution|Avoid unless necessary>",
  "important_clauses_to_review": [<list of short clause descriptions worth re-reading>]
}}
"""
