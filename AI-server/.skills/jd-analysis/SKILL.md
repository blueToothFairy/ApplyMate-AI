---
name: jd-analysis
description: |
  Analyzes job descriptions to extract requirements, keywords, role focus, and priority matrix.
  Use when parsing or scoring JD fit.
  Do NOT use to change the user's resume directly.
---

# JD Analysis Skill

Output four structured objects:

1. `jd_requirements`: must-have, nice-to-have, soft skills.
2. `jd_keywords`: role-specific keywords.
3. `role_focus`: backend/frontend/fullstack/data/AI/QA/DevOps and seniority.
4. `priority_matrix`: requirement priority, CV evidence, and recommended action.

Classify requirements carefully:

- Must-have: explicit requirements, repeated skills, core responsibility skills.
- Nice-to-have: "plus", "preferred", "advantage", "bonus".
- Soft skills: communication, teamwork, learning, ownership.
