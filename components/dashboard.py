"""Reusable Streamlit dashboard sections."""

from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from components.charts import (
    gap_priority_chart,
    gauge_chart,
    keyword_coverage_chart,
    readiness_delta_chart,
    skills_bar_chart,
)


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0A1220;
            --panel: rgba(15, 23, 42, 0.74);
            --panel-strong: rgba(13, 20, 34, 0.96);
            --surface: rgba(8, 13, 22, 0.88);
            --surface-soft: rgba(15, 23, 42, 0.82);
            --surface-muted: rgba(15, 23, 42, 0.68);
            --control-bg: linear-gradient(135deg, rgba(19, 29, 44, 0.98), rgba(12, 22, 34, 0.98));
            --control-hover: linear-gradient(135deg, rgba(79, 209, 197, 0.14), rgba(139, 156, 251, 0.12));
            --input-bg: rgba(11, 18, 32, 0.96);
            --hero-bg: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(11, 18, 32, 0.88));
            --sidebar-bg: linear-gradient(180deg, rgba(7, 12, 21, 0.98), rgba(10, 16, 28, 0.98));
            --header-bg: rgba(8, 16, 28, 0.85);
            --metric-bg: linear-gradient(180deg, rgba(17, 24, 39, 0.82), rgba(12, 20, 34, 0.92));
            --alert-bg: rgba(12, 20, 34, 0.88);
            --pill-bg: rgba(15, 23, 42, 0.78);
            --button-text: #F3F7FB;
            --control-text: #F3F7FB;
            --border: rgba(148, 163, 184, 0.16);
            --text: #F3F7FB;
            --muted: #9AA7B8;
            --teal: #4FD1C5;
            --blue: #8B9CFB;
            --amber: #F4B860;
            --red: #FF7A90;
            --ink: #0B1220;
        }

        [data-theme="dark"],
        html[data-theme="dark"],
        body[data-theme="dark"],
        .stApp[data-theme="dark"] {
            --bg: #0A1220;
            --panel: rgba(15, 23, 42, 0.74);
            --panel-strong: rgba(13, 20, 34, 0.96);
            --surface: rgba(8, 13, 22, 0.88);
            --surface-soft: rgba(15, 23, 42, 0.82);
            --surface-muted: rgba(15, 23, 42, 0.68);
            --control-bg: linear-gradient(135deg, rgba(19, 29, 44, 0.98), rgba(12, 22, 34, 0.98));
            --control-hover: linear-gradient(135deg, rgba(79, 209, 197, 0.14), rgba(139, 156, 251, 0.12));
            --input-bg: rgba(11, 18, 32, 0.96);
            --hero-bg: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(11, 18, 32, 0.88));
            --sidebar-bg: linear-gradient(180deg, rgba(7, 12, 21, 0.98), rgba(10, 16, 28, 0.98));
            --header-bg: rgba(8, 16, 28, 0.85);
            --metric-bg: linear-gradient(180deg, rgba(17, 24, 39, 0.82), rgba(12, 20, 34, 0.92));
            --alert-bg: rgba(12, 20, 34, 0.88);
            --pill-bg: rgba(15, 23, 42, 0.78);
            --button-text: #F3F7FB;
            --control-text: #F3F7FB;
            --border: rgba(148, 163, 184, 0.16);
            --text: #F3F7FB;
            --muted: #9AA7B8;
            --teal: #4FD1C5;
            --blue: #8B9CFB;
            --amber: #F4B860;
            --red: #FF7A90;
            --ink: #0B1220;
        }

        [data-theme="light"],
        html[data-theme="light"],
        body[data-theme="light"],
        .stApp[data-theme="light"] {
            --bg: #F5F8FC;
            --panel: rgba(255, 255, 255, 0.82);
            --panel-strong: rgba(255, 255, 255, 0.96);
            --surface: rgba(255, 255, 255, 0.94);
            --surface-soft: rgba(241, 245, 249, 0.96);
            --surface-muted: rgba(233, 239, 246, 0.92);
            --control-bg: linear-gradient(180deg, rgba(249, 251, 253, 0.98), rgba(235, 241, 246, 0.98));
            --control-hover: linear-gradient(180deg, rgba(228, 245, 241, 0.98), rgba(220, 234, 255, 0.98));
            --input-bg: rgba(255, 255, 255, 0.98);
            --hero-bg: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(241, 247, 252, 0.98));
            --sidebar-bg: linear-gradient(180deg, rgba(247, 250, 253, 0.98), rgba(238, 243, 248, 0.98));
            --header-bg: rgba(255, 255, 255, 0.90);
            --metric-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 248, 252, 0.98));
            --alert-bg: rgba(248, 250, 252, 0.98);
            --pill-bg: rgba(241, 245, 249, 0.92);
            --button-text: #0F172A;
            --control-text: #0F172A;
            --border: rgba(148, 163, 184, 0.28);
            --text: #0F172A;
            --muted: #56657A;
            --teal: #0F9B8E;
            --blue: #556EFA;
            --amber: #B66A00;
            --red: #B91C1C;
            --ink: #0F172A;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(79, 209, 197, 0.12), transparent 24%),
                radial-gradient(circle at top right, rgba(139, 156, 251, 0.10), transparent 22%),
                var(--bg);
            color: var(--text);
        }

        .stApp,
        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlockContainer"],
        section.main,
        section[data-testid="stSidebar"] {
            background-color: var(--bg) !important;
            background: var(--bg) !important;
            color: var(--text) !important;
        }

        [data-theme="dark"],
        html[data-theme="dark"],
        body[data-theme="dark"],
        .stApp[data-theme="dark"] {
            color-scheme: dark;
        }

        [data-theme="light"],
        html[data-theme="light"],
        body[data-theme="light"],
        .stApp[data-theme="light"] {
            color-scheme: light;
        }

        .stApp, html, body {
            color: var(--text);
        }

        body {
            background-color: var(--bg) !important;
            background: var(--bg) !important;
        }

        [data-testid="stAppViewContainer"] {
            background-image:
                radial-gradient(circle at top left, rgba(79, 209, 197, 0.12), transparent 24%),
                radial-gradient(circle at top right, rgba(139, 156, 251, 0.10), transparent 22%);
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-color: var(--bg) !important;
        }

        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stMain"],
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stAppViewContainer"] > .main > div,
        [data-testid="stAppViewContainer"] > .main > div > div {
            background-color: transparent !important;
            background: transparent !important;
        }

        .main {
            background: transparent !important;
        }

        [data-testid="stHeader"] {
            background: var(--header-bg);
            border-bottom: 1px solid rgba(148, 163, 184, 0.10);
        }

        [data-testid="stToolbar"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1280px;
        }

        .main .block-container {
            background: transparent;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text);
            letter-spacing: -0.02em;
        }

        p, li, label, span, div {
            color: inherit;
        }

        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span,
        .stCaption,
        .stText,
        [data-testid="stMarkdownContainer"] {
            color: var(--text);
        }

        .stMarkdown, .stCaption {
            color: var(--muted);
        }

        div[data-testid="stFileUploader"] section {
            background: var(--surface-soft);
            border: 1px dashed rgba(79, 209, 197, 0.34);
            border-radius: 14px;
            padding: 0.35rem;
        }

        div[data-testid="stFileUploader"] button,
        div[data-testid="stFileUploader"] [role="button"] {
            background: var(--control-bg) !important;
            color: var(--control-text) !important;
            border: 1px solid rgba(79, 209, 197, 0.35) !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }

        div[data-testid="stFileUploader"] button:hover,
        div[data-testid="stFileUploader"] [role="button"]:hover {
            border-color: rgba(79, 209, 197, 0.55) !important;
            background: var(--control-hover) !important;
        }

        div[data-testid="stFileUploader"] svg,
        div[data-testid="stFileUploader"] button svg {
            color: var(--teal) !important;
        }

        textarea, input {
            background-color: var(--input-bg) !important;
            color: var(--text) !important;
            border-color: rgba(148, 163, 184, 0.24) !important;
            border-radius: 12px !important;
        }

        textarea::placeholder, input::placeholder {
            color: rgba(154, 167, 184, 0.72) !important;
        }

        .stButton > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 12px !important;
            border: 1px solid rgba(79, 209, 197, 0.34) !important;
            color: var(--button-text) !important;
            background: var(--control-bg) !important;
            font-weight: 700 !important;
            min-height: 2.8rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24) !important;
        }

        .stButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            border-color: rgba(79, 209, 197, 0.58) !important;
            background: var(--control-hover) !important;
            color: var(--button-text) !important;
            box-shadow: 0 16px 36px rgba(79, 209, 197, 0.16) !important;
        }

        .stButton > button:focus,
        .stButton > button:active {
            border-color: rgba(79, 209, 197, 0.75) !important;
            color: var(--button-text) !important;
        }

        .hero {
            border: 1px solid rgba(148, 163, 184, 0.18);
            background:
                radial-gradient(circle at top right, rgba(79, 209, 197, 0.10), transparent 26%),
                var(--hero-bg),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.025) 0 1px, transparent 1px 48px);
            border-radius: 16px;
            padding: clamp(28px, 5vw, 56px);
            margin-bottom: 1.2rem;
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.36);
        }

        .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.3fr) minmax(260px, 0.7fr);
            gap: 28px;
            align-items: center;
        }

        .hero h1 {
            font-size: clamp(2.35rem, 6vw, 5.1rem);
            line-height: 0.95;
            margin: 0 0 16px 0;
        }

        .hero .tagline {
            color: var(--teal);
            font-size: clamp(1.05rem, 2vw, 1.45rem);
            font-weight: 700;
            margin-bottom: 14px;
        }

        .hero .description {
            color: #B8C4D6;
            max-width: 760px;
            font-size: 1.05rem;
            line-height: 1.65;
        }

        .agent-visual {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            background: var(--surface);
            padding: 18px;
        }

        .agent-node {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.13);
            padding: 12px 0;
            color: var(--text);
            font-size: 0.92rem;
        }

        .agent-node:last-child {
            border-bottom: 0;
        }

        .agent-chip {
            color: #061014;
            background: var(--teal);
            border-radius: 999px;
            padding: 2px 9px;
            font-size: 0.72rem;
            font-weight: 800;
            white-space: nowrap;
            align-self: center;
        }

        .section-title {
            margin: 2.2rem 0 0.65rem 0;
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text);
        }

        .subtle {
            color: var(--muted);
            font-size: 0.94rem;
        }

        .kpi-card {
            border: 1px solid var(--border);
            background: var(--metric-bg);
            border-radius: 16px;
            padding: 16px 16px 14px;
            min-height: 132px;
        }

        .kpi-label {
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0;
            font-weight: 750;
            margin-bottom: 10px;
        }

        .kpi-value {
            color: var(--text);
            font-size: clamp(1.55rem, 3vw, 2.35rem);
            line-height: 1;
            font-weight: 850;
            margin-bottom: 10px;
        }

        .kpi-subtext {
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.4;
        }

        .accent-line {
            height: 3px;
            width: 56px;
            border-radius: 999px;
            margin-top: 13px;
        }

        .info-panel {
            border: 1px solid var(--border);
            background: var(--metric-bg);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .reason-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            padding: 10px 0;
        }

        .reason-row:last-child {
            border-bottom: 0;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            padding: 4px 9px;
            margin: 3px 4px 3px 0;
            color: var(--text);
            background: var(--pill-bg);
            font-size: 0.82rem;
        }

        .difficulty {
            display: inline-flex;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: 0.74rem;
            font-weight: 800;
            color: #071118;
            background: #F6C85F;
        }

        .before-after {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .ba-box {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px;
            background: var(--surface-muted);
            min-height: 108px;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-testid="stSelectbox"] [role="button"],
        div[data-testid="stMultiSelect"] [role="button"] {
            background-color: var(--input-bg) !important;
            color: var(--text) !important;
            border-color: rgba(148, 163, 184, 0.24) !important;
            border-radius: 12px !important;
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] span {
            color: var(--text) !important;
        }

        div[data-testid="stRadio"] [role="radio"] {
            background: var(--input-bg) !important;
            border-color: rgba(148, 163, 184, 0.28) !important;
        }

        div[data-testid="metric-container"] {
            background: var(--metric-bg);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 16px;
            padding: 14px 16px;
        }

        div[data-testid="metric-container"] label,
        div[data-testid="metric-container"] div,
        div[data-testid="metric-container"] span {
            color: var(--text) !important;
        }

        .stAlert {
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: var(--alert-bg);
            color: var(--text);
        }

        .ba-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 8px;
        }

        @media (max-width: 900px) {
            .hero-grid, .before-after {
                grid-template-columns: 1fr;
            }
            .hero h1 {
                font-size: clamp(2.25rem, 13vw, 3.6rem);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-grid">
                <div>
                    <h1>Resume2Offer AI</h1>
                    <div class="tagline">From Resume to Offer Through Intelligent Reasoning</div>
                    <p class="description">
                        Upload your Resume and Job Description to receive AI-powered insights,
                        interview preparation strategies, and hiring readiness analysis.
                    </p>
                </div>
                <div class="agent-visual">
                    <div class="agent-node"><strong>Scout Agent</strong><span class="agent-chip">EXTRACT</span></div>
                    <div class="agent-node"><strong>Match Agent</strong><span class="agent-chip">SCORE</span></div>
                    <div class="agent-node"><strong>Gap Agent</strong><span class="agent-chip">PRIORITIZE</span></div>
                    <div class="agent-node"><strong>Predictor Agent</strong><span class="agent-chip">FORECAST</span></div>
                    <div class="agent-node"><strong>Coach Agent</strong><span class="agent-chip">PLAN</span></div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<div class="subtle">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>{subtitle_html}', unsafe_allow_html=True)


def render_kpi_cards(analysis: dict[str, Any]) -> None:
    match = analysis["match"]
    coach = analysis["coach"]
    kpis = [
        ("Match Score", f"{match['match_score']}%", "Resume to JD fit", "#35D0BA"),
        ("ATS Score", f"{coach['ats_score']}%", "Keyword and structure quality", "#7C93FF"),
        ("Readiness Score", f"{coach['readiness_score']}%", "Current interview readiness", "#A7F3D0"),
        ("Skill Gap Risk", coach["skill_gap_risk"], "Risk from missing requirements", "#F6C85F"),
        ("Technical Alignment", f"{coach['technical_alignment']}%", "Skills coverage and depth", "#FF8FA3"),
    ]
    columns = st.columns(5)
    for column, (label, value, subtext, color) in zip(columns, kpis):
        with column:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{html.escape(label)}</div>
                    <div class="kpi-value">{html.escape(str(value))}</div>
                    <div class="kpi-subtext">{html.escape(subtext)}</div>
                    <div class="accent-line" style="background:{color};"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_agent_status(analysis: dict[str, Any]) -> None:
    render_section_title("Agent Workflow", "Each agent produces a structured artifact for the next reasoning step.")
    rows = []
    for key, label in (
        ("scout", "Scout Agent"),
        ("match", "Match Agent"),
        ("gap", "Gap Agent"),
        ("predictor", "Predictor Agent"),
        ("coach", "Coach Agent"),
    ):
        meta = analysis[key].get("_meta", {})
        provider = str(meta.get("provider", "")).strip().lower()
        if meta.get("used_llm") and provider in {"openai", "gemini", "google", "google-genai"}:
            mode = "OpenAI" if provider == "openai" else "Gemini"
        else:
            mode = "Deterministic fallback"
        rows.append(
            {
                "Agent": label,
                "Artifact": _artifact_for(key),
                "Mode": mode,
                "Status": "Complete" if not meta.get("error") or not meta.get("used_llm") else "Fallback used",
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_score_charts(analysis: dict[str, Any]) -> None:
    coach = analysis["coach"]
    match = analysis["match"]
    improvement = coach["estimated_readiness_improvement"]
    columns = st.columns(3)
    with columns[0]:
        st.plotly_chart(gauge_chart(match["match_score"], "Match Score", "#35D0BA"), use_container_width=True)
    with columns[1]:
        st.plotly_chart(gauge_chart(coach["ats_score"], "ATS Score", "#7C93FF"), use_container_width=True)
    with columns[2]:
        st.plotly_chart(gauge_chart(coach["readiness_score"], "Readiness", "#A7F3D0"), use_container_width=True)
    columns = st.columns(2)
    with columns[0]:
        st.plotly_chart(skills_bar_chart(match), use_container_width=True)
    with columns[1]:
        st.plotly_chart(readiness_delta_chart(improvement["current_readiness"], improvement["after_sprint"]), use_container_width=True)


def render_match_report(match_report: dict[str, Any]) -> None:
    render_section_title("Match Reasoning", match_report.get("why_this_score", "Explainable score breakdown."))
    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        st.markdown('<div class="info-panel">', unsafe_allow_html=True)
        st.markdown(f"**Experience Alignment:** {html.escape(match_report['experience_alignment'].get('summary', ''))}")
        st.markdown("**Why This Score?**")
        for reason in match_report.get("reasoning", []):
            color = "#35D0BA" if reason.get("type") == "positive" else "#FF6B6B"
            impact = reason.get("impact", 0)
            prefix = "+" if isinstance(impact, int) and impact > 0 else ""
            st.markdown(
                f"""
                <div class="reason-row">
                    <span>{html.escape(str(reason.get("signal", "Signal")))}</span>
                    <strong style="color:{color};">{prefix}{html.escape(str(impact))}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="info-panel">', unsafe_allow_html=True)
        st.markdown("**Matching Skills**")
        _render_pills(match_report.get("matching_skills", []), "#35D0BA")
        st.markdown("**Missing Skills**")
        _render_pills(match_report.get("missing_skills", []), "#FF6B6B")
        st.markdown("</div>", unsafe_allow_html=True)


def render_gap_analysis(gap_report: dict[str, Any]) -> None:
    render_section_title("Skill Gap Analysis", gap_report.get("gap_summary"))
    col1, col2 = st.columns([0.55, 0.45])
    with col1:
        for label, key in (
            ("High Priority Gaps", "high_priority_gaps"),
            ("Medium Priority Gaps", "medium_priority_gaps"),
            ("Low Priority Gaps", "low_priority_gaps"),
        ):
            gaps = gap_report.get(key, [])
            with st.expander(f"{label} ({len(gaps)})", expanded=key == "high_priority_gaps"):
                if not gaps:
                    st.caption("No gaps in this priority band.")
                for gap in gaps:
                    st.markdown(f"**{gap.get('skill', 'Gap')}**")
                    st.write(gap.get("description", ""))
                    st.info(gap.get("recommendation", ""))
    with col2:
        st.plotly_chart(gap_priority_chart(gap_report), use_container_width=True)


def render_ats_section(coach: dict[str, Any]) -> None:
    render_section_title("ATS Optimization", "Keyword coverage, missing terms, and resume rewrite opportunities.")
    col1, col2 = st.columns([0.45, 0.55])
    with col1:
        st.plotly_chart(
            keyword_coverage_chart(
                coach.get("present_keywords", []),
                coach.get("missing_keywords", []),
            ),
            use_container_width=True,
        )
        st.progress(coach.get("keyword_coverage", 0) / 100, text=f"Keyword Coverage: {coach.get('keyword_coverage', 0)}%")
        st.markdown("**Missing Keywords**")
        _render_pills(coach.get("missing_keywords", []), "#FF6B6B")
    with col2:
        st.markdown("**Resume Improvement Suggestions**")
        for suggestion in coach.get("resume_improvement_suggestions", []):
            st.markdown(f"- {html.escape(suggestion)}")
        st.markdown("**Before vs After Bullet Improvements**")
        for pair in coach.get("before_after_bullets", []):
            st.markdown(
                f"""
                <div class="before-after">
                    <div class="ba-box">
                        <div class="ba-label">Before</div>
                        {html.escape(pair.get("before", ""))}
                    </div>
                    <div class="ba-box">
                        <div class="ba-label">After</div>
                        {html.escape(pair.get("after", ""))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_questions(question_report: dict[str, Any]) -> None:
    render_section_title("Predicted Interview Questions", "Generated from the resume, JD, match signals, and skill gaps.")
    tabs = st.tabs(["Technical", "Behavioral", "System Design", "Role Specific"])
    tab_map = [
        ("technical_questions", tabs[0]),
        ("behavioral_questions", tabs[1]),
        ("system_design_questions", tabs[2]),
        ("role_specific_questions", tabs[3]),
    ]
    for key, tab in tab_map:
        with tab:
            questions = question_report.get(key, [])
            if not questions:
                st.caption("No questions generated for this category.")
            for index, item in enumerate(questions, start=1):
                with st.expander(f"Q{index}. {item.get('question', 'Question')}", expanded=index == 1):
                    st.markdown(f'<span class="difficulty">{html.escape(item.get("difficulty", "Medium"))}</span>', unsafe_allow_html=True)
                    st.markdown("**Why interviewer asks it**")
                    st.write(item.get("why_interviewer_asks", ""))
                    st.markdown("**Expected answer approach**")
                    st.write(item.get("expected_answer_approach", ""))


def render_sprint_plan(coach: dict[str, Any]) -> None:
    render_section_title("Personalized Preparation Sprint", "A 7-day plan to increase interview readiness.")
    col1, col2 = st.columns([0.62, 0.38])
    with col1:
        for day in coach.get("sprint_plan", []):
            with st.expander(f"{day.get('day', 'Day')} - {day.get('theme', 'Preparation')}", expanded=day.get("day") == "Day 1"):
                for task in day.get("tasks", []):
                    st.markdown(f"- {html.escape(str(task))}")
    with col2:
        st.markdown('<div class="info-panel">', unsafe_allow_html=True)
        st.markdown("**Priority Tasks**")
        for task in coach.get("priority_tasks", []):
            st.markdown(f"- {html.escape(task)}")
        st.markdown("**Topics To Study**")
        _render_pills(coach.get("topics_to_study", []), "#7C93FF")
        st.markdown("**Projects To Showcase**")
        for project in coach.get("projects_to_showcase", []):
            st.markdown(f"- {html.escape(project)}")
        st.markdown("**Mock Interview Areas**")
        for area in coach.get("mock_interview_areas", [])[:5]:
            st.markdown(f"- {html.escape(area)}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_scout_json(scout_report: dict[str, Any]) -> None:
    render_section_title("Scout Agent Output", "Structured candidate profile extracted from the resume.")
    display = {key: value for key, value in scout_report.items() if key != "_meta"}
    st.json(display)


def render_full_dashboard(analysis: dict[str, Any]) -> None:
    render_kpi_cards(analysis)
    render_agent_status(analysis)
    render_section_title("Score Dashboard", "KPI gauges and role-fit visualizations.")
    render_score_charts(analysis)
    render_match_report(analysis["match"])
    render_gap_analysis(analysis["gap"])
    render_questions(analysis["predictor"])
    render_ats_section(analysis["coach"])
    render_sprint_plan(analysis["coach"])
    render_scout_json(analysis["scout"])


def _artifact_for(key: str) -> str:
    return {
        "scout": "Candidate JSON",
        "match": "Explainable score",
        "gap": "Prioritized gaps",
        "predictor": "Question forecast",
        "coach": "Sprint and ATS plan",
    }[key]


def _render_pills(items: list[str], color: str) -> None:
    if not items:
        st.caption("None detected.")
        return
    chips = "".join(
        f'<span class="pill" style="border-color:{color}55;">{html.escape(str(item))}</span>'
        for item in items
    )
    st.markdown(chips, unsafe_allow_html=True)
