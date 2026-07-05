from __future__ import annotations

import re
from app.models import StructuredResume, StructuredJD
from app.utils.text import split_lines, find_keywords

SECTION_ALIASES = {
    "summary": ["summary", "profile", "objective", "about"],
    "skills": ["skills", "technical skills", "technologies", "tech stack"],
    "education": ["education", "academic background"],
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "projects": ["projects", "personal projects", "academic projects"],
    "certificates": ["certificates", "certifications", "awards"],
}


def parse_resume_text(text: str) -> StructuredResume:
    sections = _rough_sections(text)
    all_lines = split_lines(text)
    skills = find_keywords(text)
    projects = _lines_under(sections, "projects") or [line for line in all_lines if any(word in line.lower() for word in ["project", "built", "developed", "implemented"])]
    experience = _lines_under(sections, "experience")
    education = _lines_under(sections, "education")
    certificates = _lines_under(sections, "certificates")
    summary = sections.get("summary", "") or _first_meaningful_sentence(text)
    return StructuredResume(
        summary=summary,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        certificates=certificates,
        raw_sections=sections,
    )


def parse_jd_text(text: str) -> StructuredJD:
    lines = split_lines(text)
    tech_stack = find_keywords(text)
    responsibilities = [line for line in lines if _looks_like_responsibility(line)]
    requirements = [line for line in lines if _looks_like_requirement(line)]
    qualifications = [line for line in lines if _looks_like_qualification(line)]
    if not requirements:
        requirements = lines[: min(8, len(lines))]
    return StructuredJD(
        responsibilities=responsibilities,
        requirements=requirements,
        qualifications=qualifications,
        tech_stack=tech_stack,
        company_context=_first_meaningful_sentence(text),
    )


def _rough_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    current = "summary"
    buckets = {key: [] for key in SECTION_ALIASES}
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        matched = None
        for key, aliases in SECTION_ALIASES.items():
            if normalized in aliases or any(normalized == a for a in aliases):
                matched = key
                break
        if matched:
            current = matched
            continue
        buckets.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in buckets.items() if value}


def _lines_under(sections: dict[str, str], key: str) -> list[str]:
    return split_lines(sections.get(key, ""))


def _first_meaningful_sentence(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return parts[0][:400]


def _looks_like_responsibility(line: str) -> bool:
    l = line.lower()
    return any(x in l for x in ["respons", "collaborate", "develop", "build", "maintain", "implement", "work with"])


def _looks_like_requirement(line: str) -> bool:
    l = line.lower()
    return any(x in l for x in ["require", "must", "need", "knowledge", "experience", "familiar", "proficient", "understand"])


def _looks_like_qualification(line: str) -> bool:
    l = line.lower()
    return any(x in l for x in ["plus", "preferred", "nice", "advantage", "bonus"])
