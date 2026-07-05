from __future__ import annotations

from typing import Dict
from app.models import ApplicationSession, AuditEvent
from app.utils.ids import make_id


class InMemoryApplicationStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, ApplicationSession] = {}

    def create(self, session: ApplicationSession) -> ApplicationSession:
        self._sessions[session.application_id] = session
        return session

    def get(self, application_id: str) -> ApplicationSession:
        try:
            return self._sessions[application_id]
        except KeyError as exc:
            raise KeyError(f"Application session not found: {application_id}") from exc

    def save(self, session: ApplicationSession) -> ApplicationSession:
        self._sessions[session.application_id] = session
        return session

    def add_audit(self, application_id: str, action: str, detail: dict) -> AuditEvent:
        session = self.get(application_id)
        event = AuditEvent(event_id=make_id("audit"), action=action, detail=detail)
        session.audit_events.append(event)
        self.save(session)
        return event

    def list(self) -> list[ApplicationSession]:
        return list(self._sessions.values())


store = InMemoryApplicationStore()
