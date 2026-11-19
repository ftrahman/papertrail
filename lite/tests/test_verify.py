import pytest

from ptlite.verify import quote_on_page

PAGE = (
    "12.3 Audit. The Agency may audit the\n"
    "Contractor's records at any time. The Con-\n"
    "tractor shall provide a well-\n"
    "known format for all data.\n"
)


# --- allowed -------------------------------------------

@pytest.mark.parametrize("quote", [
    "The Agency may audit the Contractor's records",   # spans a line break
    "The  Agency   may audit the",                     # extra spaces in the quote
    "The Contractor shall provide a",                  # Con-/tractor rejoined
    "provide a well-known format for all",             # well-/known keeps its hyphen
    "  12.3 Audit. The Agency may  ",                  # spaces around the quote
])
def test_tolerated_differences_verify(quote):
    assert quote_on_page(quote, PAGE)


# --- failures ----------------------------------------------

@pytest.mark.parametrize("quote", [
    "the agency may audit the",                        # case differs
    "The Agency may audit the Contractors records",    # apostrophe missing
    "The Agency shall audit the Contractor's",         # one word changed
    "The Agency may audit the Contractor's files",     # plausible, but not on the page
    "",                                                # empty quote
    "   ",                                             # whitespace only
])
def test_near_misses_fail(quote):
    assert not quote_on_page(quote, PAGE)


def test_hyphen_mid_line_is_not_forgiven():
    """Only end-of-line hyphens are tolerated, not hyphens inside a line."""
    assert not quote_on_page("wellknown", "a well-known format")


def test_quote_from_another_page_fails():
    assert not quote_on_page("The Agency may audit", "Payment is due in 30 days.")
@pytest.mark.parametrize("quote, page", [
    ("the final report shall be delivered", "the ﬁnal report shall be delivered"),
    ("the Contractor's records shall be open", "the Contractor’s records shall be open"),
])
def test_typographic_forms_verify(quote, page):
    assert quote_on_page(quote, page)


def test_short_quote_is_not_evidence():
    assert not quote_on_page("audit rights", "The Agency has audit rights.")
