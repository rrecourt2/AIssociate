# Recording

Hand `add` one JSON object: a set of changes. The tool applies all of it or none of it.

```json
{
 "by": "assistant", "note": "Read the 2025 annual report", "op": "annual-report-2025",
 "sources": [{"ref": "ar", "title": "Audited financial statements 2025", "kind": "audited_annual_report", "date": "2026-03-28",
              "where": "Client folder/AR 2025.pdf", "extract": "Internal/sources/extracts/AR 2025.txt", "page_offset": 2,
              "about": ["P-001"], "read": "part",
              "map": [{"at": "note 5", "topic": "revenue and customers", "gist": "Two customers above 10%."}]}],
 "subjects": [{"ref": "bluegate", "kind": "party", "name": "Bluegate Supermarkets"}],
 "links": [{"ref": "sale", "from": "P-001", "type": "sells_to", "to": "@bluegate", "state": "confirmed", "source": "@ar",
            "why": "Bluegate buys 31% of revenue, so whether it pays matters for repayment."}],
 "facts": [{"ref": "rev", "about": "P-001", "statement": "Revenue was KES 4,060m in 2025.", "label": "Revenue",
            "value": 4060, "unit": "KES m", "as_of": "2025-12-31", "source": "@ar", "place": "page 22, note 5",
            "quote": "Revenue 4,060 3,720", "said_by": "document",
            "answers": [{"check": "OBS_REV_001", "value": true}], "replaces": "F-005"}]
}
```

- **A new record has no `id`.** Give each a `ref`, and point at it from the same set as `"@ar"`. `add` prints `@ar -> S-002`: that is the ID to cite. Do not work IDs out by counting.
- **A record with an `id` is a change**, also to correct a mistake. Send only the fields that change. A field you send replaces the old one, a whole `answers` list or `map` included. `null` clears a field.
- **`op`** names the set. A set with the same `op` is not applied twice, whatever it holds: give each set a name of its own.
- **`base`**, optional, is the revision you last saw. The tool refuses the set if the record has moved on.
- **`deal`** changes the deal itself: `{"deal": {"stage": "concept"}}`.
- **`--try`** prints what `add` would print and writes nothing. Use it before every large set: it tests the quotations of the set against the text of their sources, which `add` does too, and names a link or a subject that an answer calls for.

Where an answer does not count, `add` prints a `Note:` and records it all the same: the check is not asked about that subject, or is not relevant there. A check that waits may be answered in the same set as the answer that opens it. Look at the check with `show`, then move the answer with `"for"` or withdraw it. `status` lists such answers until you do. The same goes for a decision that `covers` a check for a subject it is not asked of: it settles nothing until its `about` names the right one.

## Sources

One per document, call, email or note. `title` and `kind` are required.

- `kind`: a kind of source, from `show kinds`. It decides the folder the document is filed in and how strong its evidence counts. See [standard](standard.md).
- `where`: the path of the original in the deal folder.
- `extract`: the path of a text extract of the original, if there is one.
- `page_offset`: the page of the PDF less the page number printed on it. See "Quotations and places".
- `date`, `about`, `sent_by`: the date the document bears or was published, or the date of the call, not the day you saved it and not the day a file was made; the subjects it is about; who it came from.
- `read`: `full`, `part` or `none`, `extract` when you read the extract and not the original, or a few words for a scan (below). The pages that cite the source say so.
- `map`: where things are, as `at` (page, note, minute), `topic` and `gist`. Add entries for the parts you may need again.
- `note`: anything else. For what the analyst said: their words.
- `replaces`: the source that this one replaces.

**What the analyst tells you** about the opportunity is a source of kind `analyst_note`. It needs no file. Mark its facts `said_by: analyst`:

```json
{"sources": [{"ref": "steer", "title": "Analyst, in conversation", "kind": "analyst_note", "date": "2026-11-12",
              "note": "We might finance the second UHT line."}]}
```

## Filing documents

`file` moves documents to their place. It records nothing: it prints a source record for each document, with its `where` and its `extract`, to put into the next `add` with the date, what was read and a note. `status` lists what was filed and is in no source, under "Documents filed and not recorded". It takes a list:

```json
[{"file": "Inbox/AR 2025.pdf", "kind": "audited_annual_report", "title": "Audited financial statements 2025",
  "party": "Cedar Foods Ltd", "period": "2025", "extract": "Inbox/AR 2025.txt"}]
```

