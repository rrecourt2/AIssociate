# Bankability 2: design

16 November 2026. This document describes Bankability 2 as it is built, and what is left for later. It gathers the decisions taken in the design interview of 13 and 14 November, and the owner's decisions after the three rounds of the trial on 15 and 16 November.

The tool has run on a made-up deal and, in three rounds, on the public documents of a real company. It has not been tried in Microsoft Copilot Cowork, and not on a live deal with an analyst.

## 1. What it is

Bankability 2 keeps the record of an investment deal. It keeps everything that is shared about a deal in one folder, in a form that a person and any AI tool can pick up again later. It knows how the deal is structured, what is known, what is assumed and what is still missing, and it always says what to do and collect next.

It is written for a development finance institution and for an investment analyst who works with an AI assistant. The first host is Microsoft Copilot Cowork.

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
10. **A backbone, not a script.** The standard says where to look and keeps the record honest. It does not replace the analysis. A capable assistant follows the deal, not the list.

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
| Inside Copilot Cowork | Shipped inside the skill, run in the workspace of a task | First, once tested in the tenant |
| On the laptop | Run from a terminal on the synced OneDrive folder | First. It also does the file work Cowork cannot do. |
| Through Copilot Code | A local MCP shell around the same tool | Later, when access is granted |

Cowork cannot call a program on the laptop. Microsoft requires an MCP server to be reachable over the internet, so there is no local server for Cowork.

What Microsoft documents for Copilot Cowork in November 2026, none of it tested with this tool yet:

- A custom skill is a folder with `SKILL.md` and up to 20 other files, 10 MB together. It sits in the user's OneDrive under `Documents/Cowork/skills`, or is uploaded as a zip with `SKILL.md` at its root, or comes inside a plugin that an administrator deploys. Files in `scripts` are run, not read. The packaged skill has 16 files and about 1 MB.
- Each task runs in a workspace of its own, which starts empty and is removed when the task ends. Nothing carries over between tasks but the files in OneDrive or SharePoint, custom instructions and the instructions of a project.
- What a task writes is saved to OneDrive. Replacing a file where it is, is documented only for Word, Excel and PowerPoint, and Cowork cannot delete. So "save each file back to its place" is the assumption to test first.
- The model can be chosen. In tenants inside the EU Data Boundary the Claude models are off unless an administrator turns them on, so the skill must not depend on one model.
- OneDrive and SharePoint show Markdown as formatted text. An HTML file is shown in Cowork's own preview, and in SharePoint it is often downloaded. `wiki.html` is therefore opened from the synced folder on the laptop.

## 4. The deal folder

```text
<Deal>/
├── Client folder/      can be shared with other lenders and consultants
│   ├── …               every document the client shared, in this one folder
│   ├── index.md        the documents by the folders of the data room, and the slots still empty
│   └── manifest.json   one entry per document
└── Internal/           the analyst and the deal team only
    ├── sources/        calls, emails, notes, press articles, internal memos, and extracts/
    ├── record/         record.json: the record and its log; only the tool writes it
    ├── wiki/           deal, parties, people, context, topics, terms, work, with index.md and wiki.html
    ├── standard/       the standard this deal uses, and its adjustments
    └── outputs/        drafts of the scan, the CIP and the FP
```

- **Two systems, kept separate.** The client folder holds what the client shares. The internal folder holds everything else. The test for where something goes: may the client see it?
- **The internal folder points into the client folder.** The client folder knows nothing about the internal one, so it can be handed to someone else as it is.
- **The data room is an index, not a tree of folders.** The first version made ten folders with their sub-folders in every new deal, and the owner found that overwhelming. The standard still holds the data room as data: folders, sub-folders and slots. The kind of a document gives its slot. Every document sits in the one client folder, and `index.md` lists them by the folders of the data room and names the slots that are always expected and still empty.
- **The manifest is the only seam.** It has one entry per document: its path, its slot in the data room, its kind, the party, the period, a fingerprint of the file, and the text extract made from it if there is one.
- **Filing is done on the laptop.** Cowork cannot move or delete files. The `file` command moves a document that sits anywhere in the deal folder to the client folder, or to the internal sources if its kind has no slot. It never overwrites: a document whose name is taken is refused.
- **Only folders that something writes to.** The entry sheets for the bank's systems are printed by `show sheet`. They have no folder.
- **One sharing rule.** Share the client folder and nothing else.

## 5. The record, the wiki and preferences

Three things have three homes.

