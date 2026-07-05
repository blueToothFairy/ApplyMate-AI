from app.utils.text import make_diff


def create_resume_diff(original_resume: str, tailored_resume: str) -> dict:
    return {
        "format": "unified_diff",
        "diff": make_diff(original_resume, tailored_resume),
    }
