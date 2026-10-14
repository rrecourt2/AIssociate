# AIssociate workflow

Use the shipped Python 3.9+ scripts. Deal Analyst owns the evidence record; FP Lead uses `fp.py` to prepare Word and package outputs. Read the stage needed now. Commands run inside the installed skill in the host workspace, not automatically on the officer's computer. The stage owner gives the confirmations below in brief updates; ask only about missing inputs or material ambiguity, otherwise continue.

## 1. Organise and save evidence

Confirm the deal, source scope/cutoff and save location. Start here even when no FP or template exists. One task writes `register.json`; specialists return proposed changes against its revision. Generated views are `register.xlsx`, `Analysis.md` and `Client-DDQ.md`.

| Need | Command |
|---|---|
| Start | `python3 scripts/register.py init FOLDER --deal example` |
| Reopen the index | `python3 scripts/register.py show FOLDER` |
| Read selected records | `python3 scripts/register.py show FOLDER C-001 O-002` |
| Read a section | `python3 scripts/register.py show FOLDER --section summary` |
| Apply changes | `python3 scripts/register.py apply FOLDER changes.json` |
| Open work / client questions | `python3 scripts/register.py lists FOLDER` / `ddq FOLDER` |
| Restore views / upgrade an old register | `python3 scripts/register.py refresh FOLDER` / `migrate FOLDER` |

A change request has `base_revision`, unique `op_id`, `actor`, `summary` and `changes`. Changes use `{"sheet":"claims","add":{...}}`, `{"sheet":"claims","update":"C-001","set":{...}}` or `{"sheet":"control","set":{...}}`. Table fields are strings; omit unavailable values. Read the relevant `TABLES`/`ALLOWED` definitions for fields. Retry unchanged requests with their original ID; reconcile stale revisions. Migration keeps a backup and history.

Keep the record proportionate:

- **Sources:** original cloud reference, version/hash, entity/period, coverage, reviewed scope and extract path. Reuse unchanged evidence within its reviewed scope. New versions get a new ID and `supersedes`; linked work reopens. Assess unlinked adverse evidence too.
- **Claims:** material assertion, kind, entity/period, located sources, support, qualifications and section links. Figures add value, unit and definition; calculations add method and located inputs. Keep management attribution and conflicting evidence.
- **Analysis:** reasoning, strategy, linked claims/sources and internal actions. Clear rechecks only after assessing the changed evidence. Check whether historical issues still apply before opening current work.
- **Open items:** purpose, evidence needed, owner and explicit audience: `client`, `internal`, `restricted` or `unknown`. Only client-facing open/promised requests enter the DDQ. Received answers need assessment; closure requires an assessor, rationale and located evidence or an attributed officer decision.

Have FP Lead save an evidence-only delivery with `python3 scripts/fp.py bundle FOLDER --out DELIVERY`. No Word preparation is needed. Upload through the host, then reopen the index and follow a claim to its source in a fresh task. Bundles contain the register/views; they do not automatically copy source documents or extracts. Preserve authorised extract caches separately, or retrieve originals through their saved references. Local revision checks are not cloud locks.

## 2. Prepare the paper

Retrieve the current Word, matching record if assistant-written, separate template and approved examples. Run `python3 scripts/fp.py --version` and retain its version/hashes. Prepare with real local paths and the register's current revision:

```sh
python3 scripts/fp.py prepare FOLDER prepare.json
python3 scripts/fp.py status FOLDER
```

```json
{
  "op_id": "prepare-01", "base_revision": 2, "deal": "example",
  "base": "/work/partial.docx", "template": "/work/template.docx",
  "examples": ["/work/approved-example.docx"],
  "output_dir": "/work/deal/output", "mode": "existing",
  "provenance": "Officer authorised improving this genuine imported draft"
}
```

Prepare inspects structure and records input hashes. It does not read the examples or complete editorial preflight. Before drafting, the template/style reviewer reads them and records required headings, fields, tables and wording, permitted deviations, and one primary example's voice and density. Save this in Analysis key `preflight`, then set `run.preflight.editorial` to `complete` through a register update. **A `run.set` replaces the whole object:** retain its other fields.

FP Lead confirms the exact base FP, template and primary example with file links, the saved evidence revision, intended recommendation and output/annex scope. State material gaps or deviations; reuse settled choices on later rounds.

| Mode | Use |
|---|---|
| `existing` | Authorised first import of a genuine draft; revise a new copy |
| `first` | Base is the configured blank template itself |
| `normal` | Current assistant Word and its matching `.sections.json`; protect officer edits |

Missing records do not prove a first draft. For Save As, use `fp_docx.py find-record CURRENT.docx` and pass a confirmed `record` in prepare. Similar legacy records are candidates, not authority. Embedded identity prevents resetting protection. Ask only when provenance is unclear.

## 3. Write and build

Use selected evidence, the whole-paper plan and shared writing/review guidance. Keep decision-relevant uncertainty in the FP and internal workplans in Analysis. Continue supported drafting through gaps; required reading, pending impacts, blockers and rechecks prevent clean readiness. A proposed condition is not an existing protection.

Inspect the current Word with `fp_docx.py inspect CURRENT.docx --markdown` and JSON inspection. Draft Markdown uses `## section-id`, paragraphs, bullets, tables and `**bold**`. `{{keep:N}}` positions fixed content; do not repeat it. Located tags such as `[S-012 p.45]` are removed from Word and source IDs retained in its record; deliver the located draft too.

```sh
python3 scripts/fp.py build FOLDER build.json
```

```json
{
  "op_id": "build-01", "base_revision": 4,
  "content": "/work/deal/draft.md", "out": "FP-v01.docx",
  "protect": ["recommendation"], "support": ["/work/deal/financial-table.json"]
}
```

Build requires saved located claims and recorded preflight. `protect` and `support` are optional; optional `fields` holds expressly authorised cover-field replacements. Use a new output name. The writer preserves officer edits, comments, tracked changes and fixed content; unapplied replacements go to `.proposals.md`.

Word/record share deal/build IDs. Follow the reported retry instructions after interrupted publication or register failure; keep published files. Never bypass refusal through blank reconstruction. Absent headings and predefined-table population are unsupported. Explicitly protect deliberate edits only to ignored Word save-noise properties. `built` means supported operations succeeded, not that the FP is ready.

For figures, use `fin_table.py SPREAD.xlsx MAPPING.json --json TABLE.json`. Mapping requires `unit` and `identity` entries for `entity`, `perimeter` and `unit`, each with `value` and a matching selected-sheet `cell` or reviewed external `basis`/`reviewed_by`. Unit labels must agree; no conversion is inferred. Preserve workbook hashes, cells and formulas. Do not enable cached formulas merely to bypass a refusal.

## 4. Deliver and verify

Run `fp.py bundle FOLDER --out DELIVERY` again for the paper. It includes Word/record, register/views, client `DDQ.md`, located draft/support, proposals and a hash manifest. The bundle is internal and **local-only**. Host tools handle authorised upload; reopen saved bytes before claiming persistence. No email or storage connector is provided. If access or Python fails, return labelled proposals and the missing handoff.

Review the whole FP against the examples and inspect actual Word layout. Record the officer's readiness decision against the current Word hash and evidence revision. Mechanical checks cannot certify house style, mandatory table content or investment judgment. Confirm delivery with links to the verified saved files, applied/unapplied changes, unperformed checks and open decisions. Communications remain drafts.
