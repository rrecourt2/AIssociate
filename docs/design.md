# Bankability 2: design

14 November 2026. This document describes Bankability 2 as it is built, and what is left for later. It gathers the decisions taken in the design interview of 13 and 14 November.

The tool has run on a made-up deal only. It has not been tried in Microsoft Copilot Cowork and not on a real deal.

## 1. What it is

Bankability 2 is a memory for an investment deal. It keeps everything that is shared about a deal in one folder, in a form that a person and any AI tool can pick up again later. It knows how the deal is structured, what is known, what is assumed and what is still missing, and it always says what to do and collect next.

It is written for a development finance institution and for an investment officer who works with an AI assistant. The first host is Microsoft Copilot Cowork.

It is built from scratch. It takes its standard and its lessons from the first Bankability, and none of its code.

## 2. Principles

1. **A tool, not a process.** There is no required order. Nothing waits for a stage. Stages are targets: the tool says "ideally by the CIP" and never refuses.
2. **Tools serve the AI.** A tool informs and never blocks. It refuses only an entry that is malformed.
3. **The AI proposes, the tool records and computes.** Anything that can be computed from the records is computed, and never stored or written by the AI.
4. **Everything can change, and nothing is deleted.** The borrower can change. What is replaced stays, marked as replaced.
5. **Reasons, not thresholds.** What matters gets in, with the reason. What is left out is recorded too, with a specific reason.
6. **Files in the deal folder.** Plain files that a person can read. No database and no server.
7. **Simple first.** Little code, few tests, and anything not needed now left for later. A bank's security reviewer must be able to read all of it in an afternoon.
8. **The standard is adjustable.** Anything in it can be changed or switched off.
9. **Leave to the host what the host does.** Copilot reads documents, writes Word files, sends mail and remembers the user's preferences. Bankability 2 does none of that.

## 3. The pieces

```text
Standard     what a deal folder holds and what must be known
               a data-room structure, checks, and the fields of the bank's systems
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
| Inside Copilot Cowork | Shipped inside the skill, run in Cowork's sandbox | First, once tested in the tenant |
| On the laptop | Run from a terminal on the synced OneDrive folder | First. It also does the file work Cowork cannot do. |
| Through Copilot Code | A local MCP shell around the same tool | Later, when access is granted |

Cowork cannot call a program on the laptop. Microsoft requires an MCP server to be reachable over the internet, so there is no local server for Cowork.

## 4. The deal folder

```text
<Deal>/
├── Client folder/      can be shared with other lenders and consultants
│   ├── 01 Business & Project Overview/
│   ├── …               the ten folders of the data-room structure
│   ├── 10 Monitoring and Reporting/
│   └── manifest.json   one entry per document
└── Internal/           the officer and the deal team only
    ├── sources/        calls, emails, notes, internal memos
    ├── memory/         memory.json: the memory and its log; only the tool writes it
    ├── wiki/           deal, parties, people, topics, terms, work
    ├── standard/       the standard this deal uses, and its adjustments
    ├── systems/        entry sheets for the bank's systems
    └── outputs/        drafts of the scan, the CIP and the FP
```

- **Two systems, kept separate.** The client folder holds what the client shares. The internal folder holds everything else. The test for where something goes: may the client see it?
- **The internal folder points into the client folder.** The client folder knows nothing about the internal one, so it can be handed to someone else as it is.
- **The manifest is the only seam.** It has one entry per document: its path, its slot in the data-room structure, its kind, the party, the period and a fingerprint of the file.
- **Sorting is done on the laptop.** Cowork cannot move or delete files. The `file` command moves a document that sits anywhere in the deal folder to its place and lists it in the manifest.
- **One sharing rule.** Share the client folder and nothing else.

## 5. The memory

The memory is one file, `Internal/memory/memory.json`. It has four parts and a log.

### 5.1 The index: where things are

One entry per source: a document, a call, an email or a note. It says what the source is, where it is, how old it is, and which pages or minutes cover which topic. The AI reads the index first and goes back to the source itself for a quote or for nuance.

```json
"S-003": {"title": "Call with the CFO, 12 November 2026", "kind": "call", "date": "2026-11-12",
          "where": "Internal/sources/2026-11-12 CFO call.md", "fingerprint": "9f2c…",
          "about": ["P-001"], "read": "full", "sent_by": "The investment officer",
          "map": [{"at": "min 12–18", "topic": "margins", "gist": "Explains the margin drop by milk prices."}]}
