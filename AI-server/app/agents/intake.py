from app.agents.base import BaseAgent, AgentResult
from app.models import ApplicationSession
from app.utils.ids import make_id


class IntakeAgent(BaseAgent):
    name = "IntakeAgent"

    async def run(self, state: dict) -> AgentResult:
        request = state["request"]
        missing = []
        if not request.resume_text.strip():
            missing.append("resume_text")
        if not request.job_description_text.strip():
            missing.append("job_description_text")
        if missing:
            raise ValueError(f"Missing required input: {', '.join(missing)}")

        session = ApplicationSession(
            application_id=make_id("app"),
            original_resume_text=request.resume_text,
            job_description_text=request.job_description_text,
            company_name=getattr(request, "company_name", "") or "",
            role_title=getattr(request, "role_title", "") or "",
            recipient_email=getattr(request, "recipient_email", None),
        )
        state["session"] = session
        return AgentResult(self.name, session, ["Input normalized into an application session."])
