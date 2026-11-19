import pymupdf

from ptlite.extract import extract


def make_pdf(path, pages):
    doc = pymupdf.open()
    for text in pages:
        doc.new_page().insert_text((72, 72), text)
    doc.save(path)


def test_blank_pdf_not_silent(tmp_path):
    make_pdf(tmp_path / "scan.pdf", ["", ""])
    assert extract(tmp_path / "scan.pdf", "scan").needs_ocr
