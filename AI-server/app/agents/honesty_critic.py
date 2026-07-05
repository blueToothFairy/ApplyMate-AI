from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent, AgentResult
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider
from app.utils.text import find_keywords


class HonestyCriticAgent(BaseAgent):
    name = "HonestyCriticAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        version = next(v for v in session.tailored_resume_versions if v.version_id == session.selected_resume_version_id)

        schema: dict[str, Any] = {
            "type": "object",
            "required": ["status", "risky_claims", "notes", "safe_rewrite_suggestions"],
            "properties": {
                "status": {"type": "string", "enum": ["pass", "needs_review", "fail"]},
                "risky_claims": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "array", "items": {"type": "string"}},
                "safe_rewrite_suggestions": {"type": "array", "items": {"type": "string"}},
            },
        }
        system, prompt = build_json_prompt(
            task=(
                "Audit the tailored CV for honesty. Compare it against the original CV and JD. "
                "Flag claims that appear fabricated, unsupported, over-specific, or too strong. "
                "Do not penalize normal wording improvements that preserve the original meaning."
            ),
            schema=schema,
            inputs={
                "original_resume_text": session.original_resume_text,
                "job_description_text": session.job_description_text,
                "tailored_resume": version.content,
                "jd_analysis": session.jd_analysis.model_dump() if session.jd_analysis else {},
                "tailoring_strategy": session.tailoring_strategy.model_dump() if session.tailoring_strategy else {},
            },
            skill_names=["resume-tailoring", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            report = _fallback_report(session, version.content)
        else:
            report = {
                "status": data.get("status", "needs_review"),
                "risky_claims": data.get("risky_claims", []),
                "notes": data.get("notes", []),
                "safe_rewrite_suggestions": data.get("safe_rewrite_suggestions", []),
            }
            # Add a deterministic keyword-level safety net.
            deterministic = _fallback_report(session, version.content)
            merged_risks = sorted(set(report.get("risky_claims", [])) | set(deterministic.get("risky_claims", [])))
            report["risky_claims"] = merged_risks
            if merged_risks and report["status"] == "pass":
                report["status"] = "needs_review"
            report["notes"] = list(report.get("notes", [])) + deterministic.get("notes", [])[:1]
        version.honesty_report = report
        return AgentResult(self.name, report, ["Honesty guardrail completed with LLM critique and deterministic safety check."])


def _fallback_report(session, tailored_text: str) -> dict[str, Any]:
    original_keywords = set(find_keywords(session.original_resume_text))
    tailored_keywords = set(find_keywords(tailored_text))
    unsupported = sorted(tailored_keywords - original_keywords)
    jd_keywords = set(session.jd_analysis.jd_keywords if session.jd_analysis else [])
    risky_claims = [kw for kw in unsupported if kw in jd_keywords]
    return {
        "status": "pass" if not risky_claims else "needs_review",
        "risky_claims": risky_claims,
        "notes": [
            "The CV should not claim unsupported skills from the JD.",
            "Unsupported skills may appear in gap analysis, not as direct CV claims.",
        ],
        "safe_rewrite_suggestions": [],
    }
