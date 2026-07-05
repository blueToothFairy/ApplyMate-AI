from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.agents.workflow import workflow
from app.models import GenerateRequest
from app.utils.text import detect_prompt_injection


async def main() -> None:
    cases = json.loads(Path("evals/eval_cases.json").read_text(encoding="utf-8"))
    results = []
    for case in cases:
        response = await workflow.generate(GenerateRequest(
            resume_text=case["resume_text"],
            job_description_text=case["job_description_text"],
            company_name=case.get("company_name", ""),
            role_title=case.get("role_title", ""),
            recipient_email=case.get("recipient_email"),
        ))
        app = response.application
        version = next(v for v in app.tailored_resume_versions if v.version_id == app.selected_resume_version_id)
        passed = True
        notes = []
        expected = case.get("expected", {})
        if "min_score" in expected and version.match_score < expected["min_score"]:
            passed = False
            notes.append(f"score {version.match_score} < expected {expected['min_score']}")
        if expected.get("prompt_injection_detected") and not detect_prompt_injection(case["job_description_text"]):
            passed = False
            notes.append("prompt injection was not detected")
        if "must_not_claim" in expected and expected["must_not_claim"].lower() in version.content.lower():
            passed = False
            notes.append(f"unsupported claim present: {expected['must_not_claim']}")
        results.append({"case_id": case["case_id"], "passed": passed, "notes": notes})
    print(json.dumps(results, indent=2))
    if not all(r["passed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
