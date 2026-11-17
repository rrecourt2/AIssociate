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
- **A record with an `id` is a change** to that record. Send only the fields that change. A field you send takes the place of the old one: a new `answers` list replaces the whole list, and so does a new `map`. Send `null` to clear a field, such as the `owner` of a decision or the `asked` date of a question.
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

`add <deal> changes.json --try` checks the set and prints the same lines, and writes nothing. Use it before a large change to the structure.

Where an answer does not count, `add` adds a note and records it all the same:

```text
Note: F-020 answers OBS_DS_005 for P-001, which is not asked that check. The answer is recorded all the same.
```

The check is not asked about that subject, or it is not relevant there. Look at the check with `show`, then move the answer with `"for"` or withdraw it. `status` keeps listing such answers until you do. Withdrawing an answer leaves the fact as it is.

## Sources

One per document, call, email or note. `title` and `kind` are required.

| Field | Meaning |
|---|---|
| `kind` | A kind of source from the standard. `show kinds` lists them. A wrong kind is refused with the list. |
| `where` | The path of the original in the deal folder. The tool adds its fingerprint. |
| `extract` | The path of a text extract made from the original, if there is one. |
| `date` | The date of the document or the call. |
| `about` | The subjects it is about. |
| `read` | `full`, `part` or `none`. `extract` when you read the extract and not the original. The pages that cite the source say so. |
| `map` | Where things are: `at` (page, note, minute), `topic`, `gist`. Add entries for the parts you may need again. |
| `sent_by` | Who it came from. |
| `note` | Anything else. For what the analyst said in conversation: their words. |

**The kind decides two things:** the folder the document is filed in, and how strong its evidence counts. Choose the kind for what the document is. An annual report that is not itself audited is `annual_report`, not `audited_annual_report`. A prospectus is `prospectus`. A newspaper article is `press_article`, and other public information is `public_source`. See [standard](standard.md).

**What the analyst tells you in conversation** about the deal is a source too. It needs no file. Put the analyst's words in `note`, and mark the facts you take from it `said_by: analyst`:

```json
{"sources": [{"ref": "steer", "title": "Analyst, in conversation", "kind": "analyst_note", "date": "2026-11-12",
              "note": "We might finance the second UHT line."}]}
```

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
3. **Cite the place in the original.** `place` on a fact is the page, the note or the table of the original, not a line of the extract. When you make an extract, keep the page numbers of the original and copy its tables in full.
4. **When the original comes later.** A source that was recorded from an extract alone is pointed at the original once that is filed: send the source's `id` with the new `where` and `extract`. The tool then takes the fingerprint of the original.

Where the extract and the original differ, the original is right. Correct the extract, and say so in the `note` of the source.

## Facts

Record what would go into a table or a system field: names, amounts, dates, terms, shares, commitments. What would go into a paragraph stays in the source, and the `map` says where. `about`, `statement` and `source` are required.

| Field | Meaning |
|---|---|
| `about` | A subject, a link, or `DEAL`. A figure from consolidated accounts is about the group. A figure from a company's own accounts is about the company. |
| `statement` | One plain sentence that can stand alone. A list of facts prints its first 300 characters. |
| `label`, `value`, `unit` | Give a label to a value that belongs in a table, such as `Revenue`. Use the same label for the same figure at another date. |
| `as_of` | The date the fact refers to: the balance sheet date, the end of the year. Not the date of the document. For a standing fact, the date of the source. For an event, the date it happened: a year (`2015`) or a month (`2012-09`) will do where the day is not known. |
| `source`, `place` | Where it comes from, and the page, note or minute. Give the page as the PDF counts it, and the printed number in brackets where it differs: `p.24 (printed 22), note 16`. The browser view opens the original at that page. |
| `said_by` | Who says so: `document`, `client`, `analyst`, `third_party` or `inference`. Use `document` for the figures and terms in accounts, contracts, registers and the tables of a prospectus. Use `client` for what any party to the deal says about itself, its plans or its prospects: the borrower, its owners, a guarantor. That holds also when it says so in its own prospectus, report or website, or through the press. Use `third_party` for what a journalist, an analyst or an authority reports on their own account. Use `inference` for anything the document does not itself say: a conclusion, a figure you worked out, a borrower the note does not name. A favourable answer that only a `client` gave is marked as someone's own word. |
| `answers` | The checks it answers, as a list: `[{"check": "OBS_REV_001", "value": true}]`. Yes or no is `true` or `false`, a number is a number, a choice is one of the check's options, or a list of them where the check allows several. `status` shows the answer each check takes. An answer counts for the subject the fact is about. Add `"for": "G-001"` if it is for another subject. An answer to a check that is asked about the deal counts for the deal. |
| `fills` | The system fields it fills, such as `["CRM.country"]`. A field the institution's layer does not list is refused. |
| `nothing_found` | `true` for a search that found nothing. Say in the statement what was looked for and where, and what the search could not cover, such as a scan that cannot be searched by word. Such a fact answers a check only where the search covered the record that would show the thing: a register, or an authority's list. |
| `replaces` | The fact this one replaces: one earlier fact that was not replaced before. The old one stays, marked `outdated`. |
| `state` | Set `disputed` on each fact that is contested, for example the two figures that two documents give for the same thing, and on a figure worked out from one of them. Where several documents each give their own version, each version is its own fact, all are `disputed`, and each names the others in its statement. A fact that only reports the disagreement is true as it stands, and stays current. |