- `file` is the path of the document in the deal folder, and `kind` a kind of source. The rest is optional.
- The kind decides the folder, and `show kinds` names it, with what each kind is for. What the company itself published counts as the client's, also when nothing has been shared yet. Where no kind fits, use `other`. A page of the company's website, a news release and a broker's research report are each a `public_source`; a sustainability report is filed as an `annual_report`, the company's report on its governance as `board_composition`, and a notice filed with an exchange or a regulator as a `regulatory_document`. A public document of a kind that has a place in the client folder, such as a law or a rating agency's report, may be filed as that kind and then counts as such evidence. Filed as a `public_source` it stays in `Internal/sources/` and counts as supporting at most. Most kinds go to `Client folder/<file name>`, which the tool lists in `Client folder/index.md`: also an email with the client (`correspondence`), and a screening or a report the lender ordered. A call, the analyst's note, a press article and a public source go to `Internal/sources/`. What must stay inside the deal team is an `internal_memo`, which goes there too.
- An `extract` goes to `Internal/sources/extracts/`. Give that path as `extract` on the source.
- The tool never overwrites. Where a name is taken, it refuses that document: give it a name of its own and file it again. A folder that filing left empty can be removed.

### Originals, extracts and scans

- **The original is the source**, and `where` names it. When you make an extract, keep the page numbers of the original and copy its tables in full.
- **Where the extract and the original differ, the original is right.** Correct the extract, and say so in the `note` of the source.
- **A PDF has no text to quote from.** Write its text to `Internal/sources/extracts/<name>.txt`, with the page numbers, and name that path as `extract` on the source.
- **When the original comes later**, point the source at it: send its `id` with the new `where`, and the old text as `extract`.
- **A scanned PDF cannot be searched.** A text of it read by machine may be filed as its extract. It finds the page, and it has reading errors. Read the page itself, as an image, before you record from it: render the page with what your host offers, and turn a page that is printed sideways. Write down what you read at once, because a host may not keep the image. Where the machine text is wrong on a page you read, correct that line in the extract, so that your quotation is found. Where it has lost a table, write the rows you read under the marker of that page, between a line `[read from the page]` and a line `[end]`. Say in `read` that the text was read by machine and which pages you read in the original: `"read": "machine text; pages 12 to 19 read in the original"`.

## Facts

Record what would go into a table or a system field: names, amounts, dates, terms, shares, commitments. What would go into a paragraph stays in the source, and the `map` says where. `about`, `statement` and `source` are required.

- `about`: a subject, a link, or `DEAL`. A figure from consolidated accounts is about the group, one from a company's own accounts about the company.
- `statement`: one plain sentence that can stand alone.
- `label`, `value`, `unit`: for a value that belongs in a table. Use the same label for the same figure at another date. Give a label only to a figure of the subject itself: a competitor's revenue or a market figure would show among the subject's key values. Competitors are facts about the party or the group whose market it is, not subjects.
- `as_of`: the date the fact refers to, such as the balance sheet date, not the date of the document. For an event, when it happened: `2015` or `2012-09` will do. A standing fact needs none: the date of its source counts.
- `source`, `place`: where it comes from, and the page, note or minute of the original.
- `quote`, `said_by`: the words of the source that carry the fact, and who says so (below).
- `answers`: the checks it answers, as `[{"check": "OBS_REV_001", "value": true}]`. Yes or no is `true` or `false`, a number is a number, a choice is one of the check's options, or a list of them where the check allows several. An answer counts for the subject the fact is about: add `"for": "G-001"` for another, and for two subjects give the check twice, each with its `for`. An answer to a check about the opportunity counts for the opportunity.
- `fills`: the system fields it fills, such as `["CRM.country"]`. A field the institution's layer does not list is refused.
- `nothing_found`: `true` for a search that found nothing. Say in the statement what was looked for, where, and what the search could not cover. A search is your own conclusion: mark it `inference`, name as `source` the document searched most fully, and the others in the statement. It answers a check only where the search covered the record that would show the thing, such as a register.
- `replaces`: one earlier fact that was not replaced before. The old one stays, marked `outdated`.
- `state`: `disputed` on each fact that is contested, such as the figures that two documents give for the same thing, and on a figure worked out from one of them. Each names the others in its statement: change a colleague's fact for that where needed. Where a weaker source, such as a paper, differs from a document, keep the document's fact current and mark only the other, naming the document's fact in it. Two figures on different definitions, such as designed capacity and output in a year, are two measures and no dispute: give each its definition. A fact that only reports the disagreement stays current.

### Who says so

