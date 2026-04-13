"""
Terms & Conditions Risk Scanner
================================
A production-style Streamlit app that analyses T&C documents for hidden risks.

HOW TO RUN
----------
1. Copy .env.example → .env and fill in your API keys.
2. pip install -r requirements.txt
3. streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

from utils.extractors import extract_text_from_pdf
from utils.prompts import SYSTEM_PROMPT, build_analysis_prompt
from utils.llm_client import analyze_with_llm
from utils.parser import parse_analysis

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClauseGuard - T&C Risk Scanner",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base */
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }

/* Header */
.app-header { text-align: center; padding: 2rem 1rem 1rem 1rem; }
.app-title {
    font-size: 2.4rem; font-weight: 800; letter-spacing: -0.5px;
    background: linear-gradient(135deg, #1a73e8 0%, #6c47ff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.app-subtitle { color: #6b7280; font-size: 1.05rem; margin-bottom: 0.5rem; }

/* Score card */
.score-card {
    border-radius: 16px; padding: 2rem 2.5rem;
    display: flex; align-items: center; gap: 2rem;
    margin-bottom: 1.5rem;
}
.score-low    { background: linear-gradient(135deg, #d1fae5, #a7f3d0); border: 1.5px solid #6ee7b7; }
.score-medium { background: linear-gradient(135deg, #fef3c7, #fde68a); border: 1.5px solid #fbbf24; }
.score-high   { background: linear-gradient(135deg, #fee2e2, #fecaca); border: 1.5px solid #f87171; }
.score-number { font-size: 3.5rem; font-weight: 900; line-height: 1; }
.score-low    .score-number { color: #065f46; }
.score-medium .score-number { color: #92400e; }
.score-high   .score-number { color: #7f1d1d; }
.score-label { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.2rem; }
.score-verdict { font-size: 0.95rem; opacity: 0.85; }

/* Section cards */
.risk-section {
    background: #f9fafb; border-radius: 12px;
    padding: 1.2rem 1.5rem; margin-bottom: 1rem;
    border: 1px solid #e5e7eb;
}
.risk-section h4 { margin: 0 0 0.6rem 0; font-size: 1rem; font-weight: 700; color: #111827; }
.risk-item {
    background: white; border-radius: 8px; padding: 0.55rem 0.9rem;
    margin-bottom: 0.4rem; font-size: 0.88rem; color: #374151;
    border-left: 3px solid #e5e7eb;
}
.risk-item-red    { border-left-color: #ef4444; }
.risk-item-orange { border-left-color: #f97316; }
.risk-item-yellow { border-left-color: #eab308; }
.risk-item-blue   { border-left-color: #3b82f6; }
.risk-item-purple { border-left-color: #8b5cf6; }
.no-risk { color: #6b7280; font-style: italic; font-size: 0.88rem; }

/* Verdict badge */
.verdict-badge {
    display: inline-block; padding: 0.45rem 1.2rem;
    border-radius: 999px; font-weight: 700; font-size: 0.95rem;
}
.verdict-proceed  { background:#d1fae5; color:#065f46; }
.verdict-caution  { background:#fef3c7; color:#92400e; }
.verdict-avoid    { background:#fee2e2; color:#7f1d1d; }

/* Summary box */
.summary-box {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 12px; padding: 1.2rem 1.5rem;
    color: #1e3a5f; font-size: 0.95rem; line-height: 1.7;
    margin-bottom: 1.2rem;
}

/* Divider */
.section-divider { border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Demo text ─────────────────────────────────────────────────────────────────
DEMO_TEXT = """TERMS OF SERVICE — SubscribeMax Pro

1. AUTOMATIC RENEWAL
Your subscription will automatically renew at the end of each billing cycle. 
We will charge the payment method on file 7 days before renewal. You must cancel 
at least 14 days before the renewal date to avoid charges. Cancellations take 
effect at the end of the current billing period; no pro-rated refunds are issued.

2. DATA COLLECTION AND SHARING
By using this service you consent to our collection of all usage data, browsing 
history within the app, device identifiers, location data, and any content you 
create. We may share this data with our advertising partners, analytics providers, 
and affiliated companies. We may also sell anonymised (but re-identifiable) data 
to third parties for research purposes.

3. PRICE CHANGES
We reserve the right to change subscription fees at any time with 7 days notice 
via email. Continued use of the service after the effective date constitutes 
acceptance of the new pricing.

4. LIMITATION OF LIABILITY
To the maximum extent permitted by law, SubscribeMax Pro's liability is limited 
to the amount you paid in the last 30 days, regardless of the nature of the claim.

5. DISPUTE RESOLUTION
All disputes must be resolved via binding arbitration in Delaware, USA. You waive 
your right to participate in class action lawsuits. Arbitration fees are shared 
equally between parties.