| | Holds | Home |
|---|---|---|
| **The record** | What is known: exact, sourced, written only by the tool | `Internal/record/record.json` |
| **The wiki** | What is understood. It cites the record. | `Internal/wiki` |
| **Preferences** | How to work | By what they are about: see 5.5 |

Earlier versions called the record the memory. The word now means what an assistant remembers about its user, so it is no longer used for what the tool keeps. The code still calls the record `memory` in the names of its variables.

The record is one file. It holds an index of the sources, the facts, the graph, the decisions and questions, and a log.

### 5.1 The index: where things are

One entry per source: a document, a call, an email or a note. It says what the source is, where it is, how old it is, and which pages or minutes cover which topic. The AI reads the index first and goes back to the source itself for a quote or for nuance.

```json
"S-003": {"title": "Call with the CFO, 12 November 2026", "kind": "call", "date": "2026-11-12",
          "where": "Internal/sources/2026-11-12 CFO call.md", "fingerprint": "9f2c…",
          "about": ["P-001"], "read": "full", "sent_by": "The investment analyst",
          "map": [{"at": "min 12–18", "topic": "margins", "gist": "Explains the margin drop by milk prices."}]}
```

- **The kind of a source decides two things:** where the document is filed, and how strong its evidence counts in each check.
- **The original is the source.** A text extract made from it, for example from a scan, is a working aid. It is kept in `Internal/sources/extracts`, the source names it under `extract`, and `where` and the fingerprint stay those of the original. A fact cites the place in the original.

### 5.2 The facts: what is known

Exact things: names, amounts, dates, terms, shares, commitments. If something would go into a system field or a table, it is a fact. If it would go into a paragraph, it stays in the source and the index says where.

```json
"F-011": {"about": "P-001", "statement": "Borrowings were KES 1,300m at 31 December 2025.",
          "label": "Borrowings", "value": 1300, "unit": "KES m", "as_of": "2025-12-31",
          "source": "S-002", "place": "note 18", "said_by": "document",
          "answers": [{"check": "OBS_DEBT_001", "value": true}], "state": "current"}
```

- **Who said it.** A document, the client, the analyst, a third party, or the AI's own inference.
- **Replaced, not removed.** A fact that is replaced keeps its place, with the state `outdated` and a pointer to what replaced it. A fact can be marked `disputed`.
- **A figure at a date is not replaced by a later one.** Both stay current. The tool shows the latest, and the latest answers a check.
- **A fact comes from a source.** A wiki page or a draft is the AI's own writing and is never evidence for a fact.
- **A search that found nothing is a fact too**, marked as such.
- **An answer can be withdrawn.** The change is logged like any other.
- **Looked up by need.** `show facts` takes IDs or words and lists only the facts that hold one of them: the facts about a subject, from a source or in answer to a check. An assistant never has to print them all.

### 5.3 The graph: how the deal is structured

Who the borrower is, who guarantees, which customers, suppliers and related parties matter, and how they depend on each other. The checks grow out of it.

```json
"subjects": {"P-001": {"kind": "party", "name": "Cedar Foods Ltd"},
             "P-002": {"kind": "party", "name": null, "note": "A group company is asked to guarantee. Which one is not decided."},
             "L-001": {"kind": "facility", "name": "EUR 12m senior loan"}},
"links":    {"R-001": {"from": "P-001", "type": "borrows", "to": "L-001", "state": "confirmed", "source": "S-001"},
             "R-002": {"from": "P-002", "type": "guarantees", "to": "L-001", "state": "proposed",
                       "why": "The teaser asks the parent to guarantee the loan."}}
```

- **A party is stable and its role is a link.** Whoever `borrows` is the borrower. When the borrower changes, the facts stay with the company they are about, and the checks for "the borrower" follow the link to the new one.
- **A facility is the loan under review.** The roles that belong to the loan, and the checks on a guarantee or on security, arise only from links that point at a facility. The standard says for each kind of link which kinds of subject it counts for.
- **Debt that already exists is a link, not a facility.** The lender `lends_to` the company, and the terms, the security and the guarantors of that debt are facts about the link.
- **An owner link counts where it points at a party or a group.** `owns` then gives its role and brings the checks on the tie. Who owns a plant or a project is recorded the same way and brings no checks.
- **A subject can end.** A contract that was cancelled or a project that was shelved keeps its facts and its place in the log. It is asked nothing, and its links stop counting.
- **A person is not a company.** A natural person is a kind of subject of its own and is asked only what fits a person.
- **Repayment may rest on someone other than the borrower.** A facility `relies_on` the party or group whose cash flow repays it: the perimeter. The business and its money are examined once, on the perimeter. A company inside it is examined as a legal entity: its owners, its integrity, its board, its standing.
- **Checks on a project follow the financing.** A facility `finances` a project or an asset. Other projects are described and not checked.
- **A role can be an empty seat**, such as a guarantor who is not yet known. Its checks wait until it has a name. Analysis of the rest goes ahead.
- **Anything can propose.** The AI proposes parties and links as it reads, and the analyst can simply say so. A proposed link is usable at once.
- **A link carries its reason:** why this party matters for repayment. What is left out is a decision, with a reason that points to facts.
- **The AI states the structure once**, mentions it again when it changes, and asks only when it cannot decide.

