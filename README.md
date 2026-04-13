# ClauseGuard AI

### Detect hidden risks in Terms & Conditions — instantly, clearly, intelligently.

---

## Overview

ClauseGuard AI is a production-style Streamlit application that analyzes Terms & Conditions documents and uncovers hidden financial, privacy, and legal risks using Large Language Models (LLMs).

It transforms complex legal text into structured insights, risk scores, and plain-English summaries, helping users make informed decisions before agreeing to any service.

---

## Key Features

► AI-powered risk analysis
Identifies hidden clauses, unfair conditions, and risky policies

► Risk score (0–100)
Quantifies the overall risk level of a document

► Plain-English summary
Simplifies complex legal language into clear explanations

► Detailed risk breakdown
Financial risks
Auto-renewal risks
Privacy risks
Refund and cancellation issues
Unfair or hidden clauses
Data sharing concerns

► Important clauses highlighted
Flags critical sections that require attention

► Downloadable report
Export the full analysis as a structured Markdown file

► LangSmith integration
Tracks LLM inputs, outputs, and performance for observability

---

## Tech Stack

► Python
► Streamlit
► Large Language Models (Gemini / OpenAI / Claude)
► LangSmith (Tracing and Observability)
► PDF Text Extraction

---

## Project Structure

```
ClauseGuard/
│
├── app.py
├── requirements.txt
├── .env
│
└── utils/
    ├── __init__.py
    ├── extractors.py
    ├── llm_client.py
    ├── parser.py
    ├── prompts.py
```

---

## Getting Started

### 1. Clone the repository

```
git clone https://github.com/your-username/clauseguard-ai.git
cd clauseguard-ai
```

### 2. Create virtual environment

```
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Setup environment variables

Create a `.env` file:

```
GOOGLE_API_KEY=your_google_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=clauseguard-ai
```

### 5. Run the application

```
streamlit run app.py
```

---

## How It Works

► User inputs Terms and Conditions text or uploads a PDF
► Text is processed and sent to an LLM
► LangSmith tracks request and response
► AI returns structured JSON analysis
► Results are displayed as a risk dashboard

---

## Use Cases

► Review subscription agreements
► Analyze SaaS product terms
► Detect hidden charges and auto-renewals
► Identify privacy and data sharing risks
► Simplify legal documents for everyday users

---

## Future Improvements

► Advanced clause highlighting within original text
► Multi-document comparison
► Support for additional document formats
► Improved risk scoring models

---

## Disclaimer

This tool provides AI-generated insights and is not a substitute for professional legal advice.

---

## Author

Subasri B - GenAI Intern @ Sourcesys Technologies
