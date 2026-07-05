from __future__ import annotations

from pathlib import Path


class SkillLoader:
    """Loads Agent Skills from the local `.skills/` folder.

    The model receives only relevant skills, not the entire project context. This keeps
    prompts smaller while still making resume/JD/email/safety playbooks available.
    """

    def __init__(self, skills_root: str | Path = ".skills") -> None:
        self.skills_root = Path(skills_root)
        if not self.skills_root.exists():
            # When uvicorn is started from another working directory, resolve relative to project root.
            candidate = Path(__file__).resolve().parents[2] / ".skills"
            self.skills_root = candidate if candidate.exists() else Path(skills_root)

    def list_skills(self) -> list[dict]:
        skills = []
        if not self.skills_root.exists():
            return skills
        for skill_dir in sorted(self.skills_root.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            skills.append({
                "name": skill_dir.name,
                "path": str(skill_dir),
                "summary": content[:800],
            })
        return skills

    def read_skill(self, name: str) -> str:
        path = self.skills_root / name / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"Skill not found: {name}")
        return path.read_text(encoding="utf-8")

    def read_skill_bundle(self, name: str) -> str:
        root = self.skills_root / name
        skill_md = root / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"Skill not found: {name}")
        parts = [f"# Skill: {name}", skill_md.read_text(encoding="utf-8")]
        for subdir in ["references", "assets"]:
            folder = root / subdir
            if not folder.exists():
                continue
            for file in sorted(folder.rglob("*")):
                if file.is_file() and file.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}:
                    try:
                        parts.append(f"\n## {subdir}/{file.name}\n{file.read_text(encoding='utf-8')}")
                    except UnicodeDecodeError:
                        continue
        return "\n\n".join(parts)