- `document`: the figures and terms in accounts, contracts, registers and the tables of a prospectus.
- `client`: what a party to the deal says about itself, its plans or its prospects, also in its own prospectus, report or website, or through the press. A favourable answer on that alone is someone's own word.
- `analyst`: what the analyst told you.
- `third_party`: what a journalist, a researcher or an authority reports on their own account. A paper that retells a filed document is one too: record the document itself where it is in the folder.
- A filing with a regulator is `document` for what it reports as done, such as who holds which seat, and `client` for what the company declares about itself, such as that it has no litigation or that a director is independent.
- `inference`: what the document does not itself say: a conclusion, a figure you worked out, a borrower the note does not name. An answer that rests only on inferences never counts as the best evidence.

An admission against the speaker's own case is believed: "our margin fell in 2025". An explanation that blames an outside cause is not one: "it fell because milk prices rose in the drought". Record it as `client`.

### Quotations and places

- **Give every fact you take from a document a `quote`**: the few words that carry the fact, copied from the source's extract, or from the original where that is a .md, .txt or .html file. Capitals, the spacing between words, line breaks, Markdown marks, the bars of a table and the way a text spells an accented letter do not count. Every other character does, also a space that the machine text put inside a number: correct that line in the extract. For a figure, quote the phrase or the row that holds it. An inference has none, and nor has a fact from a source without a text, such as what the analyst told you.
- **`add` and `check` report** a quotation that is not in the text of its source, and a source that facts quote and that has no text to check against.
- **`place` names the page**, and the browser view opens the original there. Where the printed page numbers differ from the pages of the PDF, set `page_offset` on the source and cite the printed page: `"place": "page 19"`. A place that says `PDF p.21` is taken as it stands.

### Tables, worked figures and readings

- **From a table**, record each row you use as a fact of its own, with all its columns. A total that the table does not print is your inference.
- **A figure you worked out**, such as a ratio or a sum, is a fact of its own. Mark it `inference`, show the working and name the facts: "Borrowings were 0.32 times revenue in 2025: KES 1,300m (F-011) over KES 4,060m (F-008)." Name a fact of the same set by its `ref`: `(@rev)` becomes its ID, also in a `why`, a `reason` and a `decision`.
- **A fact names one source.** A comparison between two documents is an inference that names a fact from each.
- **An amount in an answer** is given in the unit of its fact, which the statement names.
- **A reading of several facts is not a fact.** It goes on a page.

### Changing, replacing and withdrawing

- **A fact was wrong or left something out, a plan moved on, or a better source gives the figure.** Record the new fact with `replaces`, and carry over the answers that still hold: the answers of an outdated fact no longer count.
- **A balance at a later date replaces nothing.** Record it as a new fact with the same `label` and its own `as_of`. Both stay current, and the later one answers the check. In the same way 2025 does not replace 2024, and an unaudited quarter does not replace an audited year.
- **Withdraw an answer** by sending the fact with the answers that remain: `{"facts": [{"id": "F-012", "answers": []}]}`. The fact stays.
- **The wrong subject, or a slip that changes no figure**, is corrected in place, with the fact's `id`.
- **A fact should not have been recorded**, such as an instruction on how to write. Send its `id` with `"state": "outdated"`, say why in the `note` of the set, and take its citations off the pages.
- **A source was withdrawn or reissued.** Record the new source with `replaces`. The old one stays, marked `replaced`, and `status` lists the facts that still rest on it.

### Wordings to avoid

When the analyst says that something is not to be said, set it on the deal: `{"deal": {"avoid": ["loan new line"]}}`. Each entry is a few words. The list you send replaces the old one, which `status` prints as "Wordings to avoid": send its entries again with the new one. `check` reports a sentence, a page title or a heading, on a page or in a draft, that holds all the words of one entry, as whole words, in any order. A plural is another word, and a sentence that denies the thing is reported like one that says it. The working notes are exempt.

## Subjects and links

A subject is a party, a person, a facility, a contract, an asset, a project or a group. A link says how two subjects relate, and gives the role: whoever `borrows` is the borrower. `show kinds` says what each kind of link is for and where it counts. Read it before you choose one.

- A subject needs a `kind`. Leave `name` empty for a role nobody holds yet, and say what is known in `note`.
- A link needs `from`, `type` and `to`, and a `why`: why it matters for repayment. It starts as `proposed`. Set `state` to `confirmed` when a source confirms it, and to `ended` when it no longer holds. A link that is your inference stays `proposed`: say so in its `why`, and name the fact it rests on.
- A new link brings the checks that fit the role, and the checks on the link itself. `status --for <ID>` shows them.
- **A facility** is a loan that the lender is considering, and nothing else. `borrows`, `guarantees`, `supports` and `secures` count only when they point at one, and `status` says so where a link does not count.
- **A person** is a subject of the kind `person`. Record a person who owns, controls or guarantees. Directors and managers who do none of these stay as facts about their company. A person who was recorded as a party is changed in place: send the `id` with `"kind": "person"`. Any kind is changed this way, and the ID keeps its letter.
- **An asset** is examined when repayment depends on it: answer `OBS_ASSET_007` for each plant. The checks on its condition are then asked, or fall away.
- **A part of an asset**, such as a line or a machine inside a plant, is an asset with a `part_of` link to the plant. It is asked no checks: it is examined with the whole. It gets a page under `assets/` if it deserves one. Leave the link out, and say in the `note` what it belongs to, only where it has to be examined apart: it is security by itself, or it is leased.
- **What the loan pays for.** Record a project or an asset that can be named, and link the facility to it: `{"from": "L-001", "type": "finances", "to": "J-001"}`. The checks on a project are asked only of a project the loan finances. Another project of the business may be a subject with a page and facts, without that link.

