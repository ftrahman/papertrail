"""Load and validate the hand-written files in lite/.

Each loader returns validated models or raises LoadError with one message naming
the file, the entry or row, and the field at fault.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml
from pydantic import ValidationError

from .schemas import (
    SILENCE_LOG_OPTIONAL,
    SILENCE_LOG_REQUIRED,
    Contract,
    ContractsFile,
    Definitions,
    SilenceLogRow,
)


class LoadError(Exception):
    pass


def _describe(err: ValidationError, path: Path, where: str = "") -> str:
    lines = []
    for e in err.errors():
        loc = ".".join(str(p) for p in e["loc"]) or "(top level)"
        lines.append(f"  {loc}: {e['msg']}")
    head = f"{path}{f' ({where})' if where else ''}: invalid"
    return "\n".join([head, *lines])


def _read_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise LoadError(f"{path}: file not found") from e
    except yaml.YAMLError as e:
        raise LoadError(f"{path}: not valid YAML: {e}") from e


def load_contracts(path: Path) -> list[Contract]:
    """contracts.yaml is a top-level list of contract entries (empty is allowed)."""
    data = _read_yaml(path)
    if data is None:
        data = []
    if not isinstance(data, list):
        raise LoadError(f"{path}: expected a list of contracts at the top level")
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise LoadError(f"{path} (entry {i + 1}): expected a mapping")
    try:
        return ContractsFile(contracts=data).contracts
    except ValidationError as e:
        # Name the entry by its id where we can, not just its index.
        lines = []
        for err in e.errors():
            loc = list(err["loc"])
            if len(loc) >= 2 and loc[0] == "contracts" and isinstance(loc[1], int):
                idx = loc[1]
                cid = data[idx].get("id", "?")
                field = ".".join(str(p) for p in loc[2:]) or "(entry)"
                lines.append(f"  entry {idx + 1} (id={cid}): {field}: {err['msg']}")
            else:
                lines.append(f"  {err['msg']}")
        raise LoadError("\n".join([f"{path}: invalid", *lines])) from e


def load_definitions(path: Path) -> Definitions:
    data = _read_yaml(path)
    if not isinstance(data, dict):
        raise LoadError(f"{path}: expected a mapping with 'version' and 'questions'")
    try:
        return Definitions.model_validate(data)
    except ValidationError as e:
        raise LoadError(_describe(e, path)) from e


def load_silence_log(path: Path) -> list[SilenceLogRow]:
    try:
        f = path.open(newline="", encoding="utf-8")
    except FileNotFoundError as e:
        raise LoadError(f"{path}: file not found") from e
    with f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing = [c for c in SILENCE_LOG_REQUIRED if c not in header]
        unknown = [c for c in header if c not in SILENCE_LOG_REQUIRED + SILENCE_LOG_OPTIONAL]
        if missing or unknown:
            parts = []
            if missing:
                parts.append(f"missing column(s): {', '.join(missing)}")
            if unknown:
                parts.append(f"unknown column(s): {', '.join(unknown)}")
            raise LoadError(f"{path}: bad header: {'; '.join(parts)}")
        rows = []
        for row in reader:
            if None in row:
                raise LoadError(f"{path} (line {reader.line_num}): more fields than columns")
            if not any((v or "").strip() for v in row.values()):
                continue  # skip blank lines
            try:
                rows.append(SilenceLogRow.model_validate(row))
            except ValidationError as e:
                raise LoadError(_describe(e, path, f"line {reader.line_num}")) from e
        return rows
