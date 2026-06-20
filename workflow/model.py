from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Stage(StrEnum):
    INTAKE = "intake"
    SUMMARY = "summary"
    FINDINGS = "findings"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    COMPLETE = "complete"


class WorkflowError(ValueError):
    """Raised when a workflow transition or record is invalid."""


@dataclass
class RunRecord:
    run_id: str
    title: str
    notes: str
    stage: Stage = Stage.INTAKE
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    draft: str = ""
    approved_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = self.__dict__.copy()
        payload["stage"] = self.stage.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunRecord":
        return cls(
            run_id=str(payload["run_id"]),
            title=str(payload["title"]),
            notes=str(payload["notes"]),
            stage=Stage(payload.get("stage", Stage.INTAKE)),
            summary=str(payload.get("summary", "")),
            findings=[str(item) for item in payload.get("findings", [])],
            draft=str(payload.get("draft", "")),
            approved_by=str(payload.get("approved_by", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            events=list(payload.get("events", [])),
        )
