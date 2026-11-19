import hashlib
from pathlib import Path

import pymupdf
from pydantic import BaseModel

MIN_CHARS_PER_PAGE = 50  # below 50 chars, treat as no text


class Page(BaseModel):
    number: int
    text: str


class ExtractedDoc(BaseModel):
    doc_id: str
    file_sha: str
    pages: list[Page]
    needs_ocr: bool


def extract(pdf: Path, doc_id: str) -> ExtractedDoc:
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    with pymupdf.open(pdf) as doc:
        pages = [
            Page(number=index + 1, text=page.get_text())  # starts at page two, keep in mind
            for index, page in enumerate(doc.pages(), start=1)
        ]
        empty = sum(len(page.text.strip()) < MIN_CHARS_PER_PAGE for page in pages)
        return ExtractedDoc(
            doc_id=doc_id, file_sha=digest, pages=pages, needs_ocr=empty > len(pages) / 2
        )
