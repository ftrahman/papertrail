import re
import unicodedata

MIN_QUOTE_WORDS = 5

_TYPOGRAPHIC = str.maketrans({
    "\u2018": "'", "\u2019": "'",   # ‘ ’
    "\u201c": '"', "\u201d": '"',   # “ ”
    "\u2013": "-", "\u2014": "-",   # – —
})
EOL_HYPHEN = re.compile(r"-[ \t]*\n\s*")

def _merge(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _normalize(s: str) -> str:
    return unicodedata.normalize("NFKC", s).translate(_TYPOGRAPHIC)

def quote_on_page(quote: str, page_text: str) -> bool:
    q = _merge(_normalize(quote))
    if len(q.split()) < MIN_QUOTE_WORDS:
        return False
    if not q:
        return False
    page = _normalize(page_text)
    options = (_merge(page), _merge(EOL_HYPHEN.sub("", page)),
        _merge(EOL_HYPHEN.sub("-", page)),
    )
    return any(q in option for option in options)
