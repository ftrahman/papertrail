# Paper Trail

Paper Trail answers accountability questions about government AI systems using only the public record: vendor contracts, privacy impact assessments, audits, court filings. Every answer cites the exact passage it came from. When the record is silent, the tool says so instead of guessing.

**Mission:** make the division of responsibility visible, so the people affected by a government AI system, and the people with power to change it, can see what was promised, what was hidden, and what was never asked for, in time to act.

The project grew out of my op-ed, *Engineered Silence*. A confident wrong answer is the worst failure this tool can have, because it does to a vendor or agency what these systems do to the people they judge.

## Design docs

Read the relevant doc before starting a milestone. If code and a doc disagree, ask me rather than picking one.

- Lightweight Contract Check (current work): https://claude.ai/artifact/5VAshS8UyfxJsPo8GkezBE
- System Design (the MVP, milestones 0 to 4, later): https://claude.ai/artifact/UwXAXawb5738QAis49YDqA
- Research Notes and Follow-ups: https://claude.ai/artifact/UM4JYWjKnD3oH7Kdz6vuMa

## Current scope: the lightweight contract check

Scripts and flat files in `lite/`. No database, server, embeddings, retrieval, agent loop, or web UI yet. Those belong to the MVP.

For each of 20 to 30 public state and local contracts, `ptlite check` asks five questions and answers each with a verified quote or a silence status.

| Key | Question |
| --- | --- |
| `know` | Must the vendor give the agency documentation of inputs, training data, validation, and known limits? |
| `show` | Can the agency share that information publicly, or does a confidentiality or trade-secret clause block it? |
| `test` | Are there measurable performance or error thresholds, plus a right for the agency or a third party to audit? |
| `act` | Are payment, renewal, or termination tied to those thresholds, and must the vendor re-validate when the model changes? |
| `leave` | Does the government keep its data and outputs, and can it switch vendors? |

The authoritative wording and what counts as each answer live in `lite/definitions.yaml`, which is versioned. Don't hardcode definitions in prompts; load them from that file.

**Answer values**

- `yes`: a quoted clause meets the definition
- `partial`: a clause addresses it but falls short
- `no`: a clause rules it out (for example, one barring disclosure)
- `silent`: every page of the full contract was read and nothing addresses it
- `incomplete`: the contract incorporates a document we don't have, so silence can't be claimed
- `unverified`: the model gave a yes, partial, or no but its quote failed verification; needs manual review
- `withheld` and `no_record`: per contract, from records requests, never produced by the model

## Rules that must not be broken

1. **Read the whole contract.** No top-k retrieval for these questions. A missed clause looks identical to a missing one.
2. **`silent` means every page was read.** For long contracts, split into overlapping page windows, ask each window, and return `silent` only if every window comes back empty. Never truncate.
3. **Verify every quote in code.** A `yes`, `partial`, or `no` must include an exact quote and page. The script checks the quote against the extracted text of that page (tolerating whitespace, line breaks, and end-of-line hyphenation, nothing more). Failure downgrades the answer to `unverified`. The model's word is never trusted.
4. **Empty text is not silence.** A PDF with no text layer is flagged for OCR and skipped, never read as an empty contract.
5. **Missing incorporated documents block `silent`.** If the contract incorporates a master agreement, exhibit, or addendum that isn't in `contracts.yaml`, the answer is `incomplete`, naming the missing document.
6. **Human-written files are ground truth.** Never edit `contracts.yaml`, `definitions.yaml`, `labels.csv`, or `silence_log.csv` without my explicit approval. Script output (`text/`, `results.jsonl`, `reports/`) can always be regenerated.
7. **Record provenance.** Every line in `results.jsonl` carries the model ID, prompt version, definitions version, and timestamp.

## Layout

```
lite/
  contracts.yaml      # me: contracts and related documents, how each was obtained
  definitions.yaml    # me: the five questions and answer definitions, versioned
  labels.csv          # me: hand labels, the gold set
  silence_log.csv     # me: records requests and outcomes
  pdfs/               # me: downloaded contracts (gitignored if large)
  text/<id>.json      # script: page-numbered text plus file hash
  results.jsonl       # script: one line per model answer
  reports/<date>.md   # script: score reports
  ptlite/             # the package
  tests/
```

Commands: `ptlite extract`, `ptlite check`, `ptlite score`.

## Stack and conventions

- Python 3.12 or later, Pydantic for every schema (model output, results, labels), PyYAML, PyMuPDF for extraction, pytest, ruff.
- Model provider behind one small interface, Anthropic by default, via the direct API. Model ID comes from an environment variable, not code. API keys come from the environment and are never committed.
- Use prompt caching so the contract text is sent once and reused across the five questions. Check the current Anthropic docs for the caching and structured-output API before writing that code; don't rely on memory.
- Structured output only: the model returns JSON matching a Pydantic schema. Invalid JSON is retried once, then recorded as an error, never guessed at.
- Tests never call a real model or the network. Use a fake model client with scripted responses, and small PDFs generated in the tests.
- Keep the extraction and quote-verification code clean and standalone. The MVP will reuse it.

## Working with me

- Build one milestone at a time (L0 to L3 in the Lightweight doc), with tests, then stop for my review before the next.
- This is a private GitHub repo until the MVP is done. Commit in small, described steps.
- When a definition is ambiguous, ask. Don't resolve it in the prompt.
- If something in these rules makes a task impossible, say so instead of working around it.