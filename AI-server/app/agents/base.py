from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentResult:
    name: str
    output: Any
    notes: list[str]


class BaseAgent:
    name = "BaseAgent"

    async def run(self, state: dict) -> AgentResult:
        raise NotImplementedError