Decisions and questions to the client are recorded as well. A question is recorded as soon as it is worth asking, with the checks its answer would close. It is a draft until it has the date it was sent.

### 5.4 The wiki: what is understood

The standard gives the work its rigour. The wiki gives it depth: what the business is, how it works, how its parts relate, what is particular about it, and how its context shows in its figures. It is a wiki, not the financial proposal. It describes, objectively and in context. The FP concludes, and is condensed from it. The analyst reads the FP, not the wiki, so there is no review duty. When the analyst corrects something in a draft or in chat, the AI corrects the page and the fact behind it.

Seven shelves, two levels deep:

| Shelf | One page per |
|---|---|
| Deal | the deal, and each plant, line, project, facility or contract that has a name |
| Parties | company, group or person that needs one |
| People | group of people: the client's side, our side, other lenders and advisers |
| Context | what surrounds the company: its history, its market and competitors, its products and how they are made, the country |
| Topics | subject of analysis |
| Terms | term under negotiation |
| Work | piece of work, such as a consultant to hire or a site visit, and the working notes |

- **A page for each subject a reader would look up.** The wiki holds the larger context, also where no check asks for it: a plant, a machine, a project, a product, the history of the company, its market, a customer that matters. A subject earns a page when two or more sources bear on it or other pages keep mentioning it. As a guide there are about as many pages as sources, or somewhat more. Not a page: a check, a single figure, a document retold, an account of what was done. The tool creates a page only for the deal, for each borrower, repayment source, guarantor and sponsor, and for each financed project.
- **The contents page is the map.** It gives the first sentence of every page. An assistant reads the contents page and the page of the deal first, and opens another page only when the task needs it. A long wiki is then no burden.
- **One page lists every source**: what it is, how far it was read, how many facts rest on it, and links to its original and its extract.
- **A page describes before it lists.** What the thing is, how it works, how it relates to the rest, what is particular about it, how the context shows in the figures, and only then the assumptions and the open points. A project or an asset gets a real page: what, where, how big, by when, who pays, how far it has come.
- **A few details that show understanding**, each specific to this business, each tied to a figure, each with a source. No filler.

Every page has the same parts:

1. **What it is.** One to three plain sentences. The first can stand alone, and is the page's line on the contents page.
2. **At a glance.** Filled in by the tool, and kept short. The page of the deal: the stage, the loan with the parties and the project at its centre, the claims by pillar and one line per claim that is challenged or contested. The page of a subject: its roles, its links that have not ended, and its challenged claims, questions and decisions. Any other page: one line that names what it is about. Names link to their pages.
3. **What we know.** The description, with the ID of the fact or source each sentence rests on.
4. **Assumptions and open points.** Each assumption with what it rests on. Then what is unknown, and what was looked for and not found.

The tool lists the sources at the foot and says where one was not read in full. Below them it adds the key values, once the deal or the subject has a fact with a label: the latest value under each label. It also writes the contents page. The AI may move a part the tool fills in. The text comes first.

`check` reads the pages, and the Markdown drafts directly in `Internal/outputs`, paragraph by paragraph. A draft that was sent or replaced is moved to a sub-folder and is then left alone:

- It reports a citation of something that does not exist, a link to a page that is not there, a page that no other page links to, a page with text and no citation, and a number that no record cited in the same paragraph holds. The working notes say how to work and are not asked for citations.
- It reports a citation of a fact that was replaced or is disputed, unless the sentence starts with a plain word that marks it: "Outdated:" or "Disputed:". New information is merged in. What it replaces stays visible only where that matters.
- It does not judge whether a sentence says what its fact says.

Other rules for a page:

- One subject per page, and each thing said once.
- Nothing is written when a source adds nothing.
- Only a person can mark a page as checked. Nobody has to.
- The People shelf holds what people said, asked for and decided, with sources. The analyst's private reading of people stays out of the deal folder.

