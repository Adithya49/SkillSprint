"""Plotly charts used by the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PLOT_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"
FONT_COLOR = "#F3F7FB"
GRID_COLOR = "rgba(148, 163, 184, 0.16)"
PRIMARY = "#4FD1C5"
SECONDARY = "#8B9CFB"
ACCENT = "#F4B860"
DANGER = "#FF7A90"
SUCCESS = "#63E6BE"


def _theme_palette() -> dict[str, str]:
    theme_base = str(st.get_option("theme.base") or "dark").lower()
    is_light = theme_base == "light"
    if is_light:
        return {
            "font": "#0F172A",
            "title": "#334155",
            "tick": "#475569",
            "gauge_bg": "rgba(241, 245, 249, 0.98)",
            "panel": "rgba(255, 255, 255, 0.96)",
            "grid": "rgba(100, 116, 139, 0.18)",
            "present": PRIMARY,
            "missing": DANGER,
            "high": DANGER,
            "medium": ACCENT,
            "low": PRIMARY,
            "stage": [SECONDARY, PRIMARY],
            "type": [PRIMARY, DANGER],
        }
    return {
        "font": FONT_COLOR,
        "title": "#AAB7C7",
        "tick": "#AAB7C7",
        "gauge_bg": "rgba(14, 21, 35, 0.92)",
        "panel": "rgba(0,0,0,0)",
        "grid": GRID_COLOR,
        "present": PRIMARY,
        "missing": DANGER,
        "high": DANGER,
        "medium": ACCENT,
        "low": PRIMARY,
        "stage": [SECONDARY, PRIMARY],
        "type": [PRIMARY, DANGER],
    }


def gauge_chart(value: int, title: str, color: str = "#35D0BA") -> go.Figure:
    palette = _theme_palette()
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%", "font": {"size": 30, "color": palette["font"]}},
            title={"text": title, "font": {"size": 15, "color": palette["title"]}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": palette["tick"], "tickfont": {"color": palette["title"]}},
                "bar": {"color": color, "thickness": 0.28},
                "bgcolor": palette["gauge_bg"],
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "rgba(255, 122, 144, 0.18)"},
                    {"range": [50, 75], "color": "rgba(244, 184, 96, 0.16)"},
                    {"range": [75, 100], "color": "rgba(79, 209, 197, 0.16)"},
                ],
            },
        )
    )
    fig.update_layout(
        height=250,
        margin=dict(l=18, r=18, t=45, b=8),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=palette["font"],
    )
    return fig


def skills_bar_chart(match_report: dict) -> go.Figure:
    palette = _theme_palette()
    required = match_report.get("required_skills", [])
    matching = set(match_report.get("matching_skills", []))
    if not required:
        required = match_report.get("matching_skills", []) + match_report.get("missing_skills", [])

    rows = [
        {
            "Skill": skill,
            "Status": "Present" if skill in matching else "Missing",
            "Value": 1,
        }
        for skill in required
    ]
    if not rows:
        rows = [{"Skill": "No explicit skills detected", "Status": "Missing", "Value": 1}]
    df = pd.DataFrame(rows)
    fig = px.bar(
        df,
        x="Value",
        y="Skill",
        color="Status",
        orientation="h",
        color_discrete_map={"Present": palette["present"], "Missing": palette["missing"]},
        text="Status",
    )
    fig.update_traces(marker_line_width=0, textposition="inside", insidetextanchor="middle")
    fig.update_layout(
        height=max(280, min(520, 36 * len(df) + 120)),
        showlegend=True,
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(tickfont={"color": palette["font"]}),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=48, b=15),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=palette["font"],
    )
    return fig


def gap_priority_chart(gap_report: dict) -> go.Figure:
    palette = _theme_palette()
    rows = [
        {"Priority": "High", "Count": len(gap_report.get("high_priority_gaps", []))},
        {"Priority": "Medium", "Count": len(gap_report.get("medium_priority_gaps", []))},
        {"Priority": "Low", "Count": len(gap_report.get("low_priority_gaps", []))},
    ]
    df = pd.DataFrame(rows)
    fig = px.bar(
        df,
        x="Priority",
        y="Count",
        color="Priority",
        color_discrete_map={"High": palette["high"], "Medium": palette["medium"], "Low": palette["low"]},
        text="Count",
    )
    fig.update_traces(marker_line_width=0, textposition="outside")
    fig.update_layout(
        height=280,
        showlegend=False,
        xaxis_title="",
        yaxis_title="Gap count",
        yaxis=dict(gridcolor=palette["grid"], rangemode="tozero"),
        margin=dict(l=10, r=10, t=25, b=20),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=palette["font"],
    )
    return fig


def readiness_delta_chart(current: int, after: int) -> go.Figure:
    palette = _theme_palette()
    df = pd.DataFrame(
        [
            {"Stage": "Current Readiness", "Score": current},
            {"Stage": "After Sprint", "Score": after},
        ]
    )
    fig = px.bar(
        df,
        x="Stage",
        y="Score",
        color="Stage",
        color_discrete_sequence=palette["stage"],
        text="Score",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside", marker_line_width=0)
    fig.update_layout(
        height=280,
        showlegend=False,
        yaxis=dict(range=[0, 105], gridcolor=palette["grid"], title=""),
        xaxis=dict(title=""),
        margin=dict(l=10, r=10, t=25, b=25),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=palette["font"],
    )
    return fig


def keyword_coverage_chart(present: list[str], missing: list[str]) -> go.Figure:
    palette = _theme_palette()
    df = pd.DataFrame(
        [
            {"Type": "Covered Keywords", "Count": len(present)},
            {"Type": "Missing Keywords", "Count": len(missing)},
        ]
    )
    fig = px.bar(
        df,
        x="Type",
        y="Count",
        color="Type",
        color_discrete_sequence=palette["type"],
        text="Count",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        height=260,
        showlegend=False,
        yaxis=dict(gridcolor=palette["grid"], rangemode="tozero", title=""),
        xaxis=dict(title=""),
        margin=dict(l=10, r=10, t=22, b=25),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=palette["font"],
    )
    return fig

