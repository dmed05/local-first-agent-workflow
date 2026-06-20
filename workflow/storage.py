from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .model import RunRecord, WorkflowError


class FileRunStore:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_id: str) -> Path:
        if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in run_id):
            raise WorkflowError("run_id contains invalid characters")
        run_dir = (self.workspace / run_id).resolve()
        if self.workspace not in run_dir.parents:
            raise WorkflowError("run_id escapes workspace")
        return run_dir

    def create(self, record: RunRecord) -> None:
        run_dir = self._run_dir(record.run_id)
        if run_dir.exists():
            raise WorkflowError(f"run already exists: {record.run_id}")
        run_dir.mkdir(parents=True)
        self.save(record)

    def load(self, run_id: str) -> RunRecord:
        state_path = self._run_dir(run_id) / "state.json"
        if not state_path.exists():
            raise WorkflowError(f"run not found: {run_id}")
        return RunRecord.from_dict(json.loads(state_path.read_text(encoding="utf-8")))

    def save(self, record: RunRecord) -> None:
        run_dir = self._run_dir(record.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        state_path = run_dir / "state.json"
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=run_dir,
            delete=False,
        ) as handle:
            json.dump(record.to_dict(), handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary = Path(handle.name)
        os.replace(temporary, state_path)

    def write_output(self, run_id: str, content: str) -> Path:
        output_path = self._run_dir(run_id) / "final-output.md"
        output_path.write_text(content, encoding="utf-8")
        return output_path
