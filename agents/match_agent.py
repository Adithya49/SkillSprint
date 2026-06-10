"""Match Agent: compares resume profile against the job description."""

from __future__ import annotations

import json
from typing import Any

from utils.jd_parser import parse_job_description
from utils.llm import LLMClient
from utils.scoring import calculate_match_score


MATCH_SYSTEM_PROMPT = """
You are the Match Agent in Resume2Offer AI.
Compare a candidate profile with a job description.
Return only valid JSON. Every score must include explainable reasoning.
Be specific, fair, and do not invent resume evidence.
"""


class MatchAgent:
    name = "Match Agent"
    purpose = "Compare resume against job description with explainable scoring."

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(self, resume_text: str, jd_text: str, candidate_profile: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback_match(resume_text, jd_text, candidate_profile)
        prompt = f"""
Return a JSON object with this exact schema:
{{
  "match_score": 0,
  "matching_skills": ["skill"],
  "missing_skills": ["skill"],
  "required_skills": ["skill"],
  "experience_alignment": {{
    "candidate_years": 0,
    "required_years": 0,
    "score": 0,
    "summary": "clear explanation"
  }},
  "reasoning": [
    {{"signal": "Python matches", "impact": 15, "type": "positive"}},
    {{"signal": "Docker missing", "impact": -7, "type": "negative"}}
  ],
  "why_this_score": "short paragraph explaining the score"
}}

Candidate profile:
{json.dumps(candidate_profile, indent=2)[:7000]}

Job description:
{jd_text[:9000]}
"""
        result = self.llm.generate_json(MATCH_SYSTEM_PROMPT, prompt, fallback)
        data = _coerce_match(result.data, fallback)
        data["_meta"] = {
            "agent": self.name,
            "used_llm": result.used_llm,
            "provider": result.provider,
            "error": result.error,
        }
        return data

    def _fallback_match(self, resume_text: str, jd_text: str, candidate_profile: dict[str, Any]) -> dict[str, Any]:
        score = calculate_match_score(resume_text, jd_text, candidate_profile.get("skills", []))
        jd = parse_job_description(jd_text)
        matching = score["matching_skills"]
        missing = score["missing_skills"]
        if matching and missing:
            why = f"The resume matches {len(matching)} important skills but still misses {len(missing)} JD skills."
        elif matching:
            why = "The resume has strong direct overlap with the job description's required skills."
        else:
            why = "The resume has limited explicit overlap with the role requirements and needs stronger keyword alignment."
        return {
            **score,
            "job_title": jd["title"],
            "why_this_score": why,
        }


def _coerce_match(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    output = dict(fallback)
    output["match_score"] = _bounded_int(data.get("match_score", fallback["match_score"]))
    for key in ("matching_skills", "missing_skills", "required_skills"):
        if isinstance(data.get(key), list):
            output[key] = [str(item).strip() for item in data[key] if str(item).strip()]
    if isinstance(data.get("experience_alignment"), dict):
        output["experience_alignment"] = {
            **fallback["experience_alignment"],
            **data["experience_alignment"],
        }
    if isinstance(data.get("reasoning"), list):
        output["reasoning"] = [_coerce_reason(reason) for reason in data["reasoning"] if isinstance(reason, dict)]
    if isinstance(data.get("why_this_score"), str):
        output["why_this_score"] = data["why_this_score"]
    return output


def _bounded_int(value: Any) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return 0


def _coerce_reason(reason: dict[str, Any]) -> dict[str, Any]:
    impact = reason.get("impact", 0)
    try:
        impact = int(round(float(impact)))
    except (TypeError, ValueError):
        impact = 0
    return {
        "signal": str(reason.get("signal", "Scoring signal")),
        "impact": impact,
        "type": "negative" if str(reason.get("type", "")).lower() == "negative" or impact < 0 else "positive",
    }

