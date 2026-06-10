"""Deterministic scoring and extraction helpers.

The agents can call an LLM when credentials are available, but these utilities
keep the product demo reliable when running locally without an API key.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    aliases: tuple[str, ...]
    category: str


SKILL_DEFINITIONS: tuple[SkillDefinition, ...] = (
    SkillDefinition("Python", ("python",), "Programming"),
    SkillDefinition("JavaScript", ("javascript", "js", "node.js", "nodejs"), "Programming"),
    SkillDefinition("TypeScript", ("typescript", "ts"), "Programming"),
    SkillDefinition("Java", ("java",), "Programming"),
    SkillDefinition("C++", ("c++", "cpp"), "Programming"),
    SkillDefinition("SQL", ("sql", "postgres", "postgresql", "mysql", "sqlite"), "Data"),
    SkillDefinition("NoSQL", ("nosql", "mongodb", "dynamodb", "cassandra"), "Data"),
    SkillDefinition("Pandas", ("pandas",), "Data"),
    SkillDefinition("NumPy", ("numpy",), "Data"),
    SkillDefinition("Machine Learning", ("machine learning", "ml", "sklearn", "scikit-learn"), "AI"),
    SkillDefinition("Deep Learning", ("deep learning", "neural network", "pytorch", "tensorflow", "keras"), "AI"),
    SkillDefinition("NLP", ("nlp", "natural language processing", "llm", "large language model"), "AI"),
    SkillDefinition("Generative AI", ("generative ai", "genai", "rag", "agents", "prompt engineering"), "AI"),
    SkillDefinition("OpenAI API", ("openai", "openai api", "gpt", "chatgpt"), "AI"),
    SkillDefinition("LangChain", ("langchain",), "AI"),
    SkillDefinition("LangGraph", ("langgraph",), "AI"),
    SkillDefinition("Streamlit", ("streamlit",), "Frontend"),
    SkillDefinition("React", ("react", "react.js", "next.js", "nextjs"), "Frontend"),
    SkillDefinition("HTML/CSS", ("html", "css", "tailwind", "bootstrap"), "Frontend"),
    SkillDefinition("Flask", ("flask",), "Backend"),
    SkillDefinition("FastAPI", ("fastapi",), "Backend"),
    SkillDefinition("Django", ("django",), "Backend"),
    SkillDefinition("REST APIs", ("rest api", "restful", "api", "apis"), "Backend"),
    SkillDefinition("GraphQL", ("graphql",), "Backend"),
    SkillDefinition("Docker", ("docker", "container", "containers"), "DevOps"),
    SkillDefinition("Kubernetes", ("kubernetes", "k8s"), "DevOps"),
    SkillDefinition("AWS", ("aws", "amazon web services", "lambda", "s3", "ec2"), "Cloud"),
    SkillDefinition("Azure", ("azure",), "Cloud"),
    SkillDefinition("GCP", ("gcp", "google cloud"), "Cloud"),
    SkillDefinition("CI/CD", ("ci/cd", "github actions", "jenkins", "gitlab ci"), "DevOps"),
    SkillDefinition("Git", ("git", "github", "gitlab", "bitbucket"), "Tools"),
    SkillDefinition("Testing", ("pytest", "unit testing", "integration testing", "test automation"), "Quality"),
    SkillDefinition("Data Visualization", ("plotly", "matplotlib", "seaborn", "dashboard"), "Data"),
    SkillDefinition("ETL", ("etl", "data pipeline", "airflow", "spark"), "Data"),
    SkillDefinition("Statistics", ("statistics", "probability", "hypothesis testing"), "Data"),
    SkillDefinition("System Design", ("system design", "scalability", "distributed systems"), "Architecture"),
    SkillDefinition("Agile", ("agile", "scrum", "kanban"), "Process"),
    SkillDefinition("Product Thinking", ("product", "roadmap", "user research", "metrics"), "Product"),
)


STOPWORDS = {
    "and",
    "are",
    "but",
    "for",
    "from",
    "have",
    "into",
    "must",
    "our",
    "that",
    "the",
    "this",
    "with",
    "will",
    "you",
    "your",
    "experience",
    "candidate",
    "role",
    "team",
    "work",
    "using",
    "strong",
    "ability",
    "skills",
    "years",
    "responsibilities",
    "requirements",
    "preferred",
    "required",
    "including",
}


def normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""

    text = text or ""
    text = text.replace("\u2022", " ")
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _has_alias(text: str, alias: str) -> bool:
    escaped = re.escape(alias.lower())
    if re.search(r"[+#./-]", alias):
        return escaped in text.lower()
    return bool(re.search(rf"\b{escaped}\b", text.lower()))


def extract_skills(text: str) -> list[str]:
    """Extract known technical and product skills from free text."""

    normalized = normalize_text(text).lower()
    found: list[str] = []
    for skill in SKILL_DEFINITIONS:
        if any(_has_alias(normalized, alias) for alias in skill.aliases):
            found.append(skill.name)
    return sorted(set(found))


def skill_category(skill_name: str) -> str:
    for skill in SKILL_DEFINITIONS:
        if skill.name == skill_name:
            return skill.category
    return "Other"


def extract_years_of_experience(text: str) -> int:
    """Return the highest explicit years-of-experience signal found."""

    patterns = [
        r"(\d{1,2})\+?\s*(?:years|yrs)\s+(?:of\s+)?experience",
        r"experience\s+(?:of\s+)?(\d{1,2})\+?\s*(?:years|yrs)",
        r"(\d{1,2})\+?\s*(?:years|yrs)",
    ]
    years = []
    for pattern in patterns:
        years.extend(int(match) for match in re.findall(pattern, text or "", flags=re.I))
    return max(years) if years else 0


def estimate_required_years(jd_text: str) -> int:
    return extract_years_of_experience(jd_text)


def split_candidate_lines(text: str, limit: int = 12) -> list[str]:
    """Collect resume-like bullets that are good candidates for rewriting."""

    raw_lines = re.split(r"[\n;]+", text or "")
    cleaned: list[str] = []
    for line in raw_lines:
        line = re.sub(r"^[\s\-*\u2022]+", "", line).strip()
        if 18 <= len(line) <= 220:
            cleaned.append(line)
    return cleaned[:limit]


def extract_keywords(text: str, max_keywords: int = 35) -> list[str]:
    """Extract a blend of canonical skills and high-signal JD keywords."""

    canonical = extract_skills(text)
    words = re.findall(r"[A-Za-z][A-Za-z+#./-]{2,}", normalize_text(text))
    counts = Counter(
        word.strip(".,:;()[]").lower()
        for word in words
        if word.lower() not in STOPWORDS and len(word) > 2
    )
    ranked_words = [
        word.title() if word.islower() else word
        for word, _ in counts.most_common(max_keywords)
        if word not in {item.lower() for item in canonical}
    ]
    combined = canonical + ranked_words
    unique: list[str] = []
    seen = set()
    for keyword in combined:
        key = keyword.lower()
        if key not in seen:
            unique.append(keyword)
            seen.add(key)
    return unique[:max_keywords]


def keyword_coverage(required_keywords: Iterable[str], resume_text: str) -> tuple[int, list[str], list[str]]:
    required = [keyword for keyword in required_keywords if keyword]
    resume_lower = normalize_text(resume_text).lower()
    present: list[str] = []
    missing: list[str] = []
    for keyword in required:
        key = keyword.lower()
        if key in resume_lower or any(_has_alias(resume_lower, alias) for alias in _aliases_for(keyword)):
            present.append(keyword)
        else:
            missing.append(keyword)
    if not required:
        return 0, present, missing
    return round((len(present) / len(required)) * 100), present, missing


def _aliases_for(skill_or_keyword: str) -> tuple[str, ...]:
    for skill in SKILL_DEFINITIONS:
        if skill.name.lower() == skill_or_keyword.lower():
            return skill.aliases
    return (skill_or_keyword,)


def calculate_match_score(
    resume_text: str,
    jd_text: str,
    candidate_skills: Iterable[str] | None = None,
) -> dict:
    """Calculate an explainable 0-100 match score."""

    candidate_skill_set = set(candidate_skills or extract_skills(resume_text))
    required_skills = extract_skills(jd_text)
    matching_skills = sorted(candidate_skill_set.intersection(required_skills))
    missing_skills = sorted(set(required_skills) - candidate_skill_set)

    if required_skills:
        skill_score = round((len(matching_skills) / len(required_skills)) * 55)
    else:
        skill_score = 25 if candidate_skill_set else 0

    resume_years = extract_years_of_experience(resume_text)
    required_years = estimate_required_years(jd_text)
    if required_years == 0:
        experience_score = 18 if resume_years else 12
    else:
        experience_score = min(20, round((resume_years / required_years) * 20))

    jd_keywords = extract_keywords(jd_text, max_keywords=25)
    coverage, _, missing_keywords = keyword_coverage(jd_keywords, resume_text)
    keyword_score = round(coverage * 0.15)

    project_signal = 10 if re.search(r"\b(project|built|designed|deployed|implemented|launched)\b", resume_text or "", re.I) else 4
    score = max(0, min(100, skill_score + experience_score + keyword_score + project_signal))

    reasoning = []
    for skill in matching_skills:
        reasoning.append(
            {
                "signal": f"{skill} matches",
                "impact": _skill_weight(skill, positive=True),
                "type": "positive",
            }
        )
    for skill in missing_skills[:8]:
        reasoning.append(
            {
                "signal": f"{skill} missing",
                "impact": _skill_weight(skill, positive=False),
                "type": "negative",
            }
        )
    reasoning.append(
        {
            "signal": f"Experience signal: {resume_years or 'not explicit'} years vs {required_years or 'unspecified'} required",
            "impact": experience_score - 10,
            "type": "positive" if experience_score >= 12 else "negative",
        }
    )
    if missing_keywords:
        reasoning.append(
            {
                "signal": f"Keyword coverage leaves {len(missing_keywords)} JD terms to add",
                "impact": -min(10, len(missing_keywords)),
                "type": "negative",
            }
        )

    return {
        "match_score": score,
        "required_skills": required_skills,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "keyword_coverage": coverage,
        "experience_alignment": {
            "candidate_years": resume_years,
            "required_years": required_years,
            "score": experience_score,
            "summary": _experience_summary(resume_years, required_years),
        },
        "reasoning": reasoning,
    }


def _skill_weight(skill: str, positive: bool) -> int:
    category_weights = {
        "AI": 12,
        "Data": 10,
        "Backend": 9,
        "Cloud": 8,
        "DevOps": 7,
        "Architecture": 8,
        "Programming": 10,
        "Frontend": 7,
        "Product": 6,
    }
    weight = category_weights.get(skill_category(skill), 5)
    return weight if positive else -max(5, math.ceil(weight * 0.7))


def _experience_summary(candidate_years: int, required_years: int) -> str:
    if required_years == 0:
        return "The job description does not specify a strict years-of-experience requirement."
    if candidate_years >= required_years:
        return "The resume appears to meet or exceed the stated experience requirement."
    if candidate_years == 0:
        return "The resume does not make years of experience explicit, which can weaken recruiter confidence."
    return "The resume shows relevant experience but appears below the stated years threshold."


def ats_score(resume_text: str, jd_text: str) -> dict:
    required_keywords = extract_keywords(jd_text, max_keywords=30)
    coverage, present, missing = keyword_coverage(required_keywords, resume_text)
    section_score = _section_score(resume_text)
    bullet_score = _bullet_quality_score(resume_text)
    final = round(coverage * 0.55 + section_score * 0.25 + bullet_score * 0.20)
    return {
        "ats_score": max(0, min(100, final)),
        "keyword_coverage": coverage,
        "present_keywords": present,
        "missing_keywords": missing[:15],
        "section_score": section_score,
        "bullet_quality_score": bullet_score,
    }


def _section_score(text: str) -> int:
    sections = ["experience", "education", "skills", "projects", "certifications"]
    hits = sum(1 for section in sections if re.search(rf"\b{section}\b", text or "", re.I))
    return round((hits / len(sections)) * 100)


def _bullet_quality_score(text: str) -> int:
    bullets = split_candidate_lines(text, limit=30)
    if not bullets:
        return 35
    action_verbs = ("built", "designed", "deployed", "improved", "reduced", "increased", "created", "led")
    scored = 0
    for bullet in bullets:
        has_action = any(verb in bullet.lower() for verb in action_verbs)
        has_metric = bool(re.search(r"\d+%?|\$|x\b", bullet))
        scored += 40 + (35 if has_action else 0) + (25 if has_metric else 0)
    return round(min(100, scored / len(bullets)))


def readiness_score(match_score: int, ats: int, gap_count: int, question_risk: int = 0) -> int:
    risk_penalty = min(18, gap_count * 3 + question_risk)
    return max(0, min(100, round(match_score * 0.55 + ats * 0.35 + 20 * 0.10 - risk_penalty)))


def gap_risk_label(missing_count: int, required_count: int) -> str:
    if required_count == 0:
        return "Low"
    ratio = missing_count / required_count
    if ratio >= 0.45:
        return "High"
    if ratio >= 0.22:
        return "Medium"
    return "Low"


def technical_alignment_score(match_score: int, skill_coverage: int) -> int:
    return max(0, min(100, round(match_score * 0.45 + skill_coverage * 0.55)))
