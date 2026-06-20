from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from workflow import Stage, WorkflowEngine, WorkflowError


class WorkflowEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.engine = WorkflowEngine(self.workspace)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_processing_stops_for_human_review(self) -> None:
        record = self.engine.new_run(
            "Synthetic handoff",
            "The example team needs a named owner. The handoff needs a checklist.",
        )
        processed, output = self.engine.process(record.run_id)
        self.assertEqual(processed.stage, Stage.REVIEW)
        self.assertIsNone(output)
        self.assertTrue(processed.summary)
        self.assertGreaterEqual(len(processed.findings), 1)

    def test_approval_is_required_before_final_output(self) -> None:
        record = self.engine.new_run("Synthetic review", "Document the review gate.")
        with self.assertRaises(WorkflowError):
            self.engine.approve(record.run_id, "Reviewer")

        reviewed, _ = self.engine.process(record.run_id)
        approved = self.engine.approve(reviewed.run_id, "Portfolio Reviewer")
        self.assertEqual(approved.stage, Stage.APPROVED)

        completed, output = self.engine.process(approved.run_id)
        self.assertEqual(completed.stage, Stage.COMPLETE)
        self.assertIsNotNone(output)
        self.assertIn("Approved by Portfolio Reviewer", output.read_text())

    def test_owner_supplied_run_id_cannot_escape_workspace(self) -> None:
        with self.assertRaises(WorkflowError):
            self.engine.store.load("../../outside")


if __name__ == "__main__":
    unittest.main()
