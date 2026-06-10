"""Resume2Offer AI Streamlit application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from agents import CoachAgent, GapAgent, MatchAgent, PredictorAgent, ScoutAgent
from components.dashboard import inject_global_css, render_full_dashboard, render_hero
from utils.llm import LLMClient
from utils.pdf_parser import PDFParseError, extract_text_from_upload


BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
SAMPLE_RESUME_PATH = ASSETS_DIR / "sample_resume.txt"
SAMPLE_JD_PATH = ASSETS_DIR / "sample_job_description.txt"


def load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def initialize_state() -> None:
    defaults = {
        "resume_text": "",
        "jd_text": "",
        "analysis": None,
        "last_error": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def run_analysis(resume_text: str, jd_text: str) -> dict[str, Any]:
    llm = LLMClient()
    scout_agent = ScoutAgent(llm)
    match_agent = MatchAgent(llm)
    gap_agent = GapAgent(llm)
    predictor_agent = PredictorAgent(llm)
    coach_agent = CoachAgent(llm)

    with st.status("Running multi-agent reasoning workflow", expanded=True) as status:
        st.write("Scout Agent is extracting candidate facts.")
        scout = scout_agent.run(resume_text)

        st.write("Match Agent is comparing resume evidence to the job description.")
        match = match_agent.run(resume_text, jd_text, scout)

        st.write("Gap Agent is prioritizing missing requirements.")
        gap = gap_agent.run(jd_text, match)

        st.write("Predictor Agent is forecasting interview questions.")
        predictor = predictor_agent.run(jd_text, scout, match, gap)

        st.write("Coach Agent is creating the ATS and preparation sprint plan.")
        coach = coach_agent.run(resume_text, jd_text, scout, match, gap, predictor)

        status.update(label="Multi-agent reasoning complete", state="complete", expanded=False)

    return {
        "scout": scout,
        "match": match,
        "gap": gap,
        "predictor": predictor,
        "coach": coach,
    }


def render_sidebar(llm: LLMClient) -> str:
    with st.sidebar:
        st.markdown("## Resume2Offer AI")
        st.caption("Multi-agent resume, JD, ATS, and interview readiness analysis.")
        page = st.radio("Navigation", ["Home", "Dashboard", "Sample Data"], label_visibility="collapsed")
        st.divider()

        mode = llm.provider.title() if llm.is_configured else "Deterministic fallback"
        st.metric("Reasoning Mode", mode)
        st.caption("Set OPENAI_API_KEY or GEMINI_API_KEY to enable model-generated reasoning.")

        if st.button("Load Sample Data", use_container_width=True):
            st.session_state["resume_text"] = load_text(SAMPLE_RESUME_PATH)
            st.session_state["jd_text"] = load_text(SAMPLE_JD_PATH)
            st.session_state["last_error"] = ""
            st.toast("Sample resume and job description loaded.")

        if st.session_state.get("analysis") and st.button("Clear Analysis", use_container_width=True):
            st.session_state["analysis"] = None
            st.session_state["last_error"] = ""
            st.toast("Analysis cleared.")

    return page


def render_home() -> None:
    render_hero()
    st.markdown("### Input Workspace")

    upload_col, jd_col = st.columns(2)
    with upload_col:
        resume_file = st.file_uploader("Upload Resume", type=["pdf", "txt", "md"], key="resume_upload")
        st.text_area(
            "Resume Text",
            key="resume_text",
            height=280,
            placeholder="Paste resume text here if you are not uploading a PDF.",
        )

    with jd_col:
        jd_file = st.file_uploader("Upload Job Description", type=["pdf", "txt", "md"], key="jd_upload")
        st.text_area(
            "Job Description",
            key="jd_text",
            height=280,
            placeholder="Paste the target job description here.",
        )

    action_col, secondary_col = st.columns([0.28, 0.72])
    with action_col:
        analyze = st.button("Analyze", use_container_width=True)
    with secondary_col:
        st.caption("The workflow runs Scout, Match, Gap, Predictor, and Coach agents in sequence.")

    if analyze:
        try:
            resume_text = _resolve_input_text(resume_file, st.session_state["resume_text"], "resume")
            jd_text = _resolve_input_text(jd_file, st.session_state["jd_text"], "job description")
            _validate_inputs(resume_text, jd_text)
            st.session_state["analysis"] = run_analysis(resume_text, jd_text)
            st.session_state["last_error"] = ""
        except (ValueError, PDFParseError) as exc:
            st.session_state["last_error"] = str(exc)
            st.error(str(exc))
        except Exception as exc:  # pragma: no cover - UI-level safety net
            st.session_state["last_error"] = f"Analysis failed: {exc}"
            st.error(st.session_state["last_error"])

    if st.session_state.get("last_error"):
        st.error(st.session_state["last_error"])

    if st.session_state.get("analysis"):
        render_full_dashboard(st.session_state["analysis"])


def render_dashboard_page() -> None:
    if not st.session_state.get("analysis"):
        st.info("Run an analysis from the Home page or load sample data first.")
        return
    render_full_dashboard(st.session_state["analysis"])


def render_sample_data() -> None:
    st.markdown("## Mock Sample Data")
    st.caption("Use this built-in resume and job description to test the full workflow.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Sample Resume")
        st.text_area("Sample Resume", value=load_text(SAMPLE_RESUME_PATH), height=520, label_visibility="collapsed")
    with col2:
        st.markdown("### Sample Job Description")
        st.text_area("Sample Job Description", value=load_text(SAMPLE_JD_PATH), height=520, label_visibility="collapsed")
    if st.button("Analyze Sample Data", use_container_width=True):
        resume_text = load_text(SAMPLE_RESUME_PATH)
        jd_text = load_text(SAMPLE_JD_PATH)
        st.session_state["resume_text"] = resume_text
        st.session_state["jd_text"] = jd_text
        st.session_state["analysis"] = run_analysis(resume_text, jd_text)
        st.session_state["last_error"] = ""


def _resolve_input_text(uploaded_file, pasted_text: str, label: str) -> str:
    if uploaded_file is not None:
        text = extract_text_from_upload(uploaded_file)
        if text.strip():
            return text.strip()
        raise ValueError(f"The uploaded {label} did not contain extractable text.")
    return (pasted_text or "").strip()


def _validate_inputs(resume_text: str, jd_text: str) -> None:
    if len(resume_text) < 120:
        raise ValueError("Please provide a resume with enough detail for analysis.")
    if len(jd_text) < 120:
        raise ValueError("Please provide a job description with enough detail for analysis.")


def main() -> None:
    load_environment()
    st.set_page_config(
        page_title="Resume2Offer AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_css()
    initialize_state()
    llm = LLMClient()
    page = render_sidebar(llm)

    if page == "Home":
        render_home()
    elif page == "Dashboard":
        render_dashboard_page()
    else:
        render_sample_data()


if __name__ == "__main__":
    main()
