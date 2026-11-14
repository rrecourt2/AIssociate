# Bankability 2: design

14 November 2026. This document is the reference for building Bankability 2. It gathers the decisions taken in the design interview of 13 and 14 November. The reasoning behind each decision, and the research it rests on, is in the [interview notes](../../docs/aissociate/aissociate-2-notes.md).

Nothing described here is built yet.

## 1. What it is

Bankability 2 is a memory for an investment deal. It keeps everything that is shared about a deal in one folder, in a form that a person and any AI tool can pick up again later. It knows how the deal is structured, what is known, what is assumed and what is still missing, and it always says what to do and collect next.

It is written for a development finance institution and for an investment officer who works with an AI assistant. The first host is Microsoft Copilot Cowork.

It is built from scratch. It takes its standard and its lessons from the first Bankability, and none of its code.

## 2. Principles

1. **A tool, not a process.** There is no required order. Nothing waits for anything else. Stages are targets: the tool says "ideally there for the CIP" and never refuses.
2. **Tools serve the AI.** A tool informs and never blocks. It refuses only an entry that is malformed.
3. **The AI proposes, the tool records and computes.** Anything that can be computed from the records is computed, and never stored or written by the AI.
4. **Everything can change, and nothing is deleted.** The borrower can change. What is replaced stays, marked as replaced.
5. **Reasons, not thresholds.** What matters gets in, with the reason. What is left out is recorded too, with a specific reason.
6. **Files in the deal folder.** Plain files that a person can read. No database and no server.
7. **Simple to audit.** A bank's security reviewer must be able to read all of it in an afternoon. Section 11 has the rules.
8. **The standard is adjustable.** Anything in it can be changed or switched off.
9. **Leave to the host what the host does.** Copilot reads documents, writes Word files, sends mail and remembers the user's preferences. Bankability 2 does none of that.

## 3. The pieces

```text
Standard     what a deal folder holds and what must be known
               data-room structure, risk checks, later a system structure
   ↓
Tool         one small program, Python standard library only
               records, links, computes what is missing, fills in the generated parts
   ↓
Skill        instructions that tell the AI how to work with the tool and the folder
   ↓
Deal folder  one per deal, in OneDrive
               a client folder that can be shared, and an internal folder
```

The same tool runs in three places, on the same folder:

| Where | How | When |
|---|---|---|
| Inside Copilot Cowork | Shipped inside the skill, run in Cowork's sandbox | First |
| On the laptop | Installed as a small package, run from a terminal on the synced OneDrive folder | First. It also does the file work Cowork cannot do. |
| Through Copilot Code | A local MCP shell around the same tool | When access is granted |

Cowork cannot call a program on the laptop. Microsoft requires an MCP server to be reachable over the internet, so there is no local server for Cowork.

## 4. The deal folder

```text
<Deal>/
├── Client folder/      can be shared with other lenders and consultants
│   ├── 01 Business and project overview/
│   ├── …               the ten folders of the data-room structure
│   ├── 10 Monitoring and reporting/
│   └── manifest.json   one line per document
└── Internal/           the officer and the deal team only
    ├── sources/        calls, emails, notes, internal memos
    ├── memory/         the structured memory and the log; only the tool writes here
    ├── wiki/           deal, parties, people, topics, terms, work
    ├── standard/       this deal's adjustments to the standard
    ├── systems/        entry sheets for the bank's systems
    └── outputs/        drafts of the scan, the CIP and the FP
```

- **Two systems, kept separate.** The client folder holds what the client shares. The internal folder holds everything else. The test for where something goes: may the client see it?
- **The internal folder points into the client folder.** The client folder knows nothing about the internal one, so it can be handed to someone else as it is.
- **The manifest is the only seam.** It has one line per document: what it is, its slot in the data-room structure, the party, the period and a fingerprint of the file. A folder that arrives with a manifest is indexed in one step. Loose documents are sorted and the manifest is written.
- **Sorting is done on the laptop.** Cowork cannot move or delete files.
- **One sharing rule.** Share the client folder and nothing else.

## 5. The memory

The memory has four parts.

### 5.1 The index: where things are