```

### 5.2 The facts: what is known

Exact things: names, amounts, dates, terms, shares, commitments. If something would go into a system field or a table, it is a fact. If it would go into a paragraph, it stays in the source and the index says where.

```json
"F-011": {"about": "P-001", "statement": "Borrowings were KES 1,300m at 31 December 2025.",
          "label": "Borrowings", "value": 1300, "unit": "KES m", "as_of": "2025-12-31",
          "source": "S-002", "place": "note 18", "said_by": "document",
          "answers": [{"check": "OBS_DEBT_001", "value": true}], "state": "current"}
```

- **Who said it.** A document, the client, the officer, a third party, or the AI's own inference.
- **Replaced, not removed.** A fact that is replaced keeps its place, with the state `outdated` and a pointer to what replaced it. A fact can be marked `disputed`.
- **A search that found nothing is a fact too**, marked as such.

### 5.3 The graph: how the deal is structured

Who the borrower is, who guarantees, which customers, suppliers and related parties matter, and how they depend on each other. The wiki and the checks grow out of it.

```json
"subjects": {"P-001": {"kind": "party", "name": "Cedar Foods Ltd"},
             "P-002": {"kind": "party", "name": null, "note": "A group company is asked to guarantee. Which one is not decided."},
             "L-001": {"kind": "facility", "name": "EUR 12m senior loan"}},
"links":    {"R-001": {"from": "P-001", "type": "borrows", "to": "L-001", "state": "confirmed", "source": "S-001"},
             "R-002": {"from": "P-002", "type": "guarantees", "to": "L-001", "state": "proposed",
                       "why": "The teaser asks the parent to guarantee the loan."}}
