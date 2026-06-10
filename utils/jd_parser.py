"""Job description parsing helpers."""

from __future__ import annotations

import re

from utils.scoring import extract_keywords, extract_skills, estimate_required_years, normalize_text


def parse_job_description(jd_text: str) -> dict:
    """Return a structured summary of a job description."""

    text = normalize_text(jd_text)
    title = _extract_title(jd_text)
    required_skills = extract_skills(jd_text)
    return {
        "title": title,
        "required_skills": required_skills,
        "keywords": extract_keywords(jd_text),
        "required_years": estimate_required_years(jd_text),
        "responsibilities": _extract_section_lines(jd_text, ("responsibilities", "what you will do", "duties")),
        "requirements": _extract_section_lines(jd_text, ("requirements", "qualifications", "what we are looking for")),
        "summary": text[:900],
    }


def _extract_title(jd_text: str) -> str:
    lines = [line.strip(" -|") for line in (jd_text or "").splitlines() if line.strip()]
    for line in lines[:6]:
        if len(line) <= 90 and re.search(r"\b(engineer|developer|scientist|analyst|manager|intern|architect|consultant)\b", line, re.I):
            return line
    return "Target Role"


def _extract_section_lines(jd_text: str, headings: tuple[str, ...], limit: int = 8) -> list[str]:
    lines = [line.strip(" -*\u2022\t") for line in (jd_text or "").splitlines()]
    results: list[str] = []
    capture = False
    for line in lines:
        if not line:
            continue
        lowered = line.lower().rstrip(":")
        if any(heading in lowered for heading in headings):
            capture = True
            continue
        if capture and re.match(r"^[A-Z][A-Za-z /&-]{2,}:$", line):
            break
        if capture and 8 <= len(line) <= 180:
            results.append(line)
        if len(results) >= limit:
            break
    return results
