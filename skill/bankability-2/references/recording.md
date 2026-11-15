# Recording

You record by handing `add` one JSON object: a set of changes. The tool applies all of it or none of it.

```json
{
 "by": "assistant",
 "note": "Read the 2025 annual report",
 "op": "annual-report-2025",
 "sources": [{"ref": "ar", "title": "Audited financial statements 2025", "kind": "audited_annual_report", "date": "2026-03-28",
              "where": "Client folder/AR 2025.pdf", "extract": "Internal/sources/extracts/AR 2025.txt",
              "about": ["P-001"], "read": "part",
              "map": [{"at": "note 5", "topic": "revenue and customers", "gist": "Two customers above 10%."}]}],
 "subjects": [{"ref": "bluegate", "kind": "party", "name": "Bluegate Supermarkets"}],
 "links": [{"ref": "sale", "from": "P-001", "type": "sells_to", "to": "@bluegate", "state": "confirmed", "source": "@ar",
            "why": "Bluegate buys 31% of revenue, so whether it pays matters for repayment."}],
 "facts": [{"ref": "rev", "about": "P-001", "statement": "Revenue was KES 4,060m in 2025.", "label": "Revenue",
            "value": 4060, "unit": "KES m", "as_of": "2025-12-31", "source": "@ar", "place": "note 5",
            "said_by": "document", "answers": [{"check": "OBS_REV_001", "value": true}], "replaces": "F-005"}]
}
```

- **A new record has no `id`.** The tool gives it one. Give it a `ref` to point at it from the same set: `"@ar"`.
- **A record with an `id` is a change** to that record. Send only the fields that change. A field you send takes the place of the old one: a new `answers` list replaces the whole list.
- **`op`** is any name for this set. A set with the same `op` is not applied twice. Use it.
- **`base`** is optional: the revision you last saw. The tool refuses the set if the record has moved on.
- **`deal`** changes the deal itself: `{"deal": {"stage": "concept"}}`.

## What `add` prints

```text
Recorded as revision 3. Added: S-002, F-008, P-003, R-003. Changed: F-005.
@ar -> S-002
@rev -> F-008
@bluegate -> P-003
@sale -> R-003
```

Give every new record a `ref`, also a fact. The lines `@ref -> ID` tell you which ID to cite on a page. Do not work the IDs out by counting.

Where an answer does not count, `add` adds a note and records it all the same:

```text
Note: F-020 answers OBS_DS_005 for P-001, which is not asked that check. The answer is recorded all the same.
```

The check is not asked about that subject, or it is not relevant there. Look at the check with `show`, then move the answer with `"for"` or withdraw it. `status` keeps listing such answers until you do.

## Sources

One per document, call, email or note. `title` and `kind` are required.

| Field | Meaning |
|---|---|
| `kind` | A kind of source from the standard. `show kinds` lists them. A wrong kind is refused with the list. |
| `where` | The path of the original in the deal folder. The tool adds its fingerprint. |
| `extract` | The path of a text extract made from the original, if there is one. |
| `date` | The date of the document or the call. |
| `about` | The subjects it is about. |
| `read` | `full`, `part` or `none`. |
| `map` | Where things are: `at` (page, note, minute), `topic`, `gist`. Add entries for the parts you may need again. |
| `sent_by` | Who it came from. |

**The kind decides two things:** the folder the document is filed in, and how strong its evidence counts. Choose the kind for what the document is. An annual report that is not itself audited is `annual_report`, not `audited_annual_report`. A prospectus is `prospectus`. A newspaper article is `press_article`, and other public information is `public_source`. See [standard](standard.md).

## Filing documents

`file` moves documents to their place and lists them. It takes a list:

```json
[{"file": "Inbox/AR 2025.pdf", "kind": "audited_annual_report", "title": "Audited financial statements 2025",
  "party": "Cedar Foods Ltd", "period": "2025", "extract": "Inbox/AR 2025.txt"}]
```

- `file` is the path of the document in the deal folder, wherever it sits now. `kind` is a kind of source. The rest is optional.
- A document of a kind that has a slot in the data room goes to `Client folder/<file name>`. All client documents sit in that one folder. The tool then writes `Client folder/index.md`, which lists them by the folders of the data room and names the slots that are always expected and still empty.
- A document of a kind without a slot, such as a call, a note or a press article, goes to `Internal/sources/`.
- The tool never overwrites. If a document of that name is already there, it refuses that one and files the others. Give the document a name of its own and file it again.

### Originals and extracts

The original document is the source. A text extract that you or someone else made from it, for example from a scan, is a working aid.

