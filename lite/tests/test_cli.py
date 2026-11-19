from pathlib import Path

import yaml

from ptlite.cli import main
from ptlite.schemas import QuestionKey

HEADER = "agency,request,date_filed,date_answered,outcome,notes,contract_id,url\n"

CONTRACT = {
    "id": "c1",
    "title": "Contract one",
    "level": "state",
    "agency": "Agency",
    "vendor": "Vendor",
    "system": "System",
    "state": "TX",
    "date": "2020-01-01",
    "obtained_via": "portal",
}


def make_dir(tmp_path: Path, contracts=None, log_rows: str = "") -> Path:
    q = {"question": "Q?", "yes": "Y"}
    defs = {"version": "1", "questions": {k.value: q for k in QuestionKey}}
    (tmp_path / "definitions.yaml").write_text(yaml.safe_dump(defs))
    (tmp_path / "contracts.yaml").write_text(yaml.safe_dump(contracts or []))
    (tmp_path / "silence_log.csv").write_text(HEADER + log_rows)
    return tmp_path


def test_validate_good_dir(tmp_path, capsys):
    d = make_dir(tmp_path, [CONTRACT], "Agency,Contract one,2026-11-18,,pending,,c1,\n")
    assert main(["validate", "--dir", str(d)]) == 0
    out = capsys.readouterr().out
    assert "contracts:    1" in out
    assert "version 1" in out
    assert "1 pending" in out


def test_validate_empty_templates(tmp_path, capsys):
    assert main(["validate", "--dir", str(make_dir(tmp_path))]) == 0
    assert "contracts:    0" in capsys.readouterr().out


def test_validate_bad_dir_names_field(tmp_path, capsys):
    d = make_dir(tmp_path, [{**CONTRACT, "obtained_via": "email"}])
    assert main(["validate", "--dir", str(d)]) == 1
    err = capsys.readouterr().err
    assert "id=c1" in err and "obtained_via" in err


def test_validate_reports_every_file(tmp_path, capsys):
    d = make_dir(tmp_path, [{**CONTRACT, "vendr": "x"}], "A,B,2026-11-18,,denied,,,\n")
    (d / "definitions.yaml").unlink()
    assert main(["validate", "--dir", str(d)]) == 1
    err = capsys.readouterr().err
    assert "vendr" in err and "definitions.yaml: file not found" in err and "outcome" in err
    assert "3 problem(s)" in err


def test_validate_missing_pdf(tmp_path, capsys):
    contract = {
        **CONTRACT,
        "pdf": "pdfs/c1.pdf",
        "related_documents": [{"id": "ex-a", "title": "Exhibit A", "kind": "exhibit"}],
    }
    d = make_dir(tmp_path, [contract])
    assert main(["validate", "--dir", str(d)]) == 1
    assert "pdf not found: pdfs/c1.pdf" in capsys.readouterr().err

    (d / "pdfs").mkdir()
    (d / "pdfs" / "c1.pdf").write_bytes(b"%PDF-1.4")
    assert main(["validate", "--dir", str(d)]) == 0
    assert "1 related document(s) without a pdf" in capsys.readouterr().out
