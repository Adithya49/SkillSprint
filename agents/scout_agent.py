"""Scout Agent: extracts candidate information from a resume."""

from __future__ import annotations

import json
import re
from typing import Any

from utils.llm import LLMClient
from utils.scoring import extract_skills, normalize_text, split_candidate_lines


SCOUT_SYSTEM_PROMPT = """
You are the Scout Agent in Resume2Offer AI.
Extract candidate facts from a resume and return only valid JSON.
Do not invent credentials. If a field is not present, return an empty list.
Keep items concise and recruiter-readable.
"""


class ScoutAgent:
    name = "Scout Agent"
    purpose = "Extract candidate information into structured JSON."

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(self, resume_text: str) -> dict[str, Any]:
        fallback = self._fallback_extract(resume_text)
        prompt = f"""
Return a JSON object with this exact schema:
{{
  "candidate_summary": "one paragraph summary",
  "skills": ["skill"],
  "experience": ["experience bullet"],
  "education": ["education item"],
  "certifications": ["certification item"],
  "projects": ["project item"],
  "signals": {{
    "leadership": ["evidence"],
    "metrics": ["evidence"],
    "domains": ["domain"]
  }}
}}

Resume:
{resume_text[:9000]}
"""
        result = self.llm.generate_json(SCOUT_SYSTEM_PROMPT, prompt, fallback)
        data = _coerce_profile(result.data, fallback)
        data["_meta"] = {
            "agent": self.name,
            "used_llm": result.used_llm,
            "provider": result.provider,
            "error": result.error,
        }
        return data

    def _fallback_extract(self, resume_text: str) -> dict[str, Any]:
        text = normalize_text(resume_text)
        skills = extract_skills(text)
        lines = split_candidate_lines(resume_text, limit=24)
        education = _matching_lines(resume_text, r"\b(B\.?Tech|M\.?Tech|B\.?S\.?|M\.?S\.?|MBA|Bachelor|Master|PhD|University|College|Institute)\b")
        certifications = _matching_lines(resume_text, r"\b(Certified|Certification|Certificate|AWS|Azure|Google Cloud|Coursera|Udemy)\b")
        projects = _matching_lines(resume_text, r"\b(Project|Built|Designed|Developed|Implemented|Deployed|GitHub|Launched)\b")
        experience = [
            line
            for line in lines
            if re.search(r"\b(Engineer|Developer|Intern|Analyst|Manager|Led|Built|Designed|Improved|Automated)\b", line, re.I)
        ][:8]

        if not experience:
            experience = lines[:5]

        domains = _domains_from_text(text)
        metric_signals = [line for line in lines if re.search(r"\d+%?|\$|x\b", line)]
        leadership = [line for line in lines if re.search(r"\b(led|owned|mentored|managed|coordinated)\b", line, re.I)]

        return {
            "candidate_summary": _summary_from_signals(skills, experience, domains),
            "skills": skills,
            "experience": experience[:8],
            "education": education[:4],
            "certifications": certifications[:4],
            "projects": projects[:6],
            "signals": {
                "leadership": leadership[:4],
                "metrics": metric_signals[:5],
                "domains": domains,
            },
        }


def _matching_lines(text: str, pattern: str) -> list[str]:
    lines = split_candidate_lines(text, limit=60)
    return [line for line in lines if re.search(pattern, line, re.I)]


def _domains_from_text(text: str) -> list[str]:
    domain_terms = {
        "AI/ML": r"\b(ai|machine learning|ml|nlp|llm|model)\b",
        "Data": r"\b(data|analytics|etl|dashboard|sql)\b",
        "Backend": r"\b(api|backend|server|microservice)\b",
        "Cloud": r"\b(cloud|aws|azure|gcp|docker|kubernetes)\b",
        "Product": r"\b(product|user|metrics|roadmap)\b",
    }
    return [label for label, pattern in domain_terms.items() if re.search(pattern, text, re.I)]


def _summary_from_signals(skills: list[str], experience: list[str], domains: list[str]) -> str:
    skill_text = ", ".join(skills[:6]) if skills else "general technical skills"
    domain_text = ", ".join(domains[:3]) if domains else "software delivery"
    exp_text = "with evidence of hands-on project or work experience" if experience else "with limited explicit experience detail"
    return f"Candidate profile emphasizes {skill_text} across {domain_text}, {exp_text}."


def _coerce_profile(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    output = dict(fallback)
    for key in ("candidate_summary",):
        if isinstance(data.get(key), str):
            output[key] = data[key]
    for key in ("skills", "experience", "education", "certifications", "projects"):
        if isinstance(data.get(key), list):
            output[key] = [str(item).strip() for item in data[key] if str(item).strip()]
    signals = data.get("signals")
    if isinstance(signals, dict):
        output["signals"] = {
            "leadership": _listify(signals.get("leadership")),
            "metrics": _listify(signals.get("metrics")),
            "domains": _listify(signals.get("domains")),
        }
    return json.loads(json.dumps(output))


def _listify(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]

