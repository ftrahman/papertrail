# Paper Trail

Answers accountability questions about government AI systems from public records,
citing the exact passage for every answer. See README.md for background.

The worst failure is a confident wrong answer: never claim a clause is absent
unless every page was read, and never trust a quote that hasn't been verified.
Findings say what a contract does or doesn't oblige, never that no accountability exists.

## Design docs

In `design/`. Read the relevant one before starting a milestone. If code and a doc disagree, ask rather than picking one.

- `design/lite.md`: the lightweight contract check (current work), with its system diagram and status
- `design/mvp.md`: the MVP, the contract check at scale, milestones 0 to 4 (later)
- `design/research.md`: the research behind the questions, decisions made, and open decisions

Before resolving anything listed under open decisions in `research.md`, ask. When a decision is made, add it to that file's decision log.

## Current scope: the lightweight contract check

Scripts and flat files in `lite/`. No server or MCP yet; those belong to the MVP. Embeddings, retrieval, agents and a web UI come after the MVP, if at all.

For 20 to 30 public contracts (state and local, plus a small federal batch reported separately), `ptlite check` asks five questions (`know`, `show`, `test`, `act`, `leave`) and answers each with a verified quote or a silence status. Their wording and what counts as each answer live only in `lite/definitions.yaml`, which is versioned. Load them from that file; never hardcode them in prompts or code.

**Answer values**

- `yes`, `partial`, `no`: a quoted, verified clause meets, partly meets, or rules out the definition
- `silent`: every page was read and nothing addresses it
- `incomplete`: would be `silent`, but an incorporated document is missing
- `unverified`: the quote failed verification; needs manual review
- `withheld`, `no_record`: per contract, from records requests; never produced by the model

## Rules that must not be broken

1. **Read the whole contract.** No top-k retrieval for these questions. A missed clause looks identical to a missing one.
2. **`silent` means every page was read.** Never truncate. For long contracts, ask overlapping page windows and return `silent` only if every window is empty. Until windows exist, a contract too long for one call is logged as skipped, never answered.
3. **Verify every quote in code.** A `yes`, `partial` or `no` needs an exact quote and page, checked against that page's extracted text. Tolerated: whitespace, line breaks, either reading of a line-end hyphen, Unicode compatibility forms (ligatures, non-breaking spaces), and curly quotes and dashes. Nothing more. Quotes under five words don't count as evidence. Failure downgrades the answer to `unverified`.
4. **Empty text is not silence.** A PDF with no text layer is flagged for OCR and skipped, never read as an empty contract.
5. **Missing incorporated documents block `silent`.** If a master agreement, exhibit or addendum the contract incorporates has no PDF in `contracts.yaml`, the answer is `incomplete`, naming the missing document.
6. **Hand-written files are ground truth.** Never edit `contracts.yaml`, `definitions.yaml`, `labels.csv` or `silence_log.csv` without the maintainer's explicit approval. Script output (`text/`, `results.jsonl`, `reports/`) can always be regenerated.
7. **Record provenance.** Every line in `results.jsonl` carries the model that answered, prompt version, definitions version and timestamp.

## Layout

```
lite/
  contracts.yaml      # hand: contracts, related documents, how each was obtained
  definitions.yaml    # hand: the five questions and answer definitions, versioned
  labels.csv          # hand: hand labels, the gold set
  silence_log.csv     # hand: records requests and outcomes
  pdfs/               # hand: downloaded contracts
  text/<id>.json      # script: page-numbered text plus file hash
  results.jsonl       # script: one line per model answer
  reports/<date>.md   # script: score reports
  ptlite/             # the package
  tests/
```

Commands: `ptlite validate` (built); `ptlite extract`, `ptlite check`, `ptlite score` (in progress). Run `make check` (imports, lint, types, tests) before committing.

## Stack and conventions

- Python 3.12+, Pydantic for every schema, PyYAML, PyMuPDF, pytest, ruff, mypy.
- The model sits behind the `ModelClient` interface, Anthropic by default via the direct API. Model ID from `PTLITE_MODEL`, API key from the environment; neither is ever committed.
- Prompt caching sends the contract once and reuses it across the five questions. Check the current Anthropic docs for caching and structured output before changing that code.
- Structured output only. Unusable output is retried once, then recorded as an error row, never guessed at.
- Tests never call a real model or the network: use the fake model client and small PDFs generated in the tests.
- Keep `extract.py` and `verify.py` clean and standalone; the MVP reuses them.

## Workflow

- The maintainer writes the code. Explain, sketch and review; don't edit source files unless asked for that specific change.
- Build one milestone at a time with tests, and stop for review before the next.
- One branch per reviewable feature; small, described commits; merge to `main` through a reviewed pull request.
- When a definition is ambiguous, ask. Don't resolve it in the prompt.
- If a rule here makes a task impossible, say so instead of working around it.
