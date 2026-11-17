"""Pydantic schemas for the hand-written files in lite/.

Every model forbids unknown fields, so a typo in contracts.yaml, definitions.yaml,
or silence_log.csv fails loudly instead of being silently dropped.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Ids become file names (text/<id>.json), so keep them to a safe character set.
Id = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")]
NonEmpty = Annotated[str, Field(min_length=1)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Answer(StrEnum):
    YES = "yes"
    PARTIAL = "partial"
    NO = "no"
    SILENT = "silent"
    INCOMPLETE = "incomplete"
    UNVERIFIED = "unverified"
    WITHHELD = "withheld"
    NO_RECORD = "no_record"


class QuestionKey(StrEnum):
    KNOW = "know"
    SHOW = "show"
    TEST = "test"
    ACT = "act"
    LEAVE = "leave"


class ObtainedVia(StrEnum):
    PORTAL = "portal"
    RECORDS_REQUEST = "records_request"
    ARCHIVE = "archive"


class RecordStatus(StrEnum):
    """Per-contract statuses from records requests, never produced by the model."""

    WITHHELD = "withheld"
    NO_RECORD = "no_record"


class RelatedKind(StrEnum):
    MASTER_AGREEMENT = "master_agreement"
    EXHIBIT = "exhibit"
    ADDENDUM = "addendum"
    AMENDMENT = "amendment"


class RequestOutcome(StrEnum):
    PROVIDED = "provided"
    REDACTED = "redacted"
    REFUSED = "refused"
    NO_RECORD = "no_record"
    PENDING = "pending"


# --- contracts.yaml ---------------------------------------------------------


class RelatedDocument(Strict):
    """A document the contract incorporates or that amends it.

    The contract and its related documents are read together as one contract family.
    `pdf` is None when we don't have the document; a missing incorporated document
    blocks a `silent` answer (the answer becomes `incomplete`).
    """

    id: Id
    title: NonEmpty
    kind: RelatedKind
    source_url: str | None = None
    pdf: str | None = None


class Contract(Strict):
    id: Id
    title: NonEmpty
    source_url: str | None = None
    agency: NonEmpty
    vendor: NonEmpty
    system: NonEmpty
    state: NonEmpty
    date: dt.date
    obtained_via: ObtainedVia
    pdf: str | None = None
    related_documents: list[RelatedDocument] = Field(default_factory=list)
    record_status: RecordStatus | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _unique_related_ids(self) -> Contract:
        ids = [d.id for d in self.related_documents]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate related document id(s): {', '.join(dupes)}")
        return self


class ContractsFile(Strict):
    contracts: list[Contract]

    @model_validator(mode="after")
    def _unique_ids(self) -> ContractsFile:
        ids = [c.id for c in self.contracts]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate contract id(s): {', '.join(dupes)}")
        return self


# --- definitions.yaml -------------------------------------------------------


class QuestionDefinition(Strict):
    question: NonEmpty
    yes: NonEmpty
    partial: str = ""
    no: str = ""


class Definitions(Strict):
    version: NonEmpty
    questions: dict[QuestionKey, QuestionDefinition]

    @field_validator("version", mode="before")
    @classmethod
    def _version_as_str(cls, v: object) -> object:
        # YAML reads `version: 1` as an int; the version is an identifier, not a number.
        return str(v) if isinstance(v, int | float) else v

    @model_validator(mode="after")
    def _all_five_questions(self) -> Definitions:
        missing = [k.value for k in QuestionKey if k not in self.questions]
        if missing:
            raise ValueError(f"missing question(s): {', '.join(missing)}")
        return self


# --- silence_log.csv --------------------------------------------------------

SILENCE_LOG_REQUIRED = ["agency", "request", "date_filed", "date_answered", "outcome", "notes"]
SILENCE_LOG_OPTIONAL = ["contract_id", "url"]


class SilenceLogRow(Strict):
    agency: NonEmpty
    request: NonEmpty
    date_filed: dt.date
    date_answered: dt.date | None = None
    outcome: RequestOutcome
    notes: str = ""
    contract_id: Id | None = None
    url: str | None = None

    @field_validator("date_answered", "contract_id", "url", mode="before")
    @classmethod
    def _blank_is_none(cls, v: object) -> object:
        return None if isinstance(v, str) and not v.strip() else v

    @model_validator(mode="after")
    def _answered_after_filed(self) -> SilenceLogRow:
        if self.date_answered and self.date_answered < self.date_filed:
            raise ValueError("date_answered is before date_filed")
        return self
