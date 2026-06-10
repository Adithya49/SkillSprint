# Resume2Offer AI

**From Resume to Offer Through Intelligent Reasoning**

Resume2Offer AI is a Streamlit MVP that analyzes a candidate resume against a job description and produces an interview-winning strategy through a multi-agent reasoning workflow.

## Features

- Scout Agent extracts skills, experience, education, certifications, projects, and evidence signals.
- Match Agent generates an explainable resume-to-JD match score.
- Gap Agent prioritizes missing skills into high, medium, and low risk.
- Predictor Agent creates technical, behavioral, system design, and role-specific interview questions.
- Coach Agent generates ATS guidance, resume bullet rewrites, readiness scoring, and a 7-day sprint plan.
- Plotly KPI gauges and skill/gap charts.
- Built-in sample resume and job description for demo testing.
- Runs with deterministic fallback when no API key is configured.
- Supports both OpenAI and Gemini through the shared LLM wrapper.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Add your OpenAI key to `.env`:

```bash
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

Or use Gemini:

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-google-genai-key
GEMINI_MODEL=gemini-2.5-flash
```

Without a provider key, the application still runs using deterministic extraction and scoring logic for hackathon demos.

## Project Structure

```text
app.py
agents/
  scout_agent.py
  match_agent.py
  gap_agent.py
  predictor_agent.py
  coach_agent.py
utils/
  pdf_parser.py
  jd_parser.py
  llm.py
  scoring.py
components/
  dashboard.py
  charts.py
assets/
  sample_resume.txt
  sample_job_description.txt
requirements.txt
.env.example
README.md
```

## LLM Provider Swap

The LLM integration is isolated in `utils/llm.py`. The current implementation supports OpenAI and Gemini. Set `LLM_PROVIDER=openai` with `OPENAI_API_KEY`, or `LLM_PROVIDER=gemini` with `GEMINI_API_KEY`.

## Run

```bash
streamlit run app.py
```

Open the local URL Streamlit prints in the terminal, then load sample data or upload your own resume and job description.

