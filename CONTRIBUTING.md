# Contributing

## Project philosophy

This project is a small executable architecture artifact. Keep additions deterministic, testable, and honest about their boundary.

Do not add a new technology merely because it is fashionable. New components must explain which institutional constraint they solve.

## Local setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
python scripts/publication_check.py
```

## Repository architecture

Core implementation lives in `src/digital_collateral`. Tests live in `tests`. Architecture and model notes live in `docs`.

## Adding a new scenario

Add a `Scenario` to `src/digital_collateral/scenarios.py`, add expected state and evidence assertions in `tests/test_core.py`, and update README scenario tables if the scenario is publication-relevant.

## Adding a new collateral adapter

Keep adapters synthetic unless a live integration is explicitly scoped. Document the source, data boundary, failure state, and evidence status.

## Adding a new evidence type

Evidence must include deterministic serialization, integrity hashing, verifier logic, and a false-verification test.

## Documentation standards

Claims must be reproducible by a command or bounded as interpretation. Do not imply endorsement, production readiness, regulatory compliance, or audit assurance.

## Research-source standards

Use public sources, link them directly, and separate source description from architectural interpretation.

## Pull requests

Include tests for core logic, keep dependencies minimal, and run `python scripts/publication_check.py` before opening a PR.
