from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Capability:
    name: str
    description: str
    parameters: dict
    examples: list[str] = field(default_factory=list)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, cap: Capability) -> None:
        self._capabilities[cap.name] = cap

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def list_names(self) -> list[str]:
        return list(self._capabilities.keys())

    def export_schema(self) -> list[dict]:
        return [
            {
                "name": c.name,
                "description": c.description,
                "parameters": c.parameters,
                "examples": c.examples,
            }
            for c in self._capabilities.values()
        ]
