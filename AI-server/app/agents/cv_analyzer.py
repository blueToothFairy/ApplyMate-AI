from __future__ import annotations

from app.agents.base import BaseAgent, AgentResult
from app.models import CVAnalysis
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider
from app.utils.text import contains_metric, has_action_verb


class CVAnalyzerAgent(BaseAgent):
    name = "CVAnalyzerAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        resume = session.structured_resume
        jd_analysis = session.jd_analysis
        assert resume is not None and jd_analysis is not None

        system, prompt = build_json_prompt(
            task=(
                "Analyze the current CV against the JD analysis. Identify strengths, weaknesses, "
                "missing keywords, weak bullets, and improvement opportunities. Be strict about "
                "evidence: a keyword is missing if the original CV does not clearly support it."
            ),
            schema=CVAnalysis.model_json_schema(),
            inputs={
                "original_resume_text": session.original_resume_text,
                "structured_resume": resume.model_dump(),
                "job_description_text": session.job_description_text,
                "jd_analysis": jd_analysis.model_dump(),
            },
            skill_names=["resume-tailoring", "jd-analysis", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            analysis = _fallback_analysis(session)
        else:
            analysis = CVAnalysis.model_validate(data)
        session.cv_analysis = analysis
        return AgentResult(self.name, analysis.model_dump(), ["CV analyzed with LLM prompt and evidence constraints."])


def _fallback_analysis(session) -> CVAnalysis:
    resume = session.structured_resume
    jd_analysis = session.jd_analysis
    resume_text = session.original_resume_text.lower()
    strengths = [kw for kw in jd_analysis.jd_keywords if kw.lower() in resume_text]
    missing = [kw for kw in jd_analysis.jd_keywords if kw.lower() not in resume_text]
    bullets = resume.projects + resume.experience
    weak_bullets = [b for b in bullets if not has_action_verb(b) or not contains_metric(b)]
    weaknesses = []
    if missing:
        weaknesses.append("Some JD keywords are not clearly supported by the current CV.")
    if weak_bullets:
        weaknesses.append("Some bullets are too generic or lack measurable impact.")
    if not resume.summary:
        weaknesses.append("Summary section is missing or unclear.")
    return CVAnalysis(
        cv_strengths=strengths,
        cv_weaknesses=weaknesses,
        missing_keywords=missing,
        weak_bullets=weak_bullets[:8],
        improvement_opportunities=[
            "Rewrite summary toward the detected role focus.",
            "Move supported JD keywords higher in Skills.",
            "Rewrite project bullets with action, scope, and outcome.",
        ],
    )
