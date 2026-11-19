# Research and decisions

Why the questions are what they are, where the evidence comes from, and every design decision: made or still open. See [lite.md](lite.md) and [mvp.md](mvp.md).

## The gap

Government AI contracts rarely contain enforceable accountability terms, and vendor self-disclosure doesn't fill the gap. Nobody connects a known system to its contract, assessments, audits and court record and answers accountability questions across them with verified citations. And no public benchmark tests whether a model can tell that a clause is **missing**: the hardest and most important claim Paper Trail makes.

| Source | Finding that shapes the design |
| --- | --- |
| FAS, Kim & Kesari (2026) | 3,771 provisions in 215 state contracts: 77% boilerplate, 5.3% transparency, 2.4% fairness and accountability. Most NASPO-bought, so one contract's gaps spread to many states |
| Kuehnert, Johnson et al., CMU (2026) | 22 of 39 vendor FactSheets gave little or no training-data information; 21 reported no performance results |
| GAO-26-107859 (2026) | Agencies buy AI as an ongoing service and don't collect lessons on terms like data rights and testing |
| Tillipman, "Buying Blind" (2026) | Contracts are now the main safeguard on federal AI; AI often arrives as an add-on to an existing licence, inheriting its terms. "Disclosures are not verification" |
| Brauneis & Goodman (2018) | 42 records requests: agencies often had no records, or contracts blocked release. Basis for the silence types |
| GSAR 552.239-7001 (in effect Oct 19, 2026) | Federal LLM clause: government owns fine-tuned weights built from its data, deletion at contract end, 72-hour incident notice, notice when a model is retired, only "reasonable efforts" on accuracy |
| CLAUSE benchmark (EACL 2026) | Closest test of AI contract review; covers some omissions, none targets missing clauses directly |

## Checking the questions against model clauses

The EU model clauses (MCC-AI, high-risk and light), the GovAI Coalition AI addendum and FactSheet, and CDT's vendor transparency rubric all back the five questions. They also set the line between `yes` and `partial`:

| Key | `yes` looks like | `partial` looks like |
| --- | --- | --- |
| `know` | EU: technical documentation at delivery, updated at every substantial change | Documentation only on request, with no defined contents |
| `show` | EU: agency may publish documentation in a register and audit conclusions | GovAI: may "communicate its general usage" only |
| `test` | EU: testing against defined thresholds, plus an annual audit | GovAI: accuracy monitoring and audit, no required level |
| `act` | EU: new conformity assessment after a substantial change, plus default on unfixed findings | GovAI or GSA: notice of model changes, no re-testing |
| `leave` | EU: agency owns its data and gets it back in a common format | Ownership with no handover duty |

Notably, even the GovAI addendum scores `partial` on `test`. Topics the standards cover that the five questions don't: human override, incident reporting, logs, bias evaluation, explanations for affected people, and whether obligations reach the company that built the model.

## Where contracts come from

| Source | Contract text? | Use |
| --- | --- | --- |
| State portals linked from EPIC's appendix | Yes | Typical contracts, mostly `silent` |
| GovAI Coalition cities that adopted the addendum | Likely | Best source of real `yes` and `partial` clauses |
| GSA eLibrary schedule terms and vendor licences | Yes | Federal batch, scored separately |
| SAM.gov solicitations | Proposed terms only | Later, as a separate document type |
| USAspending, FPDS | No, award data only | Finding records-request targets |
| GSA OneGov AI deals | Not published | Records requests; a refusal is itself a finding |

## Decisions made