6. CONTENT LICENCE
You grant us a perpetual, irrevocable, worldwide, royalty-free licence to use, 
reproduce, modify, and distribute any content you upload or create within the service.

7. ACCOUNT TERMINATION
We may suspend or terminate your account at our sole discretion without notice 
or refund if we believe you have violated these terms in any way.
"""

# ── Session state defaults ────────────────────────────────────────────────────
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "input_text" not in st.session_state:
    st.session_state.input_text = ""


# ── Helper functions ──────────────────────────────────────────────────────────

def risk_color_class(score: int) -> str:
    if score <= 30:
        return "low"
    elif score <= 60:
        return "medium"
    return "high"


def verdict_class(verdict: str) -> str:
    v = verdict.lower()
    if "avoid" in v:
        return "verdict-avoid"
    if "caution" in v:
        return "verdict-caution"
    return "verdict-proceed"


def render_risk_list(items: list, accent: str = "red") -> None:
    if not items:
        st.markdown('<p class="no-risk">✓ None identified</p>', unsafe_allow_html=True)
        return
    for item in items:
        st.markdown(
            f'<div class="risk-item risk-item-{accent}">• {item}</div>',
            unsafe_allow_html=True,
        )


def build_markdown_report(result: dict, source_label: str = "Pasted text") -> str:
    """Build a downloadable markdown report from the analysis result."""
    lines = [
        "# Terms & Conditions Risk Analysis Report",
        f"**Source:** {source_label}",
        "",
        "---",
        "",
        f"## Overall Risk Score: {result['risk_score']} / 100  —  {result['risk_level']} Risk",
        f"**Final Verdict:** {result['final_verdict']}",
        "",
        "---",
        "",
        "## Plain-English Summary",
        result.get("plain_english_summary", ""),
        "",
        "## Financial Risks",
    ]
    for item in result.get("financial_risks", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "## Privacy Risks"]
    for item in result.get("privacy_risks", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "## Unfair / Hidden Clauses"]
    for item in result.get("unfair_clauses", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "## Auto-Renewal Risks"]
    for item in result.get("auto_renewal_risks", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "## Refund & Cancellation Issues"]
    for item in result.get("refund_cancellation_issues", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "## Data Sharing Concerns"]
    for item in result.get("data_sharing_concerns", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "## Important Clauses to Review"]
    for item in result.get("important_clauses_to_review", []) or ["None identified"]:
        lines.append(f"- {item}")
    lines += ["", "---", "_Generated by Terms & Conditions Risk Scanner_"]
    return "\n".join(lines)


def run_analysis(text: str) -> None:
    """Run the LLM analysis pipeline and store result in session state."""
    if not text or not text.strip():
        st.error("No text to analyse. Please provide some content first.")
        return

    with st.spinner("🔍 Analysing document… this may take 10–30 seconds"):
        user_prompt = build_analysis_prompt(text)
        raw, err = analyze_with_llm(SYSTEM_PROMPT, user_prompt, doc_length=len(text))

        if err:
            st.error(f"**LLM Error:** {err}")
            return

        result, parse_err = parse_analysis(raw)
        if parse_err:
            st.warning(f"⚠️ Parsing issue (partial result may be shown): {parse_err}")

        st.session_state.analysis_result = result


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="app-title">🔍 Terms &amp; Conditions Risk Scanner</div>
  <div class="app-subtitle">
    Paste or upload and instantly detect hidden financial, privacy, and cancellation risks in complex terms.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Input section ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown("### 📄 Input")
    tab1, tab2 = st.tabs(["✏️  Paste / Type", "📎  Upload PDF"])

    # ── Tab 1: Paste text ──────────────────────────────────────────────────
    with tab1:
        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            if st.button("📋 Load demo text", use_container_width=True):
                st.session_state.input_text = DEMO_TEXT
        with btn_col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.input_text = ""
                st.session_state.analysis_result = None

        typed_text = st.text_area(
            label="Paste your Terms & Conditions here",
            value=st.session_state.input_text,
            height=280,
            placeholder="Paste the full Terms & Conditions, Privacy Policy, or any legal agreement text here…",
            label_visibility="collapsed",
        )
        st.session_state.input_text = typed_text

        char_count = len(typed_text.strip())
        st.caption(f"{char_count:,} characters entered" + (" (will be truncated to 18,000)" if char_count > 18000 else ""))

        if st.button("🚀 Analyse Text", type="primary", use_container_width=True, key="btn_text"):
            run_analysis(typed_text)

    # ── Tab 2: Upload PDF ──────────────────────────────────────────────────
    with tab2:
        pdf_file = st.file_uploader(
            "Upload a PDF file", type=["pdf"],
            help="Upload the T&C document as a PDF. Text-based PDFs work best.",
        )
        if pdf_file:
            with st.spinner("Extracting text from PDF…"):
                pdf_text, pdf_err = extract_text_from_pdf(pdf_file.read())

            if pdf_err:
                st.error(f"❌ {pdf_err}")
            else:
                st.success(f"✅ Extracted {len(pdf_text):,} characters from PDF")
                with st.expander("👁️ Preview extracted text"):
                    st.text(pdf_text[:3000] + ("…" if len(pdf_text) > 3000 else ""))

                if st.button("🚀 Analyse PDF", type="primary", use_container_width=True, key="btn_pdf"):
                    run_analysis(pdf_text)


# ── Right panel: tips / status ────────────────────────────────────────────────
with col_right:
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. **Paste** your T&C text or **upload** a PDF.
    2. Click **Analyse** — the scanner sends your text to an AI model for legal risk analysis.
    3. Review the **Risk Score**, structured findings, and the **Final Verdict**.
    4. **Download** the full report as a Markdown file.

    ---
    **What we detect:**
    - 💰 Financial traps & hidden fees
    - 🔒 Privacy & data sharing risks
    - 🔄 Auto-renewal / subscription tricks
    - ❌ No-refund / hard-cancel policies
    - 📜 One-sided or unfair clauses
    - 🤝 Data sold to third parties
    """)

    st.markdown("---")
    provider = os.getenv("LLM_PROVIDER", "gemini").upper()
    tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    st.markdown(f"**Provider:** `{provider}`")
    st.markdown(f"**LangSmith tracing:** {'✅ Enabled' if tracing else '⬜ Disabled'}")