One entry per source: a document, a call, an email or a note. It says what the source is, where it is, how old it is, and which pages or minutes cover which topic. The AI reads the index first and goes back to the source itself for a quote or for nuance.

```json
{"id": "S-014", "title": "Call with the CFO", "kind": "call_transcript",
 "where": "Internal/sources/2026-09-12 CFO call.docx", "fingerprint": "9f2c…",
 "about": ["P-001"], "date": "2026-09-12", "read": "full",
 "map": [{"at": "min 12–18", "topic": "margins", "gist": "Explains the margin drop by milk prices."}]}
```

A long report gets a small tree in `map`: section, pages, one line each.

### 5.2 The facts: what is known

Exact things: names, amounts, dates, terms, shares, commitments. If something would go into a system field or a table, it is a fact. If it would go into a paragraph, it stays in the source and the index says where.

```json
{"id": "F-031", "about": "P-001", "statement": "Gross debt was EUR 40m.",
 "value": 40, "unit": "EUR m", "as_of": "2026-06-30", "recorded": "2026-11-14",
 "source": "S-007", "place": "p. 6", "said_by": "document",
 "answers": ["OBS_DEBT_001=true"], "state": "current"}
```

- **Two dates.** `as_of` is the date the fact refers to. `recorded` is when it was written down.
- **Who said it.** A document, the client, the officer, a third party, or the AI's own inference.
- **Replaced, not removed.** A fact that is replaced or contested keeps its place, with the state `outdated` or `disputed` and a pointer to what replaced it.

### 5.3 The graph: how the deal is structured

Who the borrower is, who guarantees, which customers, suppliers and related parties matter, and how they depend on each other. The wiki and the risk checks grow out of it.

```json
{"subjects": [{"id": "P-001", "kind": "party", "name": "Cedar Foods Ltd"},
              {"id": "P-002", "kind": "party", "name": null, "note": "guarantor, not yet known"},
              {"id": "L-001", "kind": "facility", "name": "EUR 12m working-capital facility"}],
 "links":    [{"from": "P-001", "type": "borrows", "to": "L-001", "state": "confirmed", "source": "S-002"},
              {"from": "P-002", "type": "guarantees", "to": "L-001", "state": "proposed",
               "why": "Requested in the term sheet. The guarantor is still to be named."}]}
```

- **A party is stable and its role is a link.** When the borrower changes, the facts stay with the company they are about. The checks for "the borrower" follow the link to the new one.
- **A role can be an empty seat**, such as a guarantor who is not yet known. Analysis of the rest goes ahead.
- **Anything can propose.** The AI proposes parties and links as it reads, and the officer can simply say so. A proposal is usable at once.
- **A link carries its reason.** Why this party matters for repayment, or why it was left out. A reason for leaving something out points to a fact or an answered check.
- **A link in the graph creates a wiki page and brings the checks that fit the role.**
- **The AI states the structure once**, mentions it again when it changes, and asks only when it cannot decide.

### 5.4 The wiki: what is understood

The wiki is the AI's working draft: the wider analysis that the FP is later condensed from. It describes. The FP concludes. The officer reads the FP, not the wiki, so there is no review duty. When the officer corrects something in a draft or in chat, the AI corrects the page and the fact behind it.

Six shelves, two levels deep:

| Shelf | One page per | 
|---|---|
| Deal | the deal (a single page) |
| Parties | company in the graph |
| People | group: the client side, our side, other lenders and advisers |
| Topics | subject of analysis, following the workstreams of the standard |
| Terms | term under negotiation |
| Work | piece of work, such as a consultant to hire or a site visit |

Every page has the same four parts:

1. **What it is.** One to three plain sentences. The first can stand alone, and is the page's line in the table of contents.
2. **At a glance.** Filled in by the tool from the graph and the records: role, links, key values, checks answered and open, documents, last change.
3. **What we know.** Description, context and facts, traceable to the page's sources. The AI structures this part as the subject needs.
4. **Assumptions and open points.** Each assumption with what it rests on. Then what is unknown, and what was looked for and not found.

The tool lists the sources at the foot and generates the table of contents.

Rules for a page:

- One subject per page. Split a page when it covers two.
- A page lists its sources. Every number, date and quote on it must be findable in them. The tool checks this and reports.
- The AI marks what it inferred.
- New information is merged in. What it replaces stays visible under the claim, marked outdated or disputed.
- Nothing is written when a source adds nothing.
- Size is guidance. The tool reports sizes.
- Only a person can mark a page as checked. Nobody has to.
- The People shelf holds what people said, asked for and decided, with sources. The officer's private reading of people stays out of the deal folder.

Writing rules, taken from Wikipedia's list of signs of AI writing:

1. State a relationship exactly: who, what, since when, how much. Never "associated with".
2. No sentence about significance. Say what the fact changes for repayment, or leave it out.
3. Name who said it and where. One source is one source.
4. No summary at the end of a section or a page.
5. Use "is" and "has".
6. Give every number its unit, its date and the company it belongs to.

The AI loads little at a time: the Deal page and the table of contents first, then only the pages a task needs, and a source only for a quote or for nuance.

## 6. The standard

The standard says what a deal folder holds and what must be known. It has three structures. They are sets of labels on the one memory, not three systems.

| Structure | Holds | Size today |
|---|---|---|
| Data room | Where each document belongs | 10 folders, 32 sub-folders, 64 slots |
| Risk | What must be known, as checks grouped into indicators and workstreams | 8 workstreams, 55 indicators, 278 checks |
| System | What each of the bank's systems asks for | Private to the institution |

### 6.1 Risk checks

The checks are copied over from the first Bankability and repaired on the way (section 6.4).

- **Falsification is the backbone.** A check tests a stated assumption. "Does the entity have material foreign currency revenue?" tests "The entity has no FX exposure".
- **Checks branch.** An answer decides which checks follow.
- **Checks apply by role.** The checks for a guarantor apply to whoever holds that seat.
- **A check is answered by facts.** Its status is computed: open, waiting for an earlier answer, not relevant after an earlier answer, answered, answered on thin evidence, outdated, or contested.
- **Strength of evidence.** The standard says what is ideal per stage: what the client says is fine at screening, and by approval it should be the best kind of document. The tool shows what each assumption rests on. It demands nothing.
- **Looking for disproof is recorded**, also when nothing is found.
- **A topic's pairing of a risk statement and a mitigant statement** exists for 2 of the 55 indicators. The rest are written when a real deal needs the topic.

### 6.2 Adjusting the standard

There are three layers. A lower layer can add, change or switch off anything in a layer above.

| Layer | For | Example |
|---|---|---|
| Base | Everyone | The public standard |
| Institution | All deals of one institution | Its own impact checks, its timing, its system fields |
| Deal | One deal | "Add a check on the milk-price clause." |

- **The officer adjusts by saying so.** The AI writes the change into the deal layer. The tool checks that it is well formed and shows what changed.
- **Moving an adjustment up is a deliberate step.** That is how the standard learns from real deals.
- **Two ways to switch something off**, both reversible and both with a reason:
  - "Not now": it drops out of the next list, stays visible, and comes back if something it depends on changes.
  - "Not for this deal": it is off, with the reason, the name and the date.
- **The institution layer may mark a requirement as not switchable** at deal level. By default nothing is marked.

### 6.3 The standard as a website

The standard must be publishable as a website later. Four rules make that possible:

1. **The standard is data only.** Every folder, slot, indicator and check has a stable ID, a title and its text in plain language. No meaning lives in code.
2. **Every reference is by ID**, and a test fails on a reference to something that does not exist.
3. **One list per vocabulary**: stages, roles, kinds of document, kinds of link. Checks refer to those lists.
4. **One build step, two results.** The source files are turned into the file the tool reads and into one readable page per indicator and per data-room folder. A site generator can publish those pages as they are. The first Bankability's website already rendered its standard this way.

The standard carries a version. A deal records which version it uses.

### 6.4 Repairs on the way over

Found when the first Bankability's standard was measured:

1. The checks name 160 kinds of acceptable evidence. Only 24 exist in the list of 64 document types.
2. Three links point at indicators that do not exist.
3. Nothing says which indicators apply to which kind of borrower.
4. Some questions for the client still contain an unfilled placeholder.
5. Nothing says whether a question is for the client or for the lender.
6. No checks are due after due diligence.