1. **File the original.** `where` is always the original, and the fingerprint is the original's.
2. **Attach the extract.** Name it under `"extract"` in the filing: the tool moves it to `Internal/sources/extracts/`. Give that path as `extract` on the source.
3. **Cite the place in the original.** `place` on a fact is the page, the note or the table of the original, not a line of the extract. Keep the page numbers of the original in the extract when you make one.
4. **When the original comes later.** A source that was recorded from an extract alone is pointed at the original once that is filed: send the source's `id` with the new `where` and `extract`. The tool then takes the fingerprint of the original.

Where the extract and the original differ, the original is right.

## Facts

Record what would go into a table or a system field: names, amounts, dates, terms, shares, commitments. What would go into a paragraph stays in the source, and the `map` says where. `about`, `statement` and `source` are required.

| Field | Meaning |
|---|---|
| `about` | A subject, a link, or `DEAL`. A figure from consolidated accounts is about the group. A figure from a company's own accounts is about the company. |
| `statement` | One plain sentence that can stand alone. |
| `label`, `value`, `unit` | Give a label to a value that belongs in a table, such as `Revenue`. Use the same label for the same figure at another date. |
| `as_of` | The date the fact refers to: the balance sheet date, the end of the year. Not the date of the document. For a standing fact, the date of the source. |
| `source`, `place` | Where it comes from, and the page, note or minute. |
| `said_by` | Who says so: `document`, `client`, `officer`, `third_party` or `inference`. Use `client` for what any party to the deal says about itself: the borrower, its owners, a guarantor. Use `inference` for anything the document does not itself say: a conclusion, a figure you worked out, a borrower the note does not name. A favourable answer that only a `client` gave is marked as someone's own word. |
| `answers` | The checks it answers, as a list: `[{"check": "OBS_REV_001", "value": true}]`. Yes or no is `true` or `false`, a number is a number, a choice is one of the check's options, or a list of them where the check allows several. `status` shows the answer each check takes. An answer counts for the subject the fact is about. Add `"for": "G-001"` if it is for another subject. An answer to a check that is asked about the deal counts for the deal. |
| `fills` | The system fields it fills, such as `["CRM.country"]`. A field the institution's layer does not list is refused. |
| `nothing_found` | `true` for a search that found nothing. Say in the statement what was looked for and where. |
| `replaces` | The fact this one replaces: an earlier fact that was not replaced before. The old one stays, marked `outdated`. |
| `state` | Set `disputed` when the fact is contested, for example when two documents give the same thing differently. |

**A figure you worked out** from other facts, such as a ratio or a sum, is a fact of its own. Mark it `inference`, show the working in the statement and name the facts it comes from: "Borrowings were 0.32 times revenue in 2025: KES 1,300m (F-011) over KES 4,060m (F-008)."

### Changing, replacing and withdrawing

- **A fact was wrong, or a plan or a status has moved on.** Record the new fact with `replaces`. Carry over the answers the old fact gave, if they still hold: the answers of an outdated fact no longer count.
- **A balance at a date is not replaced by a later one.** Debt at 30 June is still true once debt at 30 September is known. Record the new figure as a new fact with the same `label` and its own `as_of`. Both stay current, and the tool shows the latest among the key values of the page. The same goes for a year: 2025 does not replace 2024, and an unaudited quarter does not replace an audited year.
- **A better source confirms or corrects a figure.** The audited statements give the revenue that the teaser gave in round numbers. Record the figure from the better source with `replaces`, so that the figure appears once and its answers rest on the better evidence.
- **Withdraw an answer** by sending the fact with the answers that remain: `{"facts": [{"id": "F-012", "answers": []}]}`. The change is logged like any other. Do not record a new fact only to undo an old one.

## Subjects and links

A subject is a party, a person, a facility, a contract, an asset, a project or a group. A link says how two subjects relate, and gives the role: whoever `borrows` is the borrower. `show kinds` lists the kinds of subject and of link.

- A subject needs a `kind`. Leave `name` empty for a role nobody holds yet, and say what is known in `note`.
- A link needs `from`, `type` and `to`. It starts as `proposed`. Set `state` to `confirmed` when a source confirms it, and to `ended` when it no longer holds.
- Give a link its `why`: why it matters for repayment.
- A mistake of your own is corrected in place: send the link's `id` with the right `type`, or with `"state": "ended"`.

A new link brings the checks that fit the role, and the checks on the link itself. Run `status --for <ID>` to see them.

### The loan under review

A `facility` is a loan that the lender is considering. Nothing else is a facility. The roles that belong to the loan come only from links that point at it: `borrows`, `guarantees`, `supports` and `secures` count when their `to` end is a facility, and `completion_support` when it is a facility or a project. A link of one of these kinds that points elsewhere gives no role and no checks, and `status` says so.

