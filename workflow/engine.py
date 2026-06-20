from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime
from pathlib import Path

from .model import RunRecord, Stage, WorkflowError
from .storage import FileRunStore


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class WorkflowEngine:
    def __init__(self, workspace: Path):
        self.store = FileRunStore(workspace)

    def new_run(self, title: str, notes: str) -> RunRecord:
        title = compact(title)
        notes = compact(notes)
        if not title or not notes:
            raise WorkflowError("title and notes are required")
        timestamp = utc_now()
        record = RunRecord(
            run_id=f"run-{secrets.token_hex(4)}",
            title=title[:120],
            notes=notes[:10_000],
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._event(record, "run_created")
        self.store.create(record)
        return record

    def process(self, run_id: str) -> tuple[RunRecord, Path | None]:
        record = self.store.load(run_id)
        output_path = None

        while True:
            if record.stage is Stage.INTAKE:
                record.summary = self._summarize(record.notes)
                self._transition(record, Stage.SUMMARY)
            elif record.stage is Stage.SUMMARY:
                record.findings = self._extract_findings(record.notes)
                self._transition(record, Stage.FINDINGS)
            elif record.stage is Stage.FINDINGS:
                record.draft = self._draft(record)
                self._transition(record, Stage.DRAFT)
            elif record.stage is Stage.DRAFT:
                self._transition(record, Stage.REVIEW)
                break
            elif record.stage is Stage.REVIEW:
                break
            elif record.stage is Stage.APPROVED:
                output_path = self.store.write_output(
                    record.run_id, self._final_output(record)
                )
                self._transition(record, Stage.COMPLETE)
                break
            elif record.stage is Stage.COMPLETE:
                output_path = self.store._run_dir(record.run_id) / "final-output.md"
                break

        self.store.save(record)
        return record, output_path

    def approve(self, run_id: str, reviewer: str) -> RunRecord:
        record = self.store.load(run_id)
        reviewer = compact(reviewer)
        if record.stage is not Stage.REVIEW:
            raise WorkflowError("only a run at the review stage can be approved")
        if not reviewer:
            raise WorkflowError("reviewer is required")
        record.approved_by = reviewer[:120]
        self._transition(record, Stage.APPROVED)
        self.store.save(record)
        return record

    def _transition(self, record: RunRecord, stage: Stage) -> None:
        record.stage = stage
        record.updated_at = utc_now()
        self._event(record, f"stage:{stage.value}")

    @staticmethod
    def _event(record: RunRecord, event: str) -> None:
        record.events.append({"at": utc_now(), "event": event})

    @staticmethod
    def _summarize(notes: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", compact(notes))
        return " ".join(sentences[:2])[:500]

    @staticmethod
    def _extract_findings(notes: str) -> list[str]:
        clauses = [
            compact(item)
            for item in re.split(r"[.;]\s*|\n+", notes)
            if compact(item)
        ]
        findings = [item[:240] for item in clauses[:5]]
        return findings or ["No actionable finding was extracted."]

    @staticmethod
    def _draft(record: RunRecord) -> str:
        findings = "\n".join(f"- {item}" for item in record.findings)
        return (
            f"# {record.title}\n\n"
            f"## Summary\n\n{record.summary}\n\n"
            f"## Findings\n\n{findings}\n\n"
            "## Review status\n\nPending human approval.\n"
        )

    @staticmethod
    def _final_output(record: RunRecord) -> str:
        return record.draft.replace(
            "Pending human approval.",
            f"Approved by {record.approved_by}.",
        )
