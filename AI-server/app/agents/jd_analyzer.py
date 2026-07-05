from __future__ import annotations

from app.agents.base import BaseAgent, AgentResult
from app.models import JDAnalysis
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider
from app.utils.text import find_keywords, detect_role_focus


class JDAnalyzerAgent(BaseAgent):
    name = "JDAnalyzerAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        jd = session.structured_jd
        assert jd is not None

        schema = JDAnalysis.model_json_schema()
        system, prompt = build_json_prompt(
            task=(
                "Analyze the job description for CV tailoring. Extract requirements, keywords, "
                "role focus, and a priority matrix. Build the priority matrix by checking whether "
                "each JD requirement/keyword is supported by the ORIGINAL CV. If unsupported, mark "
                "it as a gap and do not recommend adding it as a direct CV claim."
            ),
            schema=schema,
            inputs={
                "company_name": session.company_name,
                "role_title": session.role_title,
                "job_description_text": session.job_description_text,
                "structured_jd": jd.model_dump(),
                "original_resume_text": session.original_resume_text,
                "required_fields": ["jd_requirements", "jd_keywords", "role_focus", "priority_matrix"],
            },
            skill_names=["jd-analysis", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            analysis = _fallback_analysis(session)
        else:
            analysis = JDAnalysis.model_validate(data)
            if not analysis.jd_keywords:
                analysis.jd_keywords = find_keywords(session.job_description_text)
            if not analysis.role_focus:
                analysis.role_focus = detect_role_focus(session.job_description_text)
        session.jd_analysis = analysis
        return AgentResult(self.name, analysis.model_dump(), ["JD analyzed with LLM prompt and Agent Skill context."])


def _fallback_analysis(session) -> JDAnalysis:
    jd = session.structured_jd
    keywords = find_keywords(session.job_description_text)
    role_focus = detect_role_focus(session.job_description_text)
    resume_text = session.original_resume_text.lower()
    priority_matrix = []
    for kw in keywords:
        evidence = "found in original CV" if kw.lower() in resume_text else "not clearly supported by original CV"
        priority_matrix.append({
            "requirement": kw,
            "priority": "high" if kw in {"Node.js", "Express.js", "RESTful API", "SQL", "ReactJS", "Python"} else "medium",
            "cv_evidence": evidence,
            "action": "emphasize in CV" if evidence.startswith("found") else "show as gap; do not add as a claim",
        })
    return JDAnalysis(
        jd_requirements={
            "must_have": jd.requirements if jd else [],
            "nice_to_have": jd.qualifications if jd else [],
            "soft_skills": [],
        },
        jd_keywords=keywords,
        role_focus=role_focus,
        priority_matrix=priority_matrix,
    )
