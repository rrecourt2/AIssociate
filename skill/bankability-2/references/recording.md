# Recording

You record by handing `add` one JSON object: a set of changes. The tool applies all of it or none of it.

```json
{
 "by": "assistant",
 "note": "Read the 2025 annual report",
 "op": "annual-report-2025",
 "sources": [{"ref": "ar", "title": "Annual report 2025", "kind": "audited_annual_report", "date": "2026-03-28",
              "where": "Client folder/03 Financial Information/03.01 Historical Financials/AR 2025.pdf",
              "about": ["P-001"], "read": "part",
              "map": [{"at": "note 5", "topic": "revenue and customers", "gist": "Two customers above 10%."}]}],
 "subjects": [{"ref": "tuskway", "kind": "party", "name": "Tuskway Supermarkets"}],
 "links": [{"from": "P-001", "type": "sells_to", "to": "@tuskway", "state": "confirmed", "source": "@ar",
            "why": "Tuskway buys 31% of revenue, so whether it pays matters for repayment."}],
 "facts": [{"about": "P-001", "statement": "Revenue was KES 4,060m in 2025.", "label": "Revenue",
            "value": 4060, "unit": "KES m", "as_of": "2025-12-31", "source": "@ar", "place": "note 5",
            "said_by": "document", "answers": [{"check": "OBS_REV_001", "value": true}], "replaces": "F-005"}]
}
```

- **A new record has no `id`.** The tool gives it one. Give it a `ref` to point at it from the same set: `"@ar"`.
- **A record with an `id` is a change** to that record. Send only the fields that change.
- **`op`** is any name for this set. A set with the same `op` is not applied twice. Use it.
- **`base`** is optional: the revision you last saw. The tool refuses the set if the memory has moved on.
- **`deal`** changes the deal itself: `{"deal": {"stage": "concept"}}`.

## Sources

One per document, call, email or note. `title` and `kind` are required.

| Field | Meaning |
|---|---|
| `kind` | A kind of source from the standard, such as `audited_annual_report`, `call`, `correspondence`, `officer_note`. A wrong kind is refused with the list of kinds. |
| `where` | The file's path in the deal folder. The tool adds its fingerprint. |
| `date` | The date of the document or the call. |
| `about` | The subjects it is about. |
| `read` | `full`, `part` or `none`. |
| `map` | Where things are: `at` (page, note, minute), `topic`, `gist`. Add entries for the parts you may need again. |
| `sent_by` | Who it came from. |

## Facts

Record what would go into a table or a system field: names, amounts, dates, terms, shares, commitments. What would go into a paragraph stays in the source, and the `map` says where. `about`, `statement` and `source` are required.

| Field | Meaning |
|---|---|
| `about` | A subject, a link, or `DEAL`. |
| `statement` | One plain sentence that can stand alone. |
| `label`, `value`, `unit` | Give a label to a value that belongs in a table, such as `Revenue`. |
| `as_of` | The date the fact refers to. For a standing fact, the date of the source. |
| `source`, `place` | Where it comes from, and the page, note or minute. |
| `said_by` | `document`, `client`, `officer`, `third_party` or `inference`. Mark your own conclusions as `inference`. |
| `answers` | The checks it answers: `{"check": "OBS_REV_001", "value": true}`. Add `"for": "P-002"` if the answer is about another subject than the fact. Yes or no is `true` or `false`, a number is a number, a choice is one of the check's options. |
| `fills` | The system fields it fills, such as `["CRM.country"]`. |
| `nothing_found` | `true` for a search that found nothing. Say in the statement what was looked for and where. |
| `replaces` | The fact this one replaces. The old one stays, marked `outdated`. |
| `state` | Set `disputed` when the fact is contested. |

## Subjects and links

A subject is a party, a facility, a contract, an asset, a project or a group. A link says how two subjects relate, and gives the role: whoever `borrows` is the borrower.

- A subject needs a `kind`. Leave `name` empty for a role nobody holds yet, and say what is known in `note`.
- A link needs `from`, `type` and `to`. It starts as `proposed`. Set `state` to `confirmed` when a source confirms it, and to `ended` when it no longer holds.
- Give a link its `why`: why it matters for repayment.
- Kinds of link: `borrows`, `guarantees`, `sponsors`, `owns`, `controls`, `member_of`, `supplies_to`, `sells_to`, `lends_to`, `operates`, `builds`, `party_to`, `secures`, `ranks_behind`, `part_of`, `supports`, `completion_support`, `portfolio_support`, `other`.

A new link brings the checks that fit the role. Run `status` to see them.

## Decisions and questions

```json
{"decisions": [{"about": "P-001", "decision": "Lakeside Distributors gets no page and no checks of its own.",
                "reason": "It buys 14% of revenue and three other distributors serve the same region.",
                "rests_on": ["F-009", "F-015"], "by": "assistant"}],
 "questions": [{"asked_of": "CFO of Cedar Foods", "text": "Please send the supply contracts.",
                "about": "P-001", "asked": "2026-11-12", "via": "S-003", "checks": ["OBS_INPUT_006"]}]}
```

A decision needs a `decision` and a `reason`, and should name the facts it rests on. A question needs `asked_of` and `text`. When it is answered, change it: `{"id": "Q-001", "state": "answered", "answered_by": ["F-020"]}`.
