from __future__ import annotations

from app.agents.base import BaseAgent, AgentResult
from app.models import TailoringStrategy
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider


class TailoringStrategistAgent(BaseAgent):
    name = "TailoringStrategistAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        jd_analysis = session.jd_analysis
        cv_analysis = session.cv_analysis
        assert jd_analysis is not None and cv_analysis is not None

        system, prompt = build_json_prompt(
            task=(
                "Create a CV tailoring strategy for this application. Decide the resume angle, "
                "rewrite plan, section priority, and evidence map. The evidence_map must classify "
                "each important JD keyword as either 'supported' or 'missing' based only on the original CV."
            ),
            schema=TailoringStrategy.model_json_schema(),
            inputs={
                "company_name": session.company_name,
                "role_title": session.role_title,
                "original_resume_text": session.original_resume_text,
                "job_description_text": session.job_description_text,
                "jd_analysis": jd_analysis.model_dump(),
                "cv_analysis": cv_analysis.model_dump(),
            },
            skill_names=["resume-tailoring", "jd-analysis", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            strategy = _fallback_strategy(session)
        else:
            strategy = TailoringStrategy.model_validate(data)
            strategy.evidence_map = _normalize_evidence_map(strategy.evidence_map, session)
        session.tailoring_strategy = strategy
        return AgentResult(self.name, strategy.model_dump(), ["Tailoring strategy generated with LLM prompt."])


def _normalize_evidence_map(evidence_map: dict[str, str], session) -> dict[str, str]:
    normalized = {}
    resume_text = session.original_resume_text.lower()
    for kw in session.jd_analysis.jd_keywords:
        existing = (evidence_map or {}).get(kw, "")
        if existing in {"supported", "missing"}:
            normalized[kw] = existing
        else:
            normalized[kw] = "supported" if kw.lower() in resume_text else "missing"
    return normalized


def _fallback_strategy(session) -> TailoringStrategy:
    jd_analysis = session.jd_analysis
    role_angle = jd_analysis.role_focus.get("recommended_resume_angle", "role-aligned")
    resume_text = session.original_resume_text.lower()
    evidence_map = {kw: ("supported" if kw.lower() in resume_text else "missing") for kw in jd_analysis.jd_keywords}
    return TailoringStrategy(
        tailoring_strategy=f"Create a {role_angle} CV version while preserving factual claims from the original CV.",
        rewrite_plan=[
            "Rewrite the summary to reflect the target role.",
            "Reorder skills so supported JD keywords appear earlier.",
            "Rewrite project bullets using action verbs and concrete scope.",
            "Do not add missing technologies as claimed skills.",
        ],
        section_priority=["summary", "skills", "projects", "experience", "education", "certificates"],
        evidence_map=evidence_map,
    )
