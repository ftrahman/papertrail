# Paper Trail

Paper Trail answers accountability questions about government AI systems using only the public record. Every answer cites the exact passage it came from. When the record is silent, it says so instead of guessing.

It grew out of the op-ed *Engineered Silence*. Agencies use AI to decide who gets benefits, who is flagged for fraud and who is investigated, but the documents that show how those systems are governed are scattered and rarely read. Paper Trail surfaces what, if any, accountability exists and where.

## Current work: the lightweight contract check

Before building the full system, `lite/` tests the core idea on 20 to 30 public government AI contracts: **does the contract give the government the power to find out the system was wrong, and to do something about it?**

Each contract is asked five questions:

| Key | Question |
| --- | --- |
| `know` | Must the vendor give the agency documentation of the system's inputs, training data, validation or testing, and known limitations? |
| `show` | Can the agency share that documentation, or its own findings about the system, with the public? |
| `test` | Does the contract set a required level of accuracy or error, and give the agency or an independent party the right to audit or test the system? |
| `act` | Can the agency require a fix, suspend the system, withhold payment, or end the contract when it fails its requirements, and must the vendor re-test when the model changes? |
| `leave` | Does the government keep its data and what is built from it, and can it get that data back in a usable form to switch vendors? |

What counts as each answer is defined in [`lite/definitions.yaml`](lite/definitions.yaml), which is versioned.

### Answers

| Answer | Meaning |
| --- | --- |
| `yes` | A quoted clause meets the definition |
| `partial` | A clause addresses it but falls short |
| `no` | A clause rules it out |
| `silent` | Every page of the contract was read and nothing addresses it |
| `incomplete` | The contract incorporates a document we don't have, so silence can't be claimed |
| `unverified` | The model quoted a clause that couldn't be found on the page; needs manual review |
| `withheld`, `no_record` | From public records requests: the contract was refused or redacted, or the agency said none exists |

### How it works

1. **Extract** each contract's text page by page. A PDF with no text layer is flagged for OCR, never treated as an empty contract.
2. **Ask** a language model each question with the whole contract in context. There's no search step, because search can't prove a clause is absent.
3. **Verify** every quote in code against the page it claims to come from. A quote that isn't there becomes `unverified`. The model's word is never trusted.
4. **Record** every answer with the model, prompt version, definitions version and timestamp.
5. **Score** the answers against hand labels. The headline measure is the false-silent rate: how often the model calls a contract silent when a real clause exists.

## Status

- [x] Schemas and checks for the hand-written files (`ptlite validate`)
- [x] Page-by-page text extraction with scanned-PDF detection
- [x] Hand label format and checks
- [x] Quote verification
- [x] Model client with structured output and a retry on unusable answers
- [ ] `ptlite extract` command
- [ ] `ptlite check`: the five questions per contract, with verification
- [ ] `ptlite score`: comparison with hand labels and a report
- [ ] First labeled contracts and a preliminary evaluation

## Setup

Requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

```bash
python3 -m venv .venv
make install
```

`ptlite check` will need two environment variables, kept in a `.env` file that is never committed:

```bash
ANTHROPIC_API_KEY=...
PTLITE_MODEL=...   # the Claude model ID to use
```

## Usage

```bash
.venv/bin/ptlite validate   # check contracts.yaml, definitions.yaml, labels.csv, silence_log.csv
```

## Data files

| File | Written by | Contents |
| --- | --- | --- |
| `lite/contracts.yaml` | Hand | Each contract, its related documents, and how it was obtained |
| `lite/definitions.yaml` | Hand | The five questions and what counts as each answer |
| `lite/labels.csv` | Hand | Hand labels: the gold set the model is scored against |
| `lite/silence_log.csv` | Hand | Public records requests and their outcomes |
| `lite/pdfs/` | Hand | Downloaded contracts |
| `lite/text/<id>.json` | Script | Extracted page text and the file's hash |
| `lite/results.jsonl` | Script | One line per model answer, with provenance |
| `lite/reports/<date>.md` | Script | Score reports |

Hand-written files are ground truth and change only by hand. Script output can always be regenerated.

## Development

```bash
make check   # sort imports, lint, type-check, then test
make test    # tests only
```

Tests never call a real model or the network: they use a fake model client and small PDFs generated in the tests.

## What comes next

If the lightweight check shows the false-silent rate is low enough to stand behind a `silent` finding in public, the same check runs on hundreds of contracts. The results are published as a versioned dataset with a benchmark for detecting missing clauses, an MCP server so any AI assistant can query them, and a "state of the record" report.
