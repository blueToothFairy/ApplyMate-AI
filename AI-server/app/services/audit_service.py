from app.store import store


def log_audit_event(application_id: str, action: str, detail: dict) -> dict:
    event = store.add_audit(application_id, action, detail)
    return event.model_dump()
