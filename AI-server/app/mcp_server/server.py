"""Optional MCP server entrypoint.

Run with:
    python -m app.mcp_server.server

This exposes selected ApplyMate tool functions through MCP for demonstration.
The final email sending action intentionally remains outside this AI server.
"""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover
    FastMCP = None

from app.mcp_server import tools


def build_mcp_server():
    if FastMCP is None:
        raise RuntimeError("mcp package is not installed. Install requirements.txt first.")
    mcp = FastMCP("applymate-ai-mcp")

    mcp.tool()(tools.parse_resume)
    mcp.tool()(tools.parse_job_description)
    mcp.tool()(tools.analyze_resume_jd_fit)
    mcp.tool()(tools.generate_tailored_resume)
    mcp.tool()(tools.create_email_draft)
    mcp.tool()(tools.revise_application)
    mcp.tool()(tools.create_resume_diff_tool)
    mcp.tool()(tools.score_resume_against_jd)
    mcp.tool()(tools.create_review_bundle)
    mcp.tool()(tools.validate_send_policy_tool)
    mcp.tool()(tools.log_audit_event)
    mcp.tool()(tools.send_application_email)
    return mcp


mcp = build_mcp_server() if FastMCP is not None else None


if __name__ == "__main__":
    if mcp is None:
        raise RuntimeError("MCP server cannot start because mcp package is unavailable.")
    mcp.run()