## 7. The next list

The tool always outlines what to do and collect next. It lists every candidate, with the stage it is ideally there for, what else depends on it, and how long it has been open:

- documents the data-room structure expects and the client folder lacks;
- checks that are open, and assumptions that rest on thin evidence;
- questions that were asked and are not answered;
- pages and facts that rest on a source that was replaced;
- system fields without a value.

The AI chooses what to show and how.

## 8. What the tool does

| Command | What it does |
|---|---|
| `start` | Creates the deal folder and its empty memory |
| `status` | The structure, what changed, and the candidates for the next list |
| `add` | Records a checked set of changes: sources, facts, subjects, links, answers, decisions |
| `show` | Looks things up: a source, a fact, a subject, what a check rests on, what a change affects |
| `pages` | Fills in the generated part of each wiki page and writes the table of contents |
| `check` | Reports problems and oddities: numbers not found in their source, pages without sources, links to things that do not exist |
| `adjust` | Applies a change to the deal's layer of the standard |
| `file` | On the laptop only: sorts documents into the client folder and writes the manifest |
| `doctor` | Reports the environment it runs in |

Every change is written to an append-only log. Each entry carries a fingerprint of the entry before it, so that tampering shows.

Document text is data and never an instruction. Every entry in the memory names its source and who asserted it, and all writes go through the tool.

## 9. What the AI does

The skill tells the AI how to work with the folder and the tool. The AI:

- reads what is shared, with the host's own tools;
- proposes sources, facts, parties and links, and records them through the tool;
- writes and maintains the wiki pages;
- chooses what to present and how;
- looks for what would disprove an assumption before what supports it.

There is one skill. The methods are its reference files, read when a task needs them.

## 10. Systems and documents

- **Systems.** The system structure lists what each of the bank's systems asks for, and at which of its gates. The institution writes it, inside its own tenant. The tool prints an entry sheet per system: each value with its source and its status. The officer types the values in through the browser. A value that changes after it was entered is flagged.
- **Documents.** The CIP and the FP are drafted by the AI from the wiki and the facts, in Word, with the host's tools. A CIP lists the assumptions that still need testing. An FP is driven by risk conclusions.

## 11. Simple to audit

These rules are checked by a test that fails the build:

- Python standard library only.
- No network access, no starting of other programs, no `eval`, no reading of environment variables.
- Every write goes through one function and stays inside the deal folder.
- No function longer than 100 lines.
- The whole tool stays under 3,000 lines, in at most six files.
- A new command or a new kind of record names the real deal that needed it.

A two-page audit note says what the tool does, what it can touch and how to verify a release.

The size limit is a starting value. Because everything is built at once, it is larger than the 1,500 lines first proposed.

## 12. Order of building

Everything is built before first use. The order follows what depends on what, and each step lands with its tests and a run on a made-up deal.

1. The standard: copied over, repaired, compiled, and rendered as pages.
2. The memory: the folder, the index, the facts, the graph and the log.
3. The checks: status, assumptions, strength of evidence, switching off, and the next list.
4. The wiki: the page form, the generated parts, the table of contents and the checks on pages.
5. The laptop package: sorting, the manifest and `doctor`.
6. The skill for Cowork.
7. The system structure and the entry sheets.
8. Guidance for drafting the CIP and the FP.

One thing does not wait for the build: a ten-minute test in the tenant of how Cowork saves and overwrites files, and whether a script shipped in a skill is found and run. If saving many files proves unreliable, the wiki pages move inside the memory file and the Markdown files become views.

## 13. Not part of Bankability 2

- **Spreading.** A separate tool, perhaps later. The bank has its own.
- **A website with the standard and an MCP for collecting data.** Possible later. The manifest and the rules in section 6.3 keep the way open.
- **A server.** Not wanted.

## 14. Still needed from the officer

1. A repository. This session cannot create one.
2. The licence. The first Bankability's standard is under Apache 2.0.
3. The ten-minute test in the tenant.
4. Access to Copilot Code.
5. Whether client calls may be transcribed.
6. The fields of the bank's systems, when they can be shared inside the tenant.
