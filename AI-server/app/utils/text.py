from __future__ import annotations

import re
from difflib import unified_diff

TECH_KEYWORDS = [
    "python", "fastapi", "django", "flask", "node.js", "nodejs", "express.js", "express",
    "nestjs", "react", "reactjs", "vue", "next.js", "nextjs", "typescript", "javascript",
    "java", "spring", "c++", "c#", ".net", "sql", "mysql", "postgresql", "mongodb",
    "redis", "docker", "kubernetes", "git", "github", "ci/cd", "rest", "restful api",
    "graphql", "api", "microservices", "aws", "gcp", "azure", "html", "css", "tailwind",
    "testing", "unit test", "integration test", "agile", "scrum", "qa", "selenium", "playwright",
]

ROLE_KEYWORDS = {
    "backend": ["backend", "api", "server", "database", "sql", "node", "express", "fastapi", "rest"],
    "frontend": ["frontend", "react", "vue", "ui", "html", "css", "tailwind", "responsive"],
    "fullstack": ["fullstack", "full-stack", "frontend", "backend", "react", "node", "api"],
    "ai": ["ai", "machine learning", "llm", "rag", "agent", "nlp", "computer vision"],
    "data": ["data", "etl", "analytics", "sql", "bigquery", "warehouse", "dashboard"],
    "qa": ["qa", "quality", "test case", "automation", "selenium", "playwright", "manual testing"],
    "devops": ["devops", "docker", "kubernetes", "ci/cd", "cloud", "deployment"],
}

PROMPT_INJECTION_PATTERNS = [
    r"ignore.*instructions",
    r"disregard.*instructions",
    r"forget.*instructions",
    r"override.*system",
    r"you are now",
    r"send.*cv.*to",
    r"email.*attacker",
    r"tool call",
    r"call .*send",
]

PLACEHOLDER_PATTERN = re.compile(r"\[[^\]]+\]|\{\{[^}]+\}\}|<[^>]+>")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_lines(text: str) -> list[str]:
    return [line.strip(" -•\t") for line in (text or "").splitlines() if line.strip()]


def find_keywords(text: str, keywords: list[str] | None = None) -> list[str]:
    haystack = (text or "").lower()
    found = []
    for kw in keywords or TECH_KEYWORDS:
        pattern = r"(?<![a-z0-9+#.])" + re.escape(kw.lower()) + r"(?![a-z0-9+#.])"
        if re.search(pattern, haystack):
            canonical = canonical_keyword(kw)
            if canonical not in found:
                found.append(canonical)
    return found


def canonical_keyword(keyword: str) -> str:
    mapping = {
        "nodejs": "Node.js",
        "node.js": "Node.js",
        "express": "Express.js",
        "express.js": "Express.js",
        "reactjs": "ReactJS",
        "react": "ReactJS",
        "nextjs": "Next.js",
        "next.js": "Next.js",
        "rest": "RESTful API",
        "restful api": "RESTful API",
        "api": "API",
        "sql": "SQL",
        "mongodb": "MongoDB",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "git": "Git",
        "github": "GitHub",
        "docker": "Docker",
        "fastapi": "FastAPI",
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
    }
    return mapping.get(keyword.lower(), keyword.strip())


def detect_role_focus(jd_text: str) -> dict[str, str]:
    text = (jd_text or "").lower()
    scores = {}
    for role, kws in ROLE_KEYWORDS.items():
        scores[role] = sum(1 for kw in kws if kw in text)
    primary = max(scores, key=scores.get) if scores else "general"
    if scores.get(primary, 0) == 0:
        primary = "general"
    level = "intern" if any(x in text for x in ["intern", "internship", "fresher", "junior", "entry"] ) else "general"
    return {
        "primary_focus": primary,
        "secondary_focus": second_best(scores, primary),
        "level": level,
        "role_type": f"{primary.title()} {level.title()}" if primary != "general" else level.title(),
        "recommended_resume_angle": f"{primary}-focused" if primary != "general" else "role-aligned",
    }


def second_best(scores: dict[str, int], primary: str) -> str:
    candidates = {k: v for k, v in scores.items() if k != primary}
    if not candidates:
        return "general"
    name = max(candidates, key=candidates.get)
    return name if candidates[name] > 0 else "general"


def detect_prompt_injection(text: str) -> list[str]:
    lower = (text or "").lower()
    hits = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower):
            hits.append(pattern)
    return hits


def make_diff(original: str, revised: str) -> str:
    return "\n".join(unified_diff(
        (original or "").splitlines(),
        (revised or "").splitlines(),
        fromfile="original_cv",
        tofile="tailored_cv",
        lineterm="",
    ))


def has_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.search(text or ""))


def contains_metric(text: str) -> bool:
    return bool(re.search(r"\b\d+(%|x|\+| users?| ms| sec| seconds?| projects?| endpoints?| pages?| hours?)\b", text.lower()))


def has_action_verb(text: str) -> bool:
    verbs = ["built", "developed", "implemented", "designed", "optimized", "integrated", "tested", "deployed", "created", "improved", "reduced", "increased"]
    return any(v in text.lower() for v in verbs)
