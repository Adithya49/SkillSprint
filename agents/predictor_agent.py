"""Predictor Agent: generates likely interview questions."""

from __future__ import annotations

import json
from typing import Any

from utils.jd_parser import parse_job_description
from utils.llm import LLMClient


PREDICTOR_SYSTEM_PROMPT = """
You are the Predictor Agent in Resume2Offer AI.
Predict likely interview questions from the resume, JD, match report, and gaps.
Return only valid JSON. For every question include why it is asked, expected answer approach, and difficulty.
Make questions specific to the candidate and target role.
"""


class PredictorAgent:
    name = "Predictor Agent"
    purpose = "Predict likely interview questions and answer strategies."

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(
        self,
        jd_text: str,
        candidate_profile: dict[str, Any],
        match_report: dict[str, Any],
        gap_report: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = self._fallback_questions(jd_text, candidate_profile, match_report, gap_report)
        prompt = f"""
Return a JSON object with this exact schema:
{{
  "technical_questions": [
    {{"question": "...", "why_interviewer_asks": "...", "expected_answer_approach": "...", "difficulty": "Easy | Medium | Hard"}}
  ],
  "behavioral_questions": [],
  "system_design_questions": [],
  "role_specific_questions": []
}}

Candidate profile:
{json.dumps(candidate_profile, indent=2)[:5000]}

Match report:
{json.dumps(match_report, indent=2)[:5000]}

Gap report:
{json.dumps(gap_report, indent=2)[:5000]}

Job description:
{jd_text[:9000]}
"""
        result = self.llm.generate_json(PREDICTOR_SYSTEM_PROMPT, prompt, fallback)
        data = _coerce_questions(result.data, fallback)
        data["_meta"] = {
            "agent": self.name,
            "used_llm": result.used_llm,
            "provider": result.provider,
            "error": result.error,
        }
        return data

    def _fallback_questions(
        self,
        jd_text: str,
        candidate_profile: dict[str, Any],
        match_report: dict[str, Any],
        gap_report: dict[str, Any],
    ) -> dict[str, Any]:
        jd = parse_job_description(jd_text)
        matching = match_report.get("matching_skills", [])[:5]
        missing = match_report.get("missing_skills", [])[:4]
        projects = candidate_profile.get("projects", [])[:3]
        role = jd["title"]

        technical = [
            _question(
                f"Walk me through how you have used {skill} in a real project.",
                f"{skill} appears in both the resume and JD, so the interviewer will validate depth.",
                "Use a problem-action-result structure, mention design choices, and quantify impact where possible.",
                "Medium",
            )
            for skill in matching[:4]
        ]
        technical += [
            _question(
                f"The JD mentions {skill}. How would you get productive with it in the first 30 days?",
                f"{skill} is a gap, so the interviewer may test learning agility and risk.",
                "Acknowledge the gap, connect adjacent experience, and outline a concrete ramp-up plan.",
                "Hard",
            )
            for skill in missing[:3]
        ]
        if not technical:
            technical.append(
                _question(
                    "Which technical project best proves you can succeed in this role?",
                    "The resume needs a stronger bridge to the target role.",
                    "Select one relevant project, explain architecture, tradeoffs, and measurable outcome.",
                    "Medium",
                )
            )

        behavioral = [
            _question(
                "Tell me about a time you learned a new technical area quickly under pressure.",
                "The role requires adaptability and quick ramp-up.",
                "Use STAR format and end with what changed because of your work.",
                "Medium",
            ),
            _question(
                "Describe a time you received ambiguous requirements and turned them into a working solution.",
                "Hiring teams want evidence of ownership beyond task execution.",
                "Show how you clarified scope, made tradeoffs, communicated, and delivered.",
                "Medium",
            ),
            _question(
                "What is one technical decision you would make differently now?",
                "This tests judgment, self-awareness, and engineering maturity.",
                "Explain the original context, the lesson, and the improved decision framework.",
                "Hard",
            ),
        ]

        system_design = [
            _question(
                f"Design a scalable system for a core workflow in a {role}.",
                "The interviewer is checking architecture thinking and ability to reason under constraints.",
                "Clarify requirements, define APIs/data model, discuss scaling, reliability, and observability.",
                "Hard",
            ),
            _question(
                "How would you monitor and improve the reliability of a production AI or data workflow?",
                "Modern AI roles require production awareness, not just prototypes.",
                "Cover metrics, logging, evaluation, failure handling, and rollback plans.",
                "Hard",
            ),
        ]

        role_specific = [
            _question(
                f"Why are you a strong fit for this {role} role based on your resume?",
                "This tests whether the candidate can connect their story to the company's needs.",
                "Lead with the top three JD-aligned strengths, then address one gap with a ramp plan.",
                "Easy",
            )
        ]
        role_specific += [
            _question(
                f"How would you showcase this project for the role: {project[:90]}?",
                "The interviewer may probe resume projects that seem most transferable.",
                "Explain the problem, your contribution, technical details, and business or user impact.",
                "Medium",
            )
            for project in projects[:2]
        ]

        return {
            "technical_questions": technical[:7],
            "behavioral_questions": behavioral,
            "system_design_questions": system_design,
            "role_specific_questions": role_specific[:5],
        }


def _question(question: str, why: str, approach: str, difficulty: str) -> dict[str, str]:
    return {
        "question": question,
        "why_interviewer_asks": why,
        "expected_answer_approach": approach,
        "difficulty": difficulty,
    }


def _coerce_questions(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    output = dict(fallback)
    for key in ("technical_questions", "behavioral_questions", "system_design_questions", "role_specific_questions"):
        if isinstance(data.get(key), list):
            output[key] = [_coerce_question(item) for item in data[key] if isinstance(item, dict)]
    return output


def _coerce_question(item: dict[str, Any]) -> dict[str, str]:
    difficulty = str(item.get("difficulty", "Medium")).title()
    if difficulty not in {"Easy", "Medium", "Hard"}:
        difficulty = "Medium"
    return {
        "question": str(item.get("question", "Interview question")),
        "why_interviewer_asks": str(item.get("why_interviewer_asks", item.get("why", "This validates role fit."))),
        "expected_answer_approach": str(item.get("expected_answer_approach", item.get("approach", "Use a structured answer."))),
        "difficulty": difficulty,
    }