| Date | Decision |
| --- | --- |
| 2026-11-17 | **Definitions v2** adopted (see `lite/definitions.yaml`): `show: yes` needs an explicit disclosure clause; documentation "on request" with defined contents counts for `know`; uptime guarantees don't count as `test` thresholds and "as is" disclaimers don't make `test` a `no`; `act: yes` needs both a consequence and re-testing, consequences tied to failing requirements count, termination for convenience doesn't, service-credit-only remedies are `no`; `leave` ignores a vendor licence to de-identified aggregate data |
| 2026-11-17 | A **federal batch** of about 5 contracts joins the state and local ones, reported separately |
| 2026-11-17 | The **maintainer writes the code**; Claude explains, sketches and reviews |
| 2026-11-18 | **Quote verification** also tolerates ligatures and curly quotes or dashes (NFKC plus a table) and accepts either reading of a line-end hyphen; quotes under 5 words don't count as evidence |
| 2026-11-18 | **First release in about 3 days:** no page windows (long contracts skipped, not answered), 5 labeled contracts, missed-clause test set deferred |
| 2026-11-18 | Unusable model output: `ask_with_retry` in `model.py` retries once; `check` records the failure as an error row, never an answer |
| 2026-11-19 | Design docs live in `design/` as three files; the online docs are archived |
| 2026-11-19 | **MVP narrowed** to the contract check at scale: corpus, second reader, missed-clause benchmark, public dataset, MCP tool and report. General cited search, embeddings, the scorecard agent, connectors and a web app move after the MVP. Findings are worded as "the contract does not oblige…", not "no accountability exists" |

## Open decisions

| # | Decision | Needed before | Default until decided |
| --- | --- | --- | --- |
| 1 | Split `test`, `act`, `leave` into single-issue questions? | More labeling | Five questions, unsplit |
| 2 | When page windows disagree, which answer wins? | Page windows | `yes` > `partial` > `no` > `unverified` |
| 3 | Window every contract over a set length, or only ones too long to fit? | Page windows | Only ones too long |
| 4 | May a quote span two pages? | `check` | No |
| 5 | Refusal fallbacks to another model: on, with the answering model recorded, or off? | `check` | Off |
| 6 | Reasoning effort for the check | `check` | `high`; compare `medium` at L3 |
| 7 | How `unverified`, `incomplete`, `withheld` count in scores | `score` | Reported separately, outside the rates |
| 8 | False-silent upper bound that passes the decision point | End of L3 | Set after the first baseline |
| 9 | A second labeler with legal or procurement background | L3 | About 5 contracts, if someone is available |
| 10 | Add a sixth question: do obligations reach the model's builder? | Definitions v3 | Not asked |
| 11 | Review and dispute policy for named vendors and agencies, and whether to get legal review | MVP milestone 3 | Nothing published until a policy exists |
| 12 | License for the published labels and results | MVP milestone 3 | Open |
| 13 | OCR for scanned contracts | MVP milestone 1 | Flag and skip |
| 14 | Which open model to fine-tune as the second reader | MVP milestone 2 | A small long-context encoder |

## Follow-ups outside the code

- File records requests for Texas DIR–Deloitte TIERS and Michigan–Fast Enterprises; log every outcome in `silence_log.csv`.
- Verify secondary-source numbers against primaries (the FAS memo's MiDAS figures conflict).
- Ask FAS for their coded provisions; ask EPIC about its contract table; ask CMU about absence-detection methods.
- Run a landscape scan before claiming "first."

## Sources

[FAS](https://fas.org/publication/how-governments-purchase-ai-fair/) · [CMU, Disclosure or Marketing?](https://arxiv.org/abs/2604.01332) · [GAO-26-107859](https://files.gao.gov/reports/GAO-26-107859/index.html) · [Tillipman, Buying Blind](https://scholarship.law.gwu.edu/faculty_publications/1831) · [Brauneis & Goodman](https://yjolt.org/node/956) · [Wiley on GSAR 552.239-7001](https://www.wiley.law/alert-GSA-Releases-Final-Language-of-AI-Contract-Clause) · [Nextgov on lock-in](https://www.nextgov.com/ideas/2026/10/vendor-lock-finds-new-home-ai-and-contract-clause-wont-fix-it/416779/) · [CLAUSE](https://clause-legal.github.io/) · [EU MCC-AI](https://public-buyers-community.ec.europa.eu/communities/procurement-ai/resources/updated-eu-ai-model-contractual-clauses) · [CDT framework](https://cdt.org/insights/a-framework-for-assessing-ai-transparency-in-the-public-sector/) · [EPIC, Outsourced & Automated](https://epic.org/outsourced-automated/) · [Open Contracting Partnership](https://www.open-contracting.org/2026/07/09/ai-in-public-procurement-between-experimentation-and-impact/)
