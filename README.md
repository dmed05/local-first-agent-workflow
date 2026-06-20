# Local-First Agent Workflow

A generic, staged workflow engine for turning unstructured intake notes into a
reviewed deliverable without sending source data to an external service.

The repository demonstrates the operational layer around AI automation:
explicit stage contracts, durable run state, validation, human approval, and
safe publication boundaries. The included processor is deterministic so the
project works without credentials.

## Workflow

```text
intake
  ↓
summary
  ↓
key findings
  ↓
draft output
  ↓
human review gate
  ↓
approved final output
```

Every run stores:

- its current stage;
- structured inputs and outputs;
- validation errors;
- approval state;
- an append-only event log.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m unittest discover -s tests

python -m workflow.cli new-run \
  --workspace .demo-runs \
  --title "Synthetic onboarding review" \
  --notes "The example team needs a documented handoff and owner."

python -m workflow.cli process \
  --workspace .demo-runs \
  --run-id <run-id>
```

The first processing pass stops at `review`. Approve it explicitly:

```bash
python -m workflow.cli approve \
  --workspace .demo-runs \
  --run-id <run-id> \
  --reviewer "Portfolio Reviewer"

python -m workflow.cli process \
  --workspace .demo-runs \
  --run-id <run-id>
```

The final Markdown artifact is written inside the run directory.

## Design choices

- Local files are the system of record.
- Stage transitions are validated and cannot skip the review gate.
- No network calls or API keys are required.
- The `runs/`, `outputs/`, and `private/` paths are ignored.
- Synthetic fixtures are committed; operational records are prohibited.
- The same publication scan runs locally and in GitHub Actions.

An AI provider can later replace the deterministic summary and findings
functions without changing the state machine or approval contract.

## License

MIT
