"""Coach Agent: creates ATS guidance and a 7-day preparation sprint."""

from __future__ import annotations

import json
from typing import Any

from utils.llm import LLMClient
from utils.scoring import (
    ats_score,
    gap_risk_label,
    readiness_score,
    split_candidate_lines,
    technical_alignment_score,
)


COACH_SYSTEM_PROMPT = """
You are the Coach Agent in Resume2Offer AI.
Create a concise, high-leverage interview preparation strategy.
Return only valid JSON. The plan must be actionable and personalized to the resume/JD.
Include ATS score reasoning, missing keywords, resume bullet rewrites, and a 7-day sprint.
"""


class CoachAgent:
    name = "Coach Agent"
    purpose = "Generate preparation strategy, ATS guidance, and readiness improvement."

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(
        self,
        resume_text: str,
        jd_text: str,
        candidate_profile: dict[str, Any],
        match_report: dict[str, Any],
        gap_report: dict[str, Any],
        question_report: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = self._fallback_plan(resume_text, jd_text, candidate_profile, match_report, gap_report, question_report)
        prompt = f"""
Return a JSON object with this exact schema:
{{
  "ats_score": 0,
  "keyword_coverage": 0,
  "present_keywords": ["keyword"],
  "missing_keywords": ["keyword"],
  "resume_improvement_suggestions": ["suggestion"],
  "before_after_bullets": [
    {{"before": "Worked on APIs.", "after": "Designed and deployed RESTful APIs using Flask, improving response efficiency and maintainability."}}
  ],
  "readiness_score": 0,
  "skill_gap_risk": "Low | Medium | High",
  "technical_alignment": 0,
  "priority_tasks": ["task"],
  "topics_to_study": ["topic"],
  "projects_to_showcase": ["project"],
  "mock_interview_areas": ["area"],
  "estimated_readiness_improvement": {{"current_readiness": 78, "after_sprint": 91}},
  "sprint_plan": [
    {{"day": "Day 1", "theme": "theme", "tasks": ["actionable task"]}}
  ]
}}

Resume:
{resume_text[:7000]}

Candidate profile:
{json.dumps(candidate_profile, indent=2)[:4000]}

Match report:
{json.dumps(match_report, indent=2)[:4000]}

Gap report:
{json.dumps(gap_report, indent=2)[:4000]}

Predicted questions:
{json.dumps(question_report, indent=2)[:4000]}

Job description:
{jd_text[:7000]}
"""
        result = self.llm.generate_json(COACH_SYSTEM_PROMPT, prompt, fallback)
        data = _coerce_plan(result.data, fallback)
        data["_meta"] = {
            "agent": self.name,
            "used_llm": result.used_llm,
            "provider": result.provider,
            "error": result.error,
        }
        return data

    def _fallback_plan(
        self,
        resume_text: str,
        jd_text: str,
        candidate_profile: dict[str, Any],
        match_report: dict[str, Any],
        gap_report: dict[str, Any],
        question_report: dict[str, Any],
    ) -> dict[str, Any]:
        ats = ats_score(resume_text, jd_text)
        match_score = int(match_report.get("match_score", 0))
        gap_count = sum(len(gap_report.get(key, [])) for key in ("high_priority_gaps", "medium_priority_gaps", "low_priority_gaps"))
        ready = readiness_score(match_score, ats["ats_score"], gap_count)
        required_count = len(match_report.get("required_skills", []))
        missing_count = len(match_report.get("missing_skills", []))
        risk = gap_report.get("overall_gap_risk") or gap_risk_label(missing_count, required_count)
        alignment = technical_alignment_score(match_score, ats["keyword_coverage"])
        after = min(98, ready + 8 + min(8, gap_count * 2))

        missing_keywords = ats["missing_keywords"]
        high_gaps = [gap["skill"] for gap in gap_report.get("high_priority_gaps", [])]
        medium_gaps = [gap["skill"] for gap in gap_report.get("medium_priority_gaps", [])]
        all_gaps = high_gaps + medium_gaps
        topics = all_gaps[:6] or missing_keywords[:6] or match_report.get("required_skills", [])[:6]
        projects = candidate_profile.get("projects", [])[:3] or candidate_profile.get("experience", [])[:3]
        questions = question_report.get("technical_questions", []) + question_report.get("role_specific_questions", [])

        return {
            "ats_score": ats["ats_score"],
            "keyword_coverage": ats["keyword_coverage"],
            "present_keywords": ats["present_keywords"],
            "missing_keywords": missing_keywords,
            "resume_improvement_suggestions": _resume_suggestions(missing_keywords, ats),
            "before_after_bullets": _rewrite_bullets(resume_text, match_report.get("matching_skills", []), missing_keywords),
            "readiness_score": ready,
            "skill_gap_risk": risk,
            "technical_alignment": alignment,
            "priority_tasks": _priority_tasks(high_gaps, match_report, ats),
            "topics_to_study": topics[:7],
            "projects_to_showcase": projects[:4],
            "mock_interview_areas": [item.get("question", "Mock interview question") for item in questions[:5]],
            "estimated_readiness_improvement": {
                "current_readiness": ready,
                "after_sprint": after,
            },
            "sprint_plan": _sprint_plan(topics, projects, missing_keywords),
        }


def _resume_suggestions(missing_keywords: list[str], ats: dict[str, Any]) -> list[str]:
    suggestions = [
        "Mirror the job title and top role keywords in the summary and skills sections when truthful.",
        "Convert responsibility-only bullets into outcome bullets with metrics, scope, and tools.",
        "Group technical skills by category so recruiters can scan role-critical tools quickly.",
    ]
    if missing_keywords:
        suggestions.insert(0, f"Add honest evidence for missing keywords: {', '.join(missing_keywords[:6])}.")
    if ats.get("section_score", 0) < 80:
        suggestions.append("Add clear section headings for Skills, Experience, Projects, Education, and Certifications.")
    return suggestions


def _rewrite_bullets(resume_text: str, strengths: list[str], missing_keywords: list[str]) -> list[dict[str, str]]:
    source = split_candidate_lines(resume_text, limit=6)
    if not source:
        source = ["Worked on APIs.", "Built machine learning project.", "Created dashboards."]

    target_skills = strengths[:3] + missing_keywords[:3]
    skill_phrase = ", ".join(target_skills[:3]) if target_skills else "role-relevant tools"
    rewrites: list[dict[str, str]] = []
    templates = [
        "Designed and delivered {skill_phrase} solutions, improving reliability, usability, and maintainability for target users.",
        "Built production-ready workflows using {skill_phrase}, translating ambiguous requirements into measurable outcomes.",
        "Implemented end-to-end features with {skill_phrase}, documenting tradeoffs and reducing delivery risk.",
    ]
    for index, before in enumerate(source[:3]):
        rewrites.append(
            {
                "before": before,
                "after": templates[index % len(templates)].format(skill_phrase=skill_phrase),
            }
        )
    return rewrites


def _priority_tasks(high_gaps: list[str], match_report: dict[str, Any], ats: dict[str, Any]) -> list[str]:
    tasks = []
    if high_gaps:
        tasks.append(f"Close the highest-risk gap first: prepare a demo or story for {high_gaps[0]}.")
    tasks.append("Prepare a 90-second role-fit pitch anchored to the top three matching skills.")
    tasks.append("Rewrite the resume summary and top three bullets using JD language.")
    if ats.get("missing_keywords"):
        tasks.append(f"Add truthful evidence for missing ATS terms: {', '.join(ats['missing_keywords'][:5])}.")
    if match_report.get("missing_skills"):
        tasks.append("Prepare a transparent answer for each missing skill with adjacent experience and ramp plan.")
    return tasks


def _sprint_plan(topics: list[str], projects: list[str], missing_keywords: list[str]) -> list[dict[str, Any]]:
    primary_topic = topics[0] if topics else "role fundamentals"
    second_topic = topics[1] if len(topics) > 1 else "system design fundamentals"
    project = projects[0] if projects else "your strongest relevant project"
    keywords = ", ".join(missing_keywords[:5]) if missing_keywords else "top JD keywords"

    return [
        {
            "day": "Day 1",
            "theme": "Role decoding and story map",
            "tasks": [
                "Highlight the top 10 requirements in the JD and map each to resume evidence.",
                "Write a 90-second answer for 'Tell me about yourself' tied to the target role.",
            ],
        },
        {
            "day": "Day 2",
            "theme": "ATS and resume rewrite",
            "tasks": [
                f"Add truthful evidence for {keywords}.",
                "Rewrite the top three bullets with action, tool, scope, and outcome.",
            ],
        },
        {
            "day": "Day 3",
            "theme": f"Deep dive: {primary_topic}",
            "tasks": [
                f"Study core concepts and common interview probes for {primary_topic}.",
                "Build or document one small proof-of-skill artifact.",
            ],
        },
        {
            "day": "Day 4",
            "theme": f"Project defense: {project[:60]}",
            "tasks": [
                "Prepare architecture, tradeoff, failure, metric, and impact talking points.",
                "Practice explaining the project at 2-minute, 5-minute, and 10-minute depths.",
            ],
        },
        {
            "day": "Day 5",
            "theme": f"Deep dive: {second_topic}",
            "tasks": [
                f"Review interview patterns for {second_topic}.",
                "Create a one-page cheat sheet with examples from your experience.",
            ],
        },
        {
            "day": "Day 6",
            "theme": "Mock interview loop",
            "tasks": [
                "Run one technical mock and one behavioral mock using the predicted questions.",
                "Record weak answers and rewrite them using STAR or problem-action-result.",
            ],
        },
        {
            "day": "Day 7",
            "theme": "Final readiness pass",
            "tasks": [
                "Review gap answers, resume bullets, and role-fit pitch.",
                "Prepare five thoughtful questions for the hiring team.",
            ],
        },
    ]


def _coerce_plan(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    output = dict(fallback)
    for key in ("ats_score", "keyword_coverage", "readiness_score", "technical_alignment"):
        output[key] = _bounded_int(data.get(key, fallback[key]))
    if data.get("skill_gap_risk") in {"Low", "Medium", "High"}:
        output["skill_gap_risk"] = data["skill_gap_risk"]
    for key in (
        "missing_keywords",
        "present_keywords",
        "resume_improvement_suggestions",
        "priority_tasks",
        "topics_to_study",
        "projects_to_showcase",
        "mock_interview_areas",
    ):
        if isinstance(data.get(key), list):
            output[key] = [str(item).strip() for item in data[key] if str(item).strip()]
    if isinstance(data.get("before_after_bullets"), list):
        output["before_after_bullets"] = [
            {"before": str(item.get("before", "")), "after": str(item.get("after", ""))}
            for item in data["before_after_bullets"]
            if isinstance(item, dict)
        ]
    if isinstance(data.get("estimated_readiness_improvement"), dict):
        output["estimated_readiness_improvement"] = {
            "current_readiness": _bounded_int(data["estimated_readiness_improvement"].get("current_readiness", output["readiness_score"])),
            "after_sprint": _bounded_int(data["estimated_readiness_improvement"].get("after_sprint", output["readiness_score"])),
        }
    if isinstance(data.get("sprint_plan"), list):
        output["sprint_plan"] = [_coerce_day(day) for day in data["sprint_plan"] if isinstance(day, dict)]
    return output


def _coerce_day(day: dict[str, Any]) -> dict[str, Any]:
    tasks = day.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = [str(tasks)]
    return {
        "day": str(day.get("day", "Day")),
        "theme": str(day.get("theme", "Preparation")),
        "tasks": [str(task).strip() for task in tasks if str(task).strip()],
    }


def _bounded_int(value: Any) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return 0
