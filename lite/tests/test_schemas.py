from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from ptlite.files import LoadError, load_contracts, load_definitions, load_silence_log
from ptlite.schemas import Answer, Contract, Level, QuestionKey

CONTRACT = {
    "id": "tx-dir-deloitte-tiers",
    "title": "TIERS maintenance and operations",
    "level": "state",
    "source_url": "https://example.gov/contract.pdf",
    "agency": "Texas DIR",
    "vendor": "Deloitte",
    "system": "TIERS",
    "state": "TX",
    "date": "2020-01-15",
    "obtained_via": "portal",
    "pdf": "pdfs/tx-dir-deloitte-tiers.pdf",
    "related_documents": [
        {"id": "msa", "title": "Master Services Agreement", "kind": "master_agreement"}
    ],
}

QUESTION = {"question": "Q?", "yes": "A clause obliges it", "partial": "", "no": ""}
DEFINITIONS = {"version": "1", "questions": {k.value: dict(QUESTION) for k in QuestionKey}}

HEADER = "agency,request,date_filed,date_answered,outcome,notes,contract_id,url\n"


def write_yaml(tmp_path: Path, name: str, data: object) -> Path:
    p = tmp_path / name
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def write_text(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_answer_values_match_claude_md():
    assert [a.value for a in Answer] == [
        "yes", "partial", "no", "silent", "incomplete", "unverified", "withheld", "no_record",
    ]  # fmt: skip


# --- contracts.yaml ---


def test_valid_contracts_load(tmp_path):
    contracts = load_contracts(write_yaml(tmp_path, "c.yaml", [CONTRACT]))
    assert contracts[0].id == "tx-dir-deloitte-tiers"
    assert contracts[0].related_documents[0].pdf is None


def test_empty_contracts_file_is_empty_list(tmp_path):
    assert load_contracts(write_text(tmp_path, "c.yaml", "")) == []
    assert load_contracts(write_text(tmp_path, "c.yaml", "[]\n")) == []


def test_duplicate_contract_id_rejected(tmp_path):
    with pytest.raises(LoadError, match="duplicate contract id"):
        load_contracts(write_yaml(tmp_path, "c.yaml", [CONTRACT, CONTRACT]))


def test_unknown_field_rejected_and_named(tmp_path):
    bad = {**CONTRACT, "vendr": "typo"}
    with pytest.raises(LoadError, match=r"id=tx-dir-deloitte-tiers.*vendr"):
        load_contracts(write_yaml(tmp_path, "c.yaml", [bad]))


def test_bad_obtained_via_rejected(tmp_path):
    bad = {**CONTRACT, "obtained_via": "email"}
    with pytest.raises(LoadError, match="obtained_via"):
        load_contracts(write_yaml(tmp_path, "c.yaml", [bad]))


def test_bad_id_characters_rejected(tmp_path):
    bad = {**CONTRACT, "id": "TX contract/1"}
    with pytest.raises(LoadError, match="id"):
        load_contracts(write_yaml(tmp_path, "c.yaml", [bad]))


def test_record_status_limited_to_records_values(tmp_path):
    ok = {**CONTRACT, "record_status": "withheld"}
    assert load_contracts(write_yaml(tmp_path, "c.yaml", [ok]))[0].record_status == "withheld"
    bad = {**CONTRACT, "record_status": "silent"}
    with pytest.raises(LoadError, match="record_status"):
        load_contracts(write_yaml(tmp_path, "c.yaml", [bad]))


def test_top_level_must_be_list(tmp_path):
    with pytest.raises(LoadError, match="expected a list"):
        load_contracts(write_yaml(tmp_path, "c.yaml", {"contracts": []}))


def test_missing_file(tmp_path):
    with pytest.raises(LoadError, match="file not found"):
        load_contracts(tmp_path / "nope.yaml")


def test_federal_contract_needs_no_state():
    c = Contract.model_validate({**CONTRACT, "level": "federal", "state": None})
    assert c.level is Level.FEDERAL


def test_state_contract_needs_state():
    with pytest.raises(ValidationError, match="state is required"):
        Contract.model_validate({**CONTRACT, "level": "state", "state": None})


# --- definitions.yaml ---


def test_valid_definitions_load(tmp_path):
    d = load_definitions(write_yaml(tmp_path, "d.yaml", DEFINITIONS))
    assert d.version == "1"
    assert set(d.questions) == set(QuestionKey)


def test_bare_yes_no_keys_are_strings(tmp_path):
    # YAML 1.1 reads bare yes/no as booleans; hand-written files use them unquoted.
    body = "".join(
        f"  {k.value}:\n    question: Q?\n    yes: Y\n    partial: P\n    no: N\n"
        for k in QuestionKey
    )
    d = load_definitions(write_text(tmp_path, "d.yaml", 'version: "1"\nquestions:\n' + body))
    assert d.questions[QuestionKey.KNOW].yes == "Y"
    assert d.questions[QuestionKey.KNOW].no == "N"


def test_true_false_still_booleans(tmp_path):
    from ptlite.files import _read_yaml

    assert _read_yaml(write_text(tmp_path, "x.yaml", "a: true\nb: no\n")) == {"a": True, "b": "no"}


def test_shipped_files_validate():
    # The real hand-written files in lite/ must always pass validation.
    from ptlite.cli import DEFAULT_DIR, validate

    assert validate(DEFAULT_DIR) == 0


def test_integer_version_read_as_string(tmp_path):
    d = load_definitions(write_yaml(tmp_path, "d.yaml", {**DEFINITIONS, "version": 2}))
    assert d.version == "2"


def test_missing_version_rejected(tmp_path):
    data = {"questions": DEFINITIONS["questions"]}
    with pytest.raises(LoadError, match="version"):
        load_definitions(write_yaml(tmp_path, "d.yaml", data))


def test_missing_question_rejected(tmp_path):
    qs = {k: v for k, v in DEFINITIONS["questions"].items() if k != "leave"}
    with pytest.raises(LoadError, match="missing question.*leave"):
        load_definitions(write_yaml(tmp_path, "d.yaml", {"version": "1", "questions": qs}))


def test_extra_question_rejected(tmp_path):
    qs = {**DEFINITIONS["questions"], "pay": dict(QUESTION)}
    with pytest.raises(LoadError, match="pay"):
        load_definitions(write_yaml(tmp_path, "d.yaml", {"version": "1", "questions": qs}))


def test_empty_yes_criterion_rejected(tmp_path):
    qs = {**DEFINITIONS["questions"], "know": {**QUESTION, "yes": ""}}
    with pytest.raises(LoadError, match="know.yes"):
        load_definitions(write_yaml(tmp_path, "d.yaml", {"version": "1", "questions": qs}))


# --- silence_log.csv ---


def test_header_only_log_is_empty(tmp_path):
    assert load_silence_log(write_text(tmp_path, "s.csv", HEADER)) == []


def test_valid_log_rows(tmp_path):
    text = HEADER + (
        "Texas DIR,TIERS contract,2026-11-18,,pending,,tx-dir-deloitte-tiers,\n"
        "\n"
        "Michigan DTMB,MiDAS contract,2026-11-18,2026-12-01,refused,trade secret,,\n"
    )
    rows = load_silence_log(write_text(tmp_path, "s.csv", text))
    assert [r.outcome for r in rows] == ["pending", "refused"]
    assert rows[0].date_answered is None and rows[1].contract_id is None


def test_optional_columns_may_be_absent(tmp_path):
    text = "agency,request,date_filed,date_answered,outcome,notes\nA,B,2026-11-18,,pending,\n"
    assert len(load_silence_log(write_text(tmp_path, "s.csv", text))) == 1


def test_bad_outcome_rejected_with_line(tmp_path):
    text = HEADER + "A,B,2026-11-18,,denied,,,\n"
    with pytest.raises(LoadError, match=r"(?s)line 2.*outcome"):
        load_silence_log(write_text(tmp_path, "s.csv", text))


def test_unknown_column_rejected(tmp_path):
    with pytest.raises(LoadError, match="unknown column.*status"):
        load_silence_log(write_text(tmp_path, "s.csv", HEADER.strip() + ",status\n"))


def test_missing_column_rejected(tmp_path):
    with pytest.raises(LoadError, match="missing column.*outcome"):
        load_silence_log(write_text(tmp_path, "s.csv", "agency,request,date_filed\n"))


def test_answered_before_filed_rejected(tmp_path):
    text = HEADER + "A,B,2026-11-18,2026-11-01,provided,,,\n"
    with pytest.raises(LoadError, match="before date_filed"):
        load_silence_log(write_text(tmp_path, "s.csv", text))


def test_too_many_fields_rejected(tmp_path):
    text = HEADER + "A,B,2026-11-18,,pending,,,,extra\n"
    with pytest.raises(LoadError, match="more fields"):
        load_silence_log(write_text(tmp_path, "s.csv", text))