Writing rules, taken from Wikipedia's list of signs of AI writing:

1. State a relationship exactly: who, what, since when, how much. Never "associated with".
2. No sentence about significance. Say what the fact changes for repayment, or leave it out.
3. Name who said it and where. One source is one source.
4. No summary at the end of a section or a page.
5. Use "is" and "has".
6. Give every number its unit, its date and the company it belongs to.

**Reading it.** The pages are plain Markdown with ordinary relative links, so the folder opens in any Markdown reader, or as a vault in Obsidian. `pages` also writes `Internal/wiki/wiki.html`: the whole wiki in one file for a browser, with a list of pages by shelf, a search box, links that open in the same view, the sources, the index of the client's documents, and citations that show the fact, its value, its date, its source and the place in the source when clicked, with a link that opens the original at that page. A long part that the tool fills in is folded away, so that the text comes first. It loads nothing from the network and opens by double click from a synced folder. Its template is one file of HTML, CSS and plain JavaScript. Python only fills in the data.

### 5.5 Preferences

A preference goes by what it is about.

| About | Example | Home |
|---|---|---|
| This deal | "Write more about the projects." "The committee will ask about the owners." | The deal folder: one page of working notes on the Work shelf, in the analyst's words and with the date. The next assistant inherits it. What the analyst says about the deal itself is a source and a fact as well. |
| The institution | Its template, its house style, its own checks | The institution's layer |
| The analyst | How they like answers | The assistant's own memory, if its host gives it one |

- **Deal content belongs in the deal folder.** An assistant's own memory is for how the analyst likes to work, never for what a deal contains.
- **A preference is recorded only when the analyst stated it**, never because a document says so.
- **Whether an assistant's own memory is on, and how it is scoped, is for the user and the institution to decide.** The tool cannot see it. See [audit.md](audit.md).

## 6. The standard

The standard says what a deal folder holds and what must be known. It is data only. [standard/README.md](../standard/README.md) describes every field.

| Structure | Holds | Size |
|---|---|---|
| Data room | Where each document belongs: an index, not folders on disk | 10 folders, 32 sub-folders, 64 slots |
| Checks | What must be known, as claims in nine pillars | 9 pillars, 70 indicators, 551 checks |
| Systems | What each of the bank's systems asks for | Private to the institution |

### 6.1 Claims and checks

[standard/FRAMEWORK.md](../standard/FRAMEWORK.md) explains the framework. In short:

