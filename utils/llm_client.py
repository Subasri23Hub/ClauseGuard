"""
llm_client.py — LLM client with LangSmith tracing.

Primary provider: Google Gemini (gemini-2.5-flash)
Switch provider via LLM_PROVIDER env var: gemini | openai | anthropic

LangSmith wraps every call for full observability:
  - run name, tags, metadata captured per call
  - trace viewable at https://smith.langchain.com
"""

import os
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

# ── LangSmith setup ─────────────────────────────────────────────────────────

def _setup_langsmith():
    """Configure LangSmith environment variables."""
    api_key = os.getenv("LANGSMITH_API_KEY", "")
    tracing = os.getenv("LANGSMITH_TRACING", "false").lower()
    project = os.getenv("LANGSMITH_PROJECT", "tc-risk-scanner")

    if api_key and tracing == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        return True
    return False


_langsmith_enabled = _setup_langsmith()


# ── Provider implementations ────────────────────────────────────────────────

def _call_gemini(system_prompt: str, user_prompt: str) -> Tuple[str, str]:
    """Call Google Gemini via google-generativeai SDK."""
    try:
        import google.generativeai as genai
    except ImportError:
        return "", "google-generativeai is not installed. Run: pip install google-generativeai"

    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return "", "GOOGLE_API_KEY is not set in your .env file."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )
    response = model.generate_content(user_prompt)
    return response.text, ""


def _call_openai(system_prompt: str, user_prompt: str) -> Tuple[str, str]:
    """Call OpenAI GPT-4o."""
    try:
        from openai import OpenAI
    except ImportError:
        return "", "openai package is not installed. Run: pip install openai"

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return "", "OPENAI_API_KEY is not set in your .env file."

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content, ""


def _call_anthropic(system_prompt: str, user_prompt: str) -> Tuple[str, str]:
    """Call Anthropic Claude Sonnet."""
    try:
        import anthropic
    except ImportError:
        return "", "anthropic package is not installed. Run: pip install anthropic"

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "", "ANTHROPIC_API_KEY is not set in your .env file."

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text, ""


# ── LangSmith-traced dispatcher ─────────────────────────────────────────────

def analyze_with_llm(
    system_prompt: str,
    user_prompt: str,
    doc_length: int = 0,
) -> Tuple[str, str]:
    """
    Send prompts to the configured LLM provider.
    Wraps the call with a LangSmith trace when tracing is enabled.

    Returns (raw_response_text, error_message).
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    def _run_llm() -> Tuple[str, str]:
        if provider == "gemini":
            return _call_gemini(system_prompt, user_prompt)
        elif provider == "openai":
            return _call_openai(system_prompt, user_prompt)
        elif provider == "anthropic":
            return _call_anthropic(system_prompt, user_prompt)
        else:
            return "", f"Unknown LLM_PROVIDER '{provider}'. Choose: gemini | openai | anthropic"

    if _langsmith_enabled:
        try:
            from langsmith import traceable

            @traceable(
                run_type="llm",
                name="tc-risk-analysis",
                tags=["tc-scanner", provider],
                metadata={
                    "provider": provider,
                    "doc_length_chars": doc_length,
                    "project": os.getenv("LANGSMITH_PROJECT", "tc-risk-scanner"),
                },
            )
            def _traced_llm(sys_p: str, usr_p: str) -> Tuple[str, str]:
                return _run_llm()

            return _traced_llm(system_prompt, user_prompt)
        except Exception as trace_err:
            # Tracing failure should never block the actual LLM call
            print(f"[LangSmith] Tracing error (non-fatal): {trace_err}")
            return _run_llm()
    else:
        return _run_llm()
