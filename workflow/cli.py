from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import WorkflowEngine
from .model import WorkflowError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Run a local staged workflow")
    commands = root.add_subparsers(dest="command", required=True)

    new = commands.add_parser("new-run")
    new.add_argument("--workspace", type=Path, required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--notes", required=True)

    process = commands.add_parser("process")
    process.add_argument("--workspace", type=Path, required=True)
    process.add_argument("--run-id", required=True)

    approve = commands.add_parser("approve")
    approve.add_argument("--workspace", type=Path, required=True)
    approve.add_argument("--run-id", required=True)
    approve.add_argument("--reviewer", required=True)

    status = commands.add_parser("status")
    status.add_argument("--workspace", type=Path, required=True)
    status.add_argument("--run-id", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    engine = WorkflowEngine(args.workspace)

    try:
        if args.command == "new-run":
            record = engine.new_run(args.title, args.notes)
            print(json.dumps(record.to_dict(), indent=2))
        elif args.command == "process":
            record, output = engine.process(args.run_id)
            payload = record.to_dict()
            payload["output"] = str(output) if output else None
            print(json.dumps(payload, indent=2))
        elif args.command == "approve":
            record = engine.approve(args.run_id, args.reviewer)
            print(json.dumps(record.to_dict(), indent=2))
        else:
            print(json.dumps(engine.store.load(args.run_id).to_dict(), indent=2))
    except WorkflowError as error:
        parser().error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