**From a table**, record each row you use as a fact of its own, with all its columns. A total that the table does not print is your inference. A row with half its columns leads to a page that says "not stated" about something the document states.

**A figure you worked out** from other facts, such as a ratio or a sum, is a fact of its own. Mark it `inference`, show the working in the statement and name the facts it comes from: "Borrowings were 0.32 times revenue in 2025: KES 1,300m (F-011) over KES 4,060m (F-008)." A fact of the same set is named by its `ref`: write `(@rev)`, and the tool puts the ID in its place. The same works in a `why`, a `reason` and a `decision`. A ref that the set does not define is left as written, so read the IDs that `add` prints. Marking a fact `inference` says that the reading is yours. How strong its evidence counts still goes by the kind of its source.

**A reading of several facts is not a fact.** What the figures mean together goes on one page, and other pages link to it.

### Changing, replacing and withdrawing

- **A fact was wrong or left something out, or a plan or a status has moved on.** Record the new fact with `replaces`. Carry over the answers the old fact gave, if they still hold: the answers of an outdated fact no longer count.
- **A balance at a date is not replaced by a later one.** Debt at 30 June is still true once debt at 30 September is known. Record the new figure as a new fact with the same `label` and its own `as_of`. Both stay current. The tool shows the latest among the key values of the page, and where both answer the same check, the later one answers. The same goes for a year: 2025 does not replace 2024, and an unaudited quarter does not replace an audited year.
- **A better source confirms or corrects a figure.** The audited statements give the revenue that the teaser gave in round numbers. Record the figure from the better source with `replaces`, so that the figure appears once and its answers rest on the better evidence.
- **Withdraw an answer** by sending the fact with the answers that remain: `{"facts": [{"id": "F-012", "answers": []}]}`. The change is logged like any other. Do not record a new fact only to undo an old one.
- **A fact was recorded about the wrong subject.** Send its `id` with the right `about`.
- **A slip that changes no figure**, such as the ID of a fact that a statement names, is corrected in place: send the `id` with the new `statement`.
- **A fact held figures at several dates.** `replaces` names one fact. Record the other dates as facts of their own.
- **A fact should not have been recorded at all**, such as an instruction on how to write. Send its `id` with `"state": "outdated"`, say why in the `note` of the set, and take its citations off the pages.
- **A source was withdrawn or reissued.** Record the new source with `replaces` and the ID of the old one. The old source stays, marked `replaced`, and `status` lists the facts that still rest on it. A page may cite it only after `Replaced:`.

## Subjects and links

A subject is a party, a person, a facility, a contract, an asset, a project or a group. A link says how two subjects relate, and gives the role: whoever `borrows` is the borrower. `show kinds` lists the kinds of subject and of link.

- A subject needs a `kind`. Leave `name` empty for a role nobody holds yet, and say what is known in `note`.
- A link needs `from`, `type` and `to`. It starts as `proposed`. Set `state` to `confirmed` when a source confirms it, and to `ended` when it no longer holds.
- Give a link its `why`: why it matters for repayment.
- A mistake of your own is corrected in place: send the link's `id` with the right `type`, or with `"state": "ended"`.
- A link that is your inference stays `proposed`. Say so in its `why`, and name the fact it rests on.
- `owns` to an asset or a project says who owns it. It brings no checks: the checks on an owner are asked where the link points at a party or a group.
- `sponsors` is for whoever stands behind the borrower or behind the project the loan pays for. Who is behind another project of the business is recorded with `owns`.
- `operates` and `builds` are for a party that runs or builds something for its owner under a contract. A company that runs its own plant needs no such link. The supplier that builds a line the business depends on does.
- An asset is examined when repayment depends on it: answer `OBS_ASSET_007` for each plant. The checks on its condition are then asked, or fall away.
- Where the same people run two companies, record a fact about them once and let its answer count for both: one answer with `"for"` for each company.