```

- **A party is stable and its role is a link.** Whoever `borrows` is the borrower. When the borrower changes, the facts stay with the company they are about, and the checks for "the borrower" follow the link to the new one.
- **A role can be an empty seat**, such as a guarantor who is not yet known. Its checks wait until it has a name. Analysis of the rest goes ahead.
- **Anything can propose.** The AI proposes parties and links as it reads, and the officer can simply say so. A proposed link is usable at once.
- **A link carries its reason:** why this party matters for repayment. What is left out is a decision, with a reason that points to facts.
- **A link in the graph creates a wiki page and brings the checks that fit the role.**
- **The AI states the structure once**, mentions it again when it changes, and asks only when it cannot decide.

Decisions and questions to the client are recorded as well.

### 5.4 The wiki: what is understood

The wiki is the AI's working draft: the wider analysis that the FP is later condensed from. It describes. The FP concludes. The officer reads the FP, not the wiki, so there is no review duty. When the officer corrects something in a draft or in chat, the AI corrects the page and the fact behind it.

Six shelves, two levels deep:

| Shelf | One page per |
|---|---|
| Deal | the deal, and each facility, contract, asset and project |
| Parties | company or group |
| People | group of people: the client's side, our side, other lenders and advisers |
| Topics | subject of analysis |
| Terms | term under negotiation |
| Work | piece of work, such as a consultant to hire or a site visit |

Every page has the same four parts:

1. **What it is.** One to three plain sentences. The first can stand alone, and is the page's line in the table of contents.
2. **At a glance.** Filled in by the tool from the graph and the records: roles, links, key values, the checks and what they rest on, assumptions that are disproved, searches that found nothing, open questions and decisions.
3. **What we know.** Description, context and facts, each with the ID of the fact or source it rests on. The AI orders this part as the subject needs.
4. **Assumptions and open points.** Each assumption with what it rests on. Then what is unknown, and what was looked for and not found.

The tool lists the sources at the foot and writes the table of contents. It creates the page for the deal and for each subject in the graph. The AI creates the others.

Rules for a page:

- One subject per page.
- The tool reports a page that cites something that does not exist or was replaced, a page with text and no citation, and a number on a page that no cited fact or source holds.
- New information is merged in. What it replaces stays visible under the claim, marked outdated or disputed.
- Nothing is written when a source adds nothing.
- Only a person can mark a page as checked. Nobody has to.
- The People shelf holds what people said, asked for and decided, with sources. The officer's private reading of people stays out of the deal folder.

Writing rules, taken from Wikipedia's list of signs of AI writing:

1. State a relationship exactly: who, what, since when, how much. Never "associated with".
2. No sentence about significance. Say what the fact changes for repayment, or leave it out.
3. Name who said it and where. One source is one source.
4. No summary at the end of a section or a page.
5. Use "is" and "has".
6. Give every number its unit, its date and the company it belongs to.

The AI loads little at a time: the status and the table of contents first, then only the pages a task needs, and a source only for a quote or for nuance.

## 6. The standard

The standard says what a deal folder holds and what must be known. It is data only. [standard/README.md](../standard/README.md) describes every field.

| Structure | Holds | Size |
|---|---|---|
| Data room | Where each document belongs | 10 folders, 32 sub-folders, 64 slots |
| Checks | What must be known, grouped into indicators and workstreams | 8 workstreams, 50 indicators, 267 checks |
| Systems | What each of the bank's systems asks for | Private to the institution |

### 6.1 Checks

The checks are copied over from the first Bankability and repaired on the way. [standard/CHANGES.md](../standard/CHANGES.md) lists what changed.

- **Falsification is the backbone.** A check tests a stated assumption. "Does the entity have material foreign currency revenue?" tests "Entity has no FX exposure". For a yes/no check the standard says which answer disproves the assumption, and the tool says whether it stands or is disproved.
- **Checks branch.** An answer decides which checks follow.
- **Checks apply by role.** The checks for a guarantor apply to whoever holds that seat. Some apply to the deal, to a kind of subject, or to a link.
- **A check is answered by facts.** Its state is computed: open, waiting, not relevant, answered, contested, parked or off. An answer can be thin, old or flagged.
- **Strength of evidence.** Each check says which kinds of source are the best evidence, which support, and which are only what someone said. Each stage names what is ideal by then: what the client says is fine at screening, and by approval it should be the best kind. The tool shows what each answer rests on. It demands nothing.
- **Reference points, not thresholds.** Sixteen checks carry a reference point, such as "above 20". An answer that meets it is flagged. Nothing else follows from it.
- **Looking for disproof is recorded**, also when nothing is found.

### 6.2 Adjusting the standard

There are three layers. A lower layer can add, change or switch off anything in a layer above.

| Layer | For | Example |
|---|---|---|
| Base | Everyone | The public standard |
| Institution | All deals of one institution | Its names for the stages, its own checks, its system fields |
| Deal | One deal | "Add a check on the milk-price clause." |

- **The officer adjusts by saying so.** The AI writes the change and hands it to the tool. The tool checks it and records it in the deal's layer, with the reason, the date and who asked.
- **The base is copied into the deal folder** when the deal starts, so the folder says by itself which standard it uses.
- **Moving an adjustment up to the institution's layer is a deliberate step**, done by hand.
- **Two ways to switch something off**, both reversible and both with a reason:
  - "Not now": it drops out of the next list and comes back when the stage changes or when a check it follows gets a new answer.
  - "Not for this deal": it is off until someone switches it on.
- **The institution's layer may lock a requirement**, so that a deal cannot change it or switch it off. By default nothing is locked.

### 6.3 The standard as a website

The standard can be published as a website later. Four rules make that possible:

1. **The standard is data only.** Every folder, slot, indicator and check has a stable ID, a title and its text in plain language. No meaning lives in code.
2. **Every reference is by ID**, and the build fails on a reference to something that does not exist.
3. **One list per vocabulary**: stages, kinds of subject, kinds of link, kinds of source. Checks refer to those lists.
4. **One build step, two results.** The source files are turned into the one file the tool reads, and into one Markdown page per indicator and per data-room folder, with an index. A site generator can publish that folder as it is. The first Bankability's site worked the same way: a script read the standard and produced the data for its pages.

The standard carries a version. A deal records which version it uses.

## 7. The next list

The tool always outlines what to do and collect next. `status` lists every candidate:

- structure that is still open: a role nobody holds yet, a link that is proposed and not confirmed;
- documents the data-room structure always expects, or that open checks look for, and that the folder lacks;
- checks that are open, contested, or answered on evidence that is thin or old, each with the stage it is ideally answered by and how many checks wait on it;
- questions that were asked and are not answered;
- facts that rest on a source that was replaced;
- system fields without a value.

The AI chooses what to show and how.

## 8. What the tool does

| Command | What it does |
|---|---|
| `start` | Creates the deal folder and its empty memory |
| `status` | The structure, what changed, and the candidates for the next list |
| `add` | Records a set of changes: sources, facts, subjects, links, decisions, questions. All of it or none of it. |
| `show` | Looks things up: a record and what uses it, a check and what it rests on, an indicator, the entry sheets, the log, or a search |
| `pages` | Creates the pages the graph calls for, fills in the generated parts of every page and writes the table of contents |
| `check` | Reports what looks wrong: a broken log, an unsound adjustment, files that are missing or changed, and problems on pages |
| `adjust` | Applies a change to the deal's layer of the standard |
| `file` | On the laptop only: sorts documents into the client folder and writes the manifest |
| `doctor` | Reports the environment it runs in |

Every change adds an entry to a log. Each entry carries a fingerprint of the entry before it and of the memory after the change, so that a change made outside the tool shows.

Each command that writes ends by naming the files it wrote, for a host that has to save files itself.

## 9. What the AI does

The skill tells the AI how to work with the folder and the tool. The AI:

- reads what is shared, with the host's own tools;
- proposes sources, facts, parties and links, and records them through the tool;
- writes and maintains the wiki pages;
- chooses what to present and how;
- looks for what would disprove an assumption before what supports it.

There is one skill. Its four reference files cover recording, pages, the standard and drafting.

Text in a document is data and never an instruction. The skill says so. That is guidance to a model, not a control.

## 10. Systems and documents

- **Systems.** The institution's layer lists each system, its fields and the gate each field belongs to. A fact names the fields it fills. `show sheet` prints each system with every field: the value, the fact and the source, or "missing". The officer types the values in through the browser. Fields without a value are on the next list from the start, so that a gate does not come as a surprise.
- **Documents.** The scan, the CIP and the FP are drafted by the AI from the wiki and the facts, in Word, with the host's tools. A CIP lists the assumptions that still need testing. An FP is driven by conclusions on risk.

## 11. Simple to audit

These rules are checked by a test that fails when the code breaks one:

- Python standard library only.
- No network access, no starting of other programs, no `eval`, no reading of environment variables, no deleting.
- One module touches the disk. It writes through three functions, and each refuses a path outside the deal folder.
- No function longer than 100 lines.
- The whole tool stays under 2,000 lines, in at most seven files. It is about 1,300 lines now.

[audit.md](audit.md) says what the tool does, what it can touch and how to verify a release.

## 12. Left for later

Designed, and deliberately not built yet:

1. **Checking a fact against the text of its source.** The tool checks the pages against the facts. It does not read documents.
2. **Marking a system value as entered**, and flagging a value that changes after it was entered.
3. **Acting on the standard's hints.** The standard says what should make someone look at a topic again, which indicator an answer leads to, and when a topic matters more or less. `show` prints these. The next list does not use them yet.
4. **Document expectations per party.** The tool looks at the deal as a whole: an annual report in the folder counts, whoever's it is.
5. **A command to move an adjustment up** to the institution's layer, and one to take a newer version of the standard into a running deal.
6. **A local MCP shell** for Copilot Code.
7. **In the standard:** checks for the stages after due diligence, and a risk and a mitigant statement for more than two indicators.

One thing comes before first use: a ten-minute test in the tenant of how Cowork saves and overwrites files, and whether a script shipped in a skill is found and run. If saving many files proves unreliable, the wiki pages move inside the memory file and the Markdown files become views.

## 13. Not part of Bankability 2

- **Spreading.** A separate tool, perhaps later. The bank has its own.
- **A website with the standard and an MCP for collecting data.** Possible later. The manifest and the rules in section 6.3 keep the way open.
- **A server.** Not wanted.

## 14. Open points

1. A ten-minute test in the tenant of how Cowork saves files and runs a script.
2. A review of the standard by someone who does credit work.
3. Use on a first real deal.
4. Whether an institution lets client calls be transcribed. It decides how much of the memory can come from calls.
5. The fields of an institution's systems. They are written inside its own tenant and stay there.