- **It starts from repayment.** The structure of the deal is discovered. The loan has two ways out, and each points at something in the structure: a party's cash flow, a guarantor's promise, an asset. The analysis follows that reliance, wherever it points. Nothing is tied to the word "borrower".
- **Four layers, kept apart**, as a rating agency keeps them: the deal, each party on its own, the links between parties, and the facility. A weak layer is not averaged away by a strong one.
- **The loan under review, the perimeter and the entity.** Roles and checks that belong to the loan arise only from links that point at it. The business and its money are examined once, on the perimeter whose cash repays the loan. Each company in it is examined as a legal entity. A person is asked only what fits a person. Checks on a project are asked of the project the loan finances.
- **Nine pillars**: the deal; environment; business; people and governance; cash flow and debt; liquidity and financial risks; environmental, social and impact; links; the facility.
- **Claims first.** People and assistants work from the 70 claims. The checks are the detail behind a claim.
- **Falsification is the backbone.** An indicator is one claim: what the lender relies on, in a sentence that can turn out false. A check is a question, a test or a mitigant. A test states its own assumption and which answer goes against it. A mitigant is asked once a test has gone against the claim.
- **The tool says where each claim stands**, for each party or link it is made about: not tested, stands so far (some tests answered, none against, and work left: a test open or waiting, or an answer on someone's own word or on evidence that is thin or old), stands (every test answered and nothing left to strengthen), challenged (with each mitigant holding, failing or not known) or contested (two facts disagree on a test, or on a question behind the claim). There are no scores and no weights.
- **Checks apply by role and by link.** A role is the end of a link, so the checks follow the role when a party changes. A guarantor is asked whether it can pay and must pay, not how it runs a factory. A link that exists brings its own checks: a guarantee, an owner, a key customer, a key supplier, another lender.
- **Discovery opens what applies and calls for structure.** The kind of credit and the sector decide which checks apply. Until they are answered, those checks wait. Some answers mean a party or a link must exist. The tool says so until it is added, or until a decision says why not.
- **Who speaks matters.** An answer that goes against a claim is believed whatever it rests on. A favourable answer that rests only on what a party said is marked as someone's own word, and a claim does not stand on that alone.
- **Strength of evidence.** Each check says which kinds of source are the best evidence, which support, and which are only what someone said. Each stage names what is ideal by then. The tool shows what each answer rests on. It demands nothing.
- **Reference points, not thresholds.** A few checks carry a reference point, such as "above 20", each with its reason. An institution or a deal can change it.
- **Size and judgement.** A test asks about what matters for repayment. Where the thing exists but is too small to matter, the answer is the favourable one and the fact says how small. A test is answered as soon as it is decided, whatever the terms of the loan turn out to be.
- **Rigour and depth.** The standard gives rigour. A few open questions ask for description: how the business earns its money, what is particular about it, what the project is. Their answers feed the wiki, which gives the understanding.
- **A gap with an agreed action.** A check can stay open with a condition, a covenant or a task, an owner and a date. That is a decision that covers the check.
- **A check settled for one subject.** A decision that covers a check for one party, asset or link, with its reason and without an owner or a date, takes the check off there and leaves it asked of the others.
- **A claim is looked at again** when a source of a kind that bears on it arrives, or an answer elsewhere changes.
- **Looking for disproof is recorded**, also when nothing is found.

### 6.2 Adjusting the standard

There are three layers. A lower layer can add, change or switch off anything in a layer above.

| Layer | For | Example |
|---|---|---|
| Base | Everyone | The public standard |
| Institution | All deals of one institution | Its names for the stages, its own checks, its system fields |
| Deal | One deal | "Add a check on the milk-price clause." |

- **The analyst adjusts by saying so.** The AI writes the change and hands it to the tool. The tool checks it and records it in the deal's layer, with the reason, the date and who asked.
- **The base is copied into the deal folder** when the deal starts, so the folder says by itself which standard it uses. `upgrade` replaces the copy with the standard that comes with the tool, and logs the change of version.
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

- claims that are challenged, contested or to look at again;
- structure that is still open: a role nobody holds yet, a link that is proposed and not confirmed, a party or link that an answer calls for and that is not there;
- documents the data-room structure always expects, or that open checks look for, and that the folder lacks;
- checks that are open, contested, or answered on evidence that is thin or old, each with the stage it is ideally answered by and how many checks wait on it. Within a stage they come in order of closeness to the loan: the deal, then the loan and the parties and project at its centre, then their links, then the rest;
- gaps with an agreed action: a decision that covers a check and names an owner or a date;
- questions without an answer, sent or not yet sent;
- facts that rest on a source that was replaced;
- system fields without a value;
- answers to a check that is not asked about that subject, or is not relevant there.

`status --for <ID>` keeps all of this to one subject or link. Each check in the list ends with its ID and the answer it takes.

Open checks are the work of due diligence, and `status` says so in two lines: by which stage the open checks are ideally answered, and what the waiting ones wait for. Many of those are mitigants, which are asked only if a test goes against its claim. The standard makes a check wait wherever one answer opens it: the checks on terms wait until terms are on paper, the checks on an asset for whether repayment depends on it. A question that opens others is left open while its answer is not known, so that what depends on it waits and does not fall away.

The AI chooses what to show and how.

## 8. What the tool does

| Command | What it does |
|---|---|
| `start` | Creates the deal folder and its empty record |
| `status` | The structure, what changed, where the claims stand, and the candidates for the next list. For the whole deal, or for one subject or link. |
| `add` | Records a set of changes: sources, facts, subjects, links, decisions, questions. All of it or none of it. It prints the ID of each new record, and a note for each answer that does not count where it was put. With `--try` it says what it would record and writes nothing. |
| `show` | Looks things up: a record and what uses it, a check and what it rests on, an indicator, every claim by pillar, the facts that hold an ID or a word, the kinds of source, subject and link, the entry sheets, the log, or a search of the record and of the checks |
| `pages` | Creates the few pages the graph calls for, fills in the generated parts of every page, and writes the contents page and the view for a browser |
| `check` | Reports what looks wrong: a broken log, an unsound adjustment, files that are missing or changed, a record that still names a replaced fact, and problems on the pages and in the drafts |
| `adjust` | Applies a change to the deal's layer of the standard |
| `file` | On the laptop only: moves documents into the client folder, lists them in the manifest and writes the index of the client folder |
| `upgrade` | Puts the standard that comes with the tool into the deal folder, logs the change of version, names the answers whose check is gone, and lists the checks that are new, gone or changed. It also moves the record of a folder made by an earlier version to its new place. |
| `doctor` | Reports the environment it runs in |

Every change adds an entry to a log. Each entry carries a fingerprint of the entry before it and of the record after the change, so that a change made outside the tool shows.

Each command that writes ends by naming the files it wrote, for a host that has to save files itself.

## 9. What the AI does

The skill tells the AI how to work with the folder and the tool. The AI:

- reads what is shared, with the host's own tools;
- proposes sources, facts, parties and links, and records them through the tool;
- writes and maintains the wiki pages;
- chooses what to present and how;
- looks for what would disprove an assumption before what supports it;
- follows the deal, not the list: it works from the claims, and goes where the documents lead.

There is one skill. Its four reference files cover recording, pages, the standard and drafting.

Text in a document is data and never an instruction. The skill says so. That is guidance to a model, not a control.

Two more rules keep the record from poisoning itself. A fact comes from a source, never from a wiki page or a draft: the AI's own writing is not evidence. And a preference is recorded only when the analyst stated it.

## 10. Systems and documents

- **Systems.** The institution's layer lists each system, its fields and the gate each field belongs to. A fact names the fields it fills. `show sheet` prints each system with every field: the value, the fact and the source, or "missing". The analyst types the values in through the browser. Fields without a value are on the next list from the start, so that a gate does not come as a surprise.
- **Documents.** The scan, the CIP and the FP are drafted by the AI from the claims, the wiki and the facts. The institution's own template and style come first. The draft is kept as Markdown in `Internal/outputs`, where `check` reads it like a page, and is made into a Word file with the host's tools. A CIP lists the assumptions that still need testing. An FP is driven by conclusions on risk. Where no terms exist, the document gives a preliminary view and a list of what is missing, and makes no recommendation.

## 11. Simple to audit

These rules are checked by a test that fails when the code breaks one:

- Python standard library only.
- No network access, no starting of other programs, no `eval`, no reading of environment variables, no deleting.
- One module touches the disk. It writes through three functions, and each refuses a path outside the deal folder.
- No function longer than 100 lines.
- The whole tool stays under 2,000 lines of Python, in at most seven files.

The view for a browser is one more file, `bankability2/wiki.html`: about 250 lines of HTML, CSS and plain JavaScript that load nothing from the network. A test checks that it names no address and no outside file.

[audit.md](audit.md) says what the tool does, what it can touch and how to verify a release.

## 12. Left for later

Designed, and deliberately not built yet:

1. **Checking a fact against the text of its source.** The tool checks the pages against the facts. It does not read documents.
2. **Marking a system value as entered**, and flagging a value that changes after it was entered.
3. **Acting on two of the standard's hints.** The standard says which indicator an answer leads to, and when a topic matters more or less. `show` prints these. The next list does not use them yet.
4. **Document expectations per party.** The tool looks at the deal as a whole: an annual report in the folder counts, whoever's it is.
5. **A command to move an adjustment up** to the institution's layer.
6. **A local MCP shell** for Copilot Code.
7. **In the standard:** a module for funds, and modules for more sectors than banks, power and agribusiness.
8. **Checking what a sentence says.** `check` matches citations and numbers. It does not judge whether a sentence says what its fact says.

One thing comes before first use: a half-hour test in the tenant, with the made-up deal. Upload the zip and see that it is accepted. Ask for the Python version and a listing of the skill's folder. Attach the deal folder and run `status`. Run `pages` and see where the files land, and whether a file can be replaced where it is. Open `wiki.html` from Cowork, from OneDrive and from the synced folder. Start a second task and see that it begins empty. If saving many files proves unreliable, the wiki pages move inside the record file and the Markdown files become views.

## 13. Not part of Bankability 2

- **Spreading.** A separate tool, perhaps later. The bank has its own.
- **A website with the standard and an MCP for collecting data.** Possible later. The manifest and the rules in section 6.3 keep the way open.
- **A server.** Not wanted.

## 14. Open points

1. A half-hour test in the tenant of how Cowork runs a script from a skill and saves files.
2. A review of the standard by someone who does credit work.
3. Use on a live deal with an analyst. The trial on public documents ran in three rounds.
4. Whether an institution lets client calls be transcribed. It decides how much of the record can come from calls.
5. The fields of an institution's systems. They are written inside its own tenant and stay there.
6. Whether an institution lets its assistants keep a memory of their own, and how it is scoped.
