"""Gap Agent: identifies missing requirements and remediation advice."""

from __future__ import annotations

import json
from typing import Any

from utils.llm import LLMClient
from utils.scoring import skill_category


GAP_SYSTEM_PROMPT = """
You are the Gap Agent in Resume2Offer AI.
Classify missing requirements into high, medium, and low priority.
Return only valid JSON. Each gap needs description, impact_level, and recommendation.
Prioritize gaps that are explicitly required by the JD or central to the target role.
"""


class GapAgent:
    name = "Gap Agent"
    purpose = "Identify missing requirements by priority."

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(self, jd_text: str, match_report: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback_gaps(match_report)
        prompt = f"""
Return a JSON object with this exact schema:
{{
  "high_priority_gaps": [
    {{"skill": "Docker", "description": "why it matters", "impact_level": "High", "recommendation": "action"}}
  ],
  "medium_priority_gaps": [
    {{"skill": "Skill", "description": "why it matters", "impact_level": "Medium", "recommendation": "action"}}
  ],
  "low_priority_gaps": [
    {{"skill": "Skill", "description": "why it matters", "impact_level": "Low", "recommendation": "action"}}
  ],
  "overall_gap_risk": "Low | Medium | High",
  "gap_summary": "short explanation"
}}

Match report:
{json.dumps(match_report, indent=2)[:7000]}

Job description:
{jd_text[:9000]}
"""
        result = self.llm.generate_json(GAP_SYSTEM_PROMPT, prompt, fallback)
        data = _coerce_gaps(result.data, fallback)
        data["_meta"] = {
            "agent": self.name,
            "used_llm": result.used_llm,
            "provider": result.provider,
            "error": result.error,
        }
        return data

    def _fallback_gaps(self, match_report: dict[str, Any]) -> dict[str, Any]:
        missing = match_report.get("missing_skills", [])
        high_categories = {"AI", "Backend", "Data", "Architecture", "Cloud"}
        high: list[dict[str, str]] = []
        medium: list[dict[str, str]] = []
        low: list[dict[str, str]] = []

        for skill in missing:
            category = skill_category(skill)
            item = {
                "skill": skill,
                "description": f"{skill} is requested or implied by the role and is not clearly evidenced in the resume.",
                "impact_level": "High" if category in high_categories else "Medium",
                "recommendation": _recommendation_for(skill, category),
            }
            if category in high_categories and len(high) < 5:
                high.append(item)
            elif category in {"DevOps", "Frontend", "Quality"} and len(medium) < 6:
                item["impact_level"] = "Medium"
                medium.append(item)
            else:
                item["impact_level"] = "Low"
                low.append(item)

        if not high and medium:
            high.append({**medium.pop(0), "impact_level": "High"})

        total_missing = len(missing)
        total_required = len(match_report.get("required_skills", []))
        risk = "Low"
        if total_required and total_missing / total_required >= 0.45:
            risk = "High"
        elif total_required and total_missing / total_required >= 0.22:
            risk = "Medium"

        return {
            "high_priority_gaps": high,
            "medium_priority_gaps": medium,
            "low_priority_gaps": low,
            "overall_gap_risk": risk,
            "gap_summary": _gap_summary(total_missing, total_required, risk),
        }


def _recommendation_for(skill: str, category: str) -> str:
    if category == "AI":
        return f"Build one compact demo using {skill}, document the approach, and prepare tradeoff talking points."
    if category == "Cloud":
        return f"Add a deployment story that shows how you would use {skill} in production."
    if category == "DevOps":
        return f"Practice a small workflow with {skill} and add a concise resume bullet if relevant."
    if category == "Data":
        return f"Prepare a project example that uses {skill} to produce measurable business or model impact."
    return f"Study the core concepts of {skill} and map them to one project in your resume."


def _gap_summary(missing_count: int, required_count: int, risk: str) -> str:
    if missing_count == 0:
        return "No major explicit skill gaps were found from the job description."
    return f"{missing_count} of {required_count or 'the'} required skills need stronger evidence, creating a {risk.lower()} gap risk."


def _coerce_gaps(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    output = dict(fallback)
    for key in ("high_priority_gaps", "medium_priority_gaps", "low_priority_gaps"):
        if isinstance(data.get(key), list):
            output[key] = [_coerce_gap(item) for item in data[key] if isinstance(item, dict)]
    if data.get("overall_gap_risk") in {"Low", "Medium", "High"}:
        output["overall_gap_risk"] = data["overall_gap_risk"]
    if isinstance(data.get("gap_summary"), str):
        output["gap_summary"] = data["gap_summary"]
    return output


def _coerce_gap(item: dict[str, Any]) -> dict[str, str]:
    impact = str(item.get("impact_level", "Medium")).title()
    if impact not in {"Low", "Medium", "High"}:
        impact = "Medium"
    skill = str(item.get("skill", "Gap"))
    return {
        "skill": skill,
        "description": str(item.get("description", f"{skill} needs stronger evidence.")),
        "impact_level": impact,
        "recommendation": str(item.get("recommendation", f"Prepare a focused example for {skill}.")),
    }