### Debt that already exists

Existing debt is never a facility. Record the lender as a party and link it to the company that owes the debt with `lends_to`. The terms, the security and the guarantors of that debt are facts about the link.

```json
{"subjects": [{"ref": "bank", "kind": "party", "name": "Rift Valley Bank"}],
 "links": [{"ref": "loan", "from": "@bank", "type": "lends_to", "to": "P-001", "state": "confirmed", "source": "S-004",
            "why": "Rift Valley Bank holds a charge over the Nakuru plant, so it is paid before an unsecured lender."}],
 "facts": [{"ref": "terms", "about": "@loan", "statement": "Rift Valley Bank lent Cedar Foods Ltd KES 800m, repayable by June 2030. KES 640m was outstanding at 30 June 2026.",
            "label": "Outstanding", "value": 640, "unit": "KES m", "as_of": "2026-06-30", "source": "S-004", "place": "page 1", "said_by": "document"},
           {"ref": "security", "about": "@loan", "statement": "The loan is secured by a first charge over the Nakuru plant and guaranteed in person by Mr Daniel Kiprop.",
            "as_of": "2026-06-30", "source": "S-004", "place": "page 2", "said_by": "document"}]}
```

- A guarantee or security for existing debt is a fact about that `lends_to` link. It is not a `guarantees` or `secures` link: those are for the loan under review.
- For a bond, the lender is its holders: a party named "Holders of the 2025 bond".
- Give a link to each lender that matters for ranking, security or refinancing. The others stay in a fact about total debt. Say in a decision which lenders got no link and why.
- The link brings the checks on another lender: who ranks ahead, what it holds, what lets it call its loan.

### A person

A natural person is a subject of the kind `person`. A person is asked only what fits a person: sanctions, political exposure, integrity, source of funds, disputes, and the capacity to pay where the person guarantees the loan under review. Record a person who owns, controls or guarantees. Directors and managers who do none of these stay as facts about their company.

### What the loan pays for

When the money pays for a project or an asset that can be named, record it as a subject and link the facility to it: `{"from": "L-001", "type": "finances", "to": "J-001"}`. The checks on a project are asked only of a project the loan finances. Another project of the business may be a subject with a page and facts. It gets no `finances` link and no checks.

### The perimeter

Repayment does not always come from the borrower. Link the facility to the party or the group whose cash repays the loan with `relies_on`: `{"from": "L-001", "type": "relies_on", "to": "G-001"}`. That is the perimeter.

- The business and its money are examined once, on the perimeter. A company that is a `member_of` the group is then not asked those checks. It is asked what belongs to a legal entity: its owners, its integrity, its board, its legal standing.
- A group is never asked the entity checks.
- So an answer on revenue, cash flow, debt, currency or related parties goes to the group, and an answer on owners or the board goes to the company. If you add the group later, `status` lists the answers that were recorded for the company and no longer count. Move each with `"for": "G-001"`.

## Decisions and questions

```json
{"decisions": [{"about": "P-001", "decision": "Lakeside Distributors gets no page and no checks of its own.",
                "reason": "It buys 14% of revenue and three other distributors serve the same region.",
                "rests_on": ["F-009", "F-015"], "by": "assistant"},
               {"about": "R-002", "decision": "The guarantee is to be backed by a standby letter of credit.",
                "reason": "The guarantor pays only after enforcement against the borrower.",
                "rests_on": ["F-021"], "by": "officer", "covers": ["OBS_GUARANTEE_MIT_001"],
                "owner": "officer", "due": "2027-01-31"}],
 "questions": [{"asked_of": "CFO of Cedar Foods", "text": "Please send the supply contracts.",
                "about": "P-001", "asked": "2026-11-12", "via": "S-003", "checks": ["OBS_INPUT_MIT_001"]}]}
```

**A decision** needs a `decision` and a `reason`, and should name the facts it rests on. A decision that `covers` checks is a gap with an agreed action: a condition, a covenant or a task. Give it an `owner` and a `due` date. It is also how you record that an answer calls for nothing more in the structure, and why. A working preference of the officer for this deal is a decision too, with `"by": "officer"`.

**A question** is recorded when it is sent, not when you think of it. Until then it is a suggestion to the officer or an open point on a page. It needs `asked_of` and `text`. Give it the date it was `asked`, the source it went out `via` if there is one, and the `checks` its answer would close: a question that names no check moves nothing when it is answered. When it is answered, change it: `{"id": "Q-001", "state": "answered", "answered_by": ["F-020"]}`.