A new link brings the checks that fit the role, and the checks on the link itself. Run `status --for <ID>` to see them.

### When the structure changes

- **A subject drops out.** A contract is cancelled, an asset is sold, a project is shelved, or a subject stood for something that is now recorded another way. End it: `{"subjects": [{"id": "C-002", "state": "ended"}]}`. It keeps its facts and its place in the log. It is asked nothing, its links stop counting, and the pages leave it out.
- **The borrower changes.** Record the new `borrows` link and end the old one. Then:
  1. Answer the checks about the deal again that turn on who borrows: `status --for DEAL` lists them, and `show <deal> facts <check>` shows the answer each has now.
  2. Decide whether `relies_on` still points at the right party or group. The perimeter is where the cash is earned, whoever signs.
  3. Look at the tie between the old and the new borrower. An owner whose company now borrows is asked what it owes and receives on its own account.
  4. `status` lists the answers that were recorded for the old borrower and that it is no longer asked. If it comes back in another role, as a guarantor for example, they count again. If it does not, withdraw them. The facts stay. Move an answer to the new borrower with `"for"` only where the fact is about the new borrower as well.
- **A party gets another role.** Add or end the link. The record of the party stays one record.
- **The borrower is open.** End the old `borrows` link and give the role to a party without a name. Where it will be one of the companies of the group, make it a `member_of` the group, so that the business is not examined a second time. Say in a decision which companies it could be, and which answers to put back once it is named.
- **The purpose changes.** End the `finances` link when the loan no longer pays for that project, or add one when it does. Answer `OBS_REQUEST_001`, `OBS_REQUEST_003` and `OBS_USE_001` again. The project keeps its facts and its page.

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
- Where the documents do not say which company of a group owes a loan, link the lender to the group and say so in the `why`. One link for a lender is enough, unless its loans to two companies differ in security or ranking: each link brings the checks on another lender. Where one borrower is the parent and the other its subsidiary, their place in the group is a difference in ranking (see the note of `OBS_LENDER_001`): give each loan its link, or keep one link, answer for the worse of the two and say so in the `why`.
- The link brings the checks on another lender: who ranks ahead, what it holds, what lets it call its loan.

### A person

A natural person is a subject of the kind `person`. A person is asked only what fits a person: sanctions, political exposure, integrity, source of funds, disputes, and the capacity to pay where the person guarantees the loan under review. Record a person who owns, controls or guarantees. Directors and managers who do none of these stay as facts about their company. A person who was recorded as a party is changed in place: send the subject's `id` with `"kind": "person"`. The ID keeps its letter.

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
                "rests_on": ["F-021"], "by": "analyst", "covers": ["OBS_GUARANTEE_MIT_001"],
                "owner": "analyst", "due": "2027-01-31"}],
 "questions": [{"asked_of": "CFO of Cedar Foods", "text": "Please send the supply contracts.",
                "about": "P-001", "asked": "2026-11-12", "via": "S-003", "checks": ["OBS_INPUT_MIT_001"]}]}
```

**A decision** needs a `decision` and a `reason`, and should name what it rests on: facts, or a source such as the analyst's note. A decision that no longer holds is changed in place: send its `id` with the new text. The log keeps what it said before. A decision that `covers` checks takes them off the list of checks to answer.

- With an `owner` and a `due` date it is a gap with an agreed action: a condition, a covenant or a task. `status` lists it as such.
- Without them it settles the matter, for the subject it names in `about`. That is how you record that an answer calls for nothing more in the structure, and why. On a check that is not answered, it takes the check off for that subject: see [standard](standard.md).

**A question** is recorded as soon as it is worth asking, so that every question lives in one place and a page can cite it. It needs `asked_of` and `text`. Without a date it is a draft, and `status` says "not sent yet". Give it the date it was `asked` only when it has gone out, with the source it went out `via` if there is one. Name the `checks` its answer would close: a question that names no check moves nothing when it is answered. When it is answered, change it: `{"id": "Q-001", "state": "answered", "answered_by": ["F-020"]}`. A question that will not be sent is `withdrawn`.