### The perimeter

Link the facility to the party or the group whose cash repays the loan: `{"from": "L-001", "type": "relies_on", "to": "G-001"}`. The business and its money are examined once, there. A company that is a `member_of` the group is asked only what belongs to a legal entity: its owners, its integrity, its board, its legal standing. So an answer on revenue, cash flow, debt, currency or related parties goes to the group, and an answer on owners or the board to the company. A customer's `sells_to` link and a supplier's `supplies_to` link run from or to the group as well: the checks on customers and suppliers are asked there. If you add the group later, `status` lists the answers that no longer count. Move each with `"for": "G-001"`.

### Debt that already exists

Existing debt is never a facility. Record the lender as a party and link it to the company that owes the debt: `{"from": "@bank", "type": "lends_to", "to": "P-001"}`. The terms, the security and the guarantors of that debt are facts about the link, never a `guarantees` or `secures` link.

- For a bond, the lender is its holders: a party named "Holders of the 2025 bond".
- Give a link to each lender that matters for ranking, security or refinancing: each link brings the checks on another lender. The others stay in a fact about total debt. Say in a decision which lenders got no link and why.
- Where the documents do not say which company of a group owes a loan, link the lender to the group and say so in the `why`.
- One link for a lender is enough, unless its loans to two companies differ in security or ranking, as loans to a parent and to its subsidiary do. Then give each loan its link. Where the statements give one balance for the bank, link it to the group.

### When the structure changes

- **A subject drops out**: a contract is cancelled, an asset sold, a project shelved. End it: `{"subjects": [{"id": "C-002", "state": "ended"}]}`. It keeps its facts. It is asked nothing, its links stop counting, and the pages leave it out.
- **The borrower changes.** Record the new `borrows` link and end the old one. Answer again the checks about the opportunity that turn on who borrows: `status --for DEAL` lists them. Decide whether `relies_on` still points at where the cash is earned, whoever signs, and look at the tie between the old and the new borrower. `status` lists the answers that the old borrower is no longer asked: withdraw them, unless it comes back in another role. Move an answer to the new borrower with `"for"` only where the fact is about the new borrower as well.
- **The borrower is open.** End the old `borrows` link and give the role to a party without a name. Where it will be a company of the group, make it a `member_of` the group, so that the business is not examined twice. Say in a decision which companies it could be, and which answers to put back once it is named.
- **The purpose changes.** End or add the `finances` link, and answer `OBS_REQUEST_001`, `OBS_REQUEST_003` and `OBS_USE_001` again. The project keeps its facts and its page.

## Decisions and questions

```json
{"decisions": [{"about": "R-002", "decision": "The guarantee is to be backed by a standby letter of credit.",
                "reason": "The guarantor pays only after enforcement against the borrower.",
                "rests_on": ["F-021"], "by": "analyst", "covers": ["OBS_GUARANTEE_MIT_001"],
                "owner": "analyst", "due": "2027-01-31"}],
 "questions": [{"asked_of": "CFO of Cedar Foods", "text": "Please send the supply contracts.",
                "about": "P-001", "asked": "2026-11-12", "via": "S-003", "checks": ["OBS_INPUT_MIT_001"]}]}
```

**A decision** needs a `decision` and a `reason`, and names in `rests_on` the facts or the source it rests on. Use one to say why something is left out, such as a customer that gets no page. One that `covers` checks takes them off the list of checks to answer: with an `owner` and a `due` date as a gap with an agreed action, without them as settled for the subject it names in `about`. Name there the subject or the link the check is asked of. See [standard](standard.md).

**A question** needs `asked_of` and `text`. Record it as soon as it is worth asking, so that a page can cite it, and name the `checks` its answer would close. Without a date it is a draft. Give it the date it was `asked` only when it has gone out, with the source it went out `via`. When it is answered: `{"id": "Q-001", "state": "answered", "answered_by": ["F-020"]}`. A question that will not be sent is `withdrawn`.