# ── Results section ───────────────────────────────────────────────────────────
st.markdown("---")

if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    score = result["risk_score"]
    level = result["risk_level"]
    verdict = result["final_verdict"]
    color = risk_color_class(score)

    st.markdown("## 📊 Analysis Results")

    # Score card
    st.markdown(f"""
    <div class="score-card score-{color}">
      <div>
        <div class="score-number">{score}</div>
        <div style="font-size:0.8rem; opacity:0.7; margin-top:2px;">out of 100</div>
      </div>
      <div>
        <div class="score-label">{level} Risk</div>
        <div class="score-verdict">
          Verdict: <span style="font-weight:700">{verdict}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Plain English Summary
    st.markdown("### 📝 Plain-English Summary")
    st.markdown(
        f'<div class="summary-box">{result.get("plain_english_summary", "")}</div>',
        unsafe_allow_html=True,
    )

    # Risk breakdown
    st.markdown("### 🔍 Detailed Risk Breakdown")

    r1, r2 = st.columns(2, gap="medium")

    with r1:
        with st.expander("💰 Financial Risks", expanded=True):
            render_risk_list(result.get("financial_risks"), "red")

        with st.expander("🔒 Privacy Risks", expanded=True):
            render_risk_list(result.get("privacy_risks"), "orange")

        with st.expander("📜 Unfair / Hidden Clauses", expanded=True):
            render_risk_list(result.get("unfair_clauses"), "red")

    with r2:
        with st.expander("🔄 Auto-Renewal Risks", expanded=True):
            render_risk_list(result.get("auto_renewal_risks"), "yellow")

        with st.expander("❌ Refund & Cancellation Issues", expanded=True):
            render_risk_list(result.get("refund_cancellation_issues"), "orange")

        with st.expander("🤝 Data Sharing Concerns", expanded=True):
            render_risk_list(result.get("data_sharing_concerns"), "purple")

    # Important clauses
    st.markdown("### 📌 Important Clauses to Review")
    clauses = result.get("important_clauses_to_review", [])
    if clauses:
        for clause in clauses:
            st.markdown(
                f'<div class="risk-item risk-item-blue">🔖 {clause}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<p class="no-risk">✓ No specific clauses flagged for review</p>', unsafe_allow_html=True)

    # Download button
    st.markdown("---")
    report_md = build_markdown_report(result)
    st.download_button(
        label="⬇️ Download Full Report (.md)",
        data=report_md,
        file_name="tc_risk_report.md",
        mime="text/markdown",
        use_container_width=False,
    )

    if st.button("🔄 Reset & Analyse Another Document"):
        st.session_state.analysis_result = None
        st.session_state.input_text = ""
        st.rerun()

else:
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem; color:#9ca3af;">
        <div style="font-size:3rem; margin-bottom:1rem;">🔍</div>
        <div style="font-size:1.1rem; font-weight:600; color:#6b7280;">No analysis yet</div>
        <div style="font-size:0.9rem; margin-top:0.4rem;">
            Enter your Terms &amp; Conditions text above and click <strong>Analyse</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#9ca3af;font-size:0.8rem;">'
    'Terms &amp; Conditions Risk Scanner · Powered by Gemini + LangSmith · '
    'Not a substitute for qualified legal advice.'
    '</div>',
    unsafe_allow_html=True,
)