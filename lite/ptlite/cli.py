"""ptlite command line."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from .files import LoadError, load_contracts, load_definitions, load_silence_log

# The editable install puts this package at lite/ptlite, so lite/ is the default data dir.
DEFAULT_DIR = Path(__file__).resolve().parent.parent


def validate(lite_dir: Path) -> int:
    """Check the hand-written files. Returns a process exit code."""
    errors: list[str] = []

    contracts = []
    try:
        contracts = load_contracts(lite_dir / "contracts.yaml")
    except LoadError as e:
        errors.append(str(e))
    for c in contracts:
        pdfs = [(c.id, c.pdf)] + [(f"{c.id}/{d.id}", d.pdf) for d in c.related_documents]
        for label, pdf in pdfs:
            if pdf and not (lite_dir / pdf).is_file():
                errors.append(f"contracts.yaml ({label}): pdf not found: {pdf}")

    definitions = None
    try:
        definitions = load_definitions(lite_dir / "definitions.yaml")
    except LoadError as e:
        errors.append(str(e))

    requests = []
    try:
        requests = load_silence_log(lite_dir / "silence_log.csv")
    except LoadError as e:
        errors.append(str(e))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    assert definitions is not None  # loading failed only if errors is non-empty

    outcomes = Counter(r.outcome.value for r in requests)
    by_outcome = ", ".join(f"{n} {o}" for o, n in sorted(outcomes.items())) or "none"
    missing = sum(1 for c in contracts for d in c.related_documents if d.pdf is None)
    print(f"contracts:    {len(contracts)}")
    if missing:
        print(f"              {missing} related document(s) without a pdf")
    print(f"definitions:  version {definitions.version}")
    print(f"records requests: {len(requests)} ({by_outcome})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ptlite")
    sub = parser.add_subparsers(dest="command", required=True)
    p_val = sub.add_parser("validate", help="check the hand-written files in lite/")
    p_val.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="the lite/ directory")
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate(args.dir)
    return 2


if __name__ == "__main__":
    sys.exit(main())
