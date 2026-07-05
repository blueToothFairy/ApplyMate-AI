from app.agents.base import BaseAgent, AgentResult
from app.services.document_service import parse_resume_text, parse_jd_text
from app.models import ApplicationStatus


class DocumentParserAgent(BaseAgent):
    name = "DocumentParserAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        session.structured_resume = parse_resume_text(session.original_resume_text)
        session.structured_jd = parse_jd_text(session.job_description_text)
        session.status = ApplicationStatus.parsed
        return AgentResult(self.name, {
            "structured_resume": session.structured_resume.model_dump(),
            "structured_jd": session.structured_jd.model_dump(),
        }, ["Parsed CV and JD into structured data."])
