Paper Trail: Lightweight Contract Check
Nov 12, 2026 · @Farheen Rahman
Purpose and scope
The research notes propose a sharper vendor contract question, three kinds of silence, and a larger contract corpus. Before any of that goes into the full system, this lightweight version tests whether those ideas work on real contracts, using a few scripts and flat files instead of a database, a server, or an agent.
It answers one question well: for each of 20 to 30 public contracts, does the contract give the government the power to find out the system was wrong, and to do something about it? It answers with a cited quote, or with a silence status.
How it relates to the other docs:
• MVP design doc (Paper Trail: System Design). This runs alongside milestones 0 and 1 and doesn't change the MVP. The text extraction and citation-checking code it needs gets written once and reused by the MVP.
• Research notes. This is the smallest test of the notes' ideas. The bigger items there (the state-of-the-record report, contract lineage, the federal inventory join, renewal alerts) wait until this version shows the approach works.
Out of scope: retrieval and embeddings, the MCP server, connectors, the agent loop, a web interface, and federal contracts (their text is rarely published).
Questions it answers
Five sub-questions from the research notes, asked of every contract:
Key
Question
Counts as yes
know
Must the vendor give the agency documentation of inputs, training data, validation, and known limits?
A clause obliges the vendor to provide that documentation to the agency
show
Can the agency share that information publicly?
No confidentiality or trade-secret clause blocks disclosure of it, or a clause explicitly allows disclosure
test
Are there measurable performance or error thresholds, plus a right to audit?
A stated threshold and an audit or testing right for the agency or a third party
act
Are payment, renewal, or termination tied to those thresholds, and must the vendor re-validate when the model changes?
A clause links a consequence to performance, or requires re-validation on change
leave
Does the government keep its data and outputs, and can it switch vendors?
Clauses on data ownership and on transition or portability
Each answer is one of:
Answer
Meaning
yes
A quoted clause meets the definition
partial
A clause addresses it but falls short, for example an audit right with no threshold
no
The contract addresses the topic in a way that rules it out, for example a clause barring disclosure
silent
The full contract was read and nothing addresses it
withheld
The contract, or the relevant part, was redacted or refused
no_record
The agency said no such record exists
The last two are recorded per contract, not per question, since they come from records requests rather than reading. Definitions get tightened after the first hand-labeling pass; the version used for each run is saved with its results.
Approach: read the whole contract
The MVP retrieves the top passages for a question. That can't support a silent answer, because a clause the retriever missed looks the same as a clause that isn't there. This version skips retrieval and gives the model the entire contract for each question.
Why that's practical here. A contract of a few hundred pages fits within the context window of current long-context models. With prompt caching, the contract text is sent once and the five questions reuse it, so asking all five costs little more than asking one.
When a contract is too long, the script splits it into overlapping windows of pages, asks the question of each window, and combines the results: any yes or partial with a verified quote wins, and silent requires every window to come back empty. Because nothing is ranked and dropped, the absence claim still rests on every page having been read.
The model is never trusted on its own word. Each answer must include the clause it relies on, quoted exactly, with its page. The script checks that the quote appears on that page of the extracted text. A yes, partial, or no without a verified quote is downgraded to unverified and goes to manual review. A silent answer carries no quote, which is why the eval measures it separately (see Evaluation).
Pipeline
One command, ptlite check contracts.yaml, runs the whole thing:
1.  List the contracts. contracts.yaml holds each contract's source URL, agency, vendor, system, date, and any related documents (addenda, amendments, exhibits).
2.  Extract text by page. Each PDF becomes page-numbered text. A contract with no text layer is flagged for OCR instead of being read as empty, since an empty file would look silent on every question.
3.  Ask five questions. One model call per question, with the contract text cached, returning structured JSON: the answer, the quoted clause, its page, and a one-sentence reason.
4.  Verify quotes. The script checks each quote against the extracted page text. Failures go to manual review.
5.  Record results. Every answer is appended to results.jsonl with the model, prompt version, and definitions version that produced it.
6.  Compare with labels. ptlite score compares results with the hand labels and writes a short report.
Six steps, no server, no database. A run over 30 contracts should finish in one sitting.
Data files
Everything lives in version-controlled files in a lite/ folder of the Paper Trail repository. No database until the MVP.
File
Contents
Written by
contracts.yaml
One entry per contract: id, title, source URL, agency, vendor, system, state, date, related documents, and how it was obtained (portal, records request, archive)
Me
text/<id>.json
Extracted text, one entry per page, plus the file's hash
Script
definitions.yaml
The five questions and what counts as each answer, with a version number
Me
labels.csv
My hand labels: contract id, question, answer, page, quoted clause, note
Me
results.jsonl
One line per model answer: contract id, question, answer, quote, page, reason, verified flag, model, prompt and definitions versions, timestamp
Script
silence_log.csv
One row per records request: agency, what was asked, date filed, date answered, outcome (provided, redacted, refused, no_record, pending), notes
Me
reports/<date>.md
Agreement and error rates for each run
Script
The split matters: files I write are the ground truth, files the script writes can always be regenerated. Keeping definitions versioned means a change to what counts as yes can be traced to the runs it affected.
Evaluation
Gold set. I label 20 to 30 contracts by hand against definitions.yaml before looking at any model output, so the labels aren't anchored to its answers. Sources: the op-ed's contracts, state contracts listed in EPIC's appendix that are posted on state portals, and any contracts records requests return. Five or so contracts get labeled a second time a week later to check my own consistency.
Metrics, per question and overall:
Metric
What it measures
Why it matters
False-silent rate
Share of my yes or partial labels the model called silent
The headline metric. A false "no standards" claim is the most damaging error this tool can make
False-yes rate
Share of my silent or no labels the model called yes
Overstates accountability that isn't there
Agreement
Share of answers that match my label exactly
Overall quality
Quote verification rate
Share of quoted answers whose quote checks out
Catches invented or misquoted clauses
Self-consistency
Agreement between my two labeling passes
Sets a ceiling: the model can't be held to a standard I don't meet myself
Targets are set after the first run, once there's a baseline. Every disagreement is read by hand and tagged as a model error, a labeling error, or an ambiguous definition. The third kind feeds the next version of definitions.yaml.
Records requests and the silence log
Records requests take weeks to months, so they start on day one, in parallel with the code.
• What to request first: the op-ed contracts that aren't public (Texas DIR–Deloitte TIERS, Michigan–Fast Enterprises), plus a few EPIC-listed contracts in states without contract portals.
• How: file through MuckRock where possible, so requests and responses are tracked and public.
• What gets logged: every request, whatever the outcome, in silence_log.csv. A refusal, a redaction, and a "no record" response are each findings, not failures.
• When a contract arrives, it's added to contracts.yaml with how it was obtained, then labeled and run like the others.
Milestones
#
Milestone
Scope
Done when
L0
Setup
lite/ folder, first five contracts in contracts.yaml, definitions.yaml v1, records requests filed
Five contracts listed and the first requests are in silence_log.csv
L1
Extract and label
Page-numbered extraction with OCR flags; hand labels for the first 10 contracts
10 contracts extracted and labeled, scanned ones flagged
L2
Check
Five-question calls with caching, quote verification, page windows for long contracts, results.jsonl
ptlite check runs on all 10, and every answer is verified or flagged for review
L3
Score and expand
ptlite score report; grow to 20 to 30 contracts; second labeling pass; definitions v2
A report on 20 or more contracts with false-silent rate per question, and a one-page findings note
Decision gate after L3. Fold this into the MVP only if the false-silent rate is low enough that I'd stand behind a silent finding in public, and the definitions held steady through a revision. If not, the findings note says why, and that's a result too.
What carries forward, and what waits
Into the MVP, if the gate passes:
From this version
Becomes in the MVP
Page-numbered extraction
Ingestion step 2 (shared code from the start)
Quote verification
The citation verification step in cited Q&A
Six answer values
The scorecard_answer.answer values, replacing not_found
Five sub-questions and definitions.yaml
The vendor contract question in the scorecard agent
Whole-contract reading
A second path beside top-k retrieval, used for contract questions and any silent claim
Related documents in contracts.yaml
A contract-family relation in the data model
labels.csv
The gold set for the scorecard eval
silence_log.csv
A table of records requests and outcomes
Waits until after the MVP, as described in the research notes: the state-of-the-record report across EPIC's contracts, NASPO contract lineage, the federal inventory join, renewal alerts, and partner pilots. Each of those depends on the false-silent rate this version measures.
Open questions
#
Question
Current default
1
When the main contract incorporates a master agreement by reference and I don't have it, is the answer silent?
No. Mark it incomplete with a note naming the missing document, so a gap in my corpus isn't reported as a gap in the contract
2
One call per question, or all five in one call?
One per question, with the contract cached; simpler to debug and score
3
Which model for the check?
The MVP's default provider; compare a second model on the same gold set once L3 is done
4
What false-silent rate is good enough to pass the gate?
Decided after the first baseline, before looking at the rest of the results
5
Should anyone else label a subset, to check my labels?
Ideally one other person with legal or procurement background labels five contracts
6
Should a contract that's mostly boilerplate but references an AI-specific exhibit be treated as one document?
Yes: the contract and its exhibits are read together as one contract family