from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent, AgentResult
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider
from app.utils.text import find_keywords


class ATSScoringAgent(BaseAgent):
    name = "ATSScoringAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        version = next(v for v in session.tailored_resume_versions if v.version_id == session.selected_resume_version_id)

        schema: dict[str, Any] = {
            "type": "object",
            "required": ["match_score", "keyword_coverage", "role_alignment_score", "improvement_notes"],
            "properties": {
                "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "keyword_coverage": {
                    "type": "object",
                    "properties": {
                        "covered": {"type": "array", "items": {"type": "string"}},
                        "missing": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "role_alignment_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "improvement_notes": {"type": "array", "items": {"type": "string"}},
            },
        }
        system, prompt = build_json_prompt(
            task=(
                "Score the tailored CV against the JD for screening fit. Do not reward unsupported "
                "claims. Provide keyword coverage and concise improvement notes."
            ),
            schema=schema,
            inputs={
                "job_description_text": session.job_description_text,
                "tailored_resume": version.content,
                "jd_analysis": session.jd_analysis.model_dump() if session.jd_analysis else {},
                "honesty_report": version.honesty_report,
            },
            skill_names=["jd-analysis", "resume-tailoring"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            data = _fallback_score(session, version.content)
        score = int(max(0, min(100, data.get("match_score", 0))))
        version.match_score = score
        output = {
            "match_score": score,
            "keyword_coverage": data.get("keyword_coverage", {"covered": [], "missing": []}),
            "role_alignment_score": int(max(0, min(100, data.get("role_alignment_score", score)))),
            "improvement_notes": data.get("improvement_notes", []),
        }
        return AgentResult(self.name, output, ["ATS/JD scoring completed with LLM evaluation."])


def _fallback_score(session, content: str) -> dict[str, Any]:
    jd_keywords = set(session.jd_analysis.jd_keywords if session.jd_analysis else [])
    cv_keywords = set(find_keywords(content))
    covered = sorted(jd_keywords & cv_keywords)
    missing = sorted(jd_keywords - cv_keywords)
    score = int((len(covered) / max(1, len(jd_keywords))) * 100)
    score = min(95, score) if jd_keywords else 50
    return {
        "match_score": score,
        "keyword_coverage": {"covered": covered, "missing": missing},
        "role_alignment_score": score,
        "improvement_notes": [
            "Only add missing keywords when supported by real CV evidence.",
            "Strengthen bullets with project scope and outcomes.",
        ],
    }
