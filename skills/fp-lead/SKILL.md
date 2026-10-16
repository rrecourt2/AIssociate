---
name: fp-lead
description: Prepare or revise a whole financing proposal (FP), integrate specialist reviews and officer edits, or draft Credit replies. Own the financing argument, writing and delivery.
---

# FP Lead

Apply [operating rules](../../shared/operating-rules.md), [writing guidance](../../shared/writing.md) and the [evidence workflow](../../shared/workflow-contract.md). Use [fp.py](../../tools/fp.py), with [release metadata](../../.claude-plugin/plugin.json), and processors [register.py](../../tools/register.py), [fp_docx.py](../../tools/fp_docx.py) and [fin_table.py](../../tools/fin_table.py); execute without reading their whole implementation.

## Prepare

Start from the saved purpose, evidence and coverage. Commission bounded updates or specialist work where needed; reconcile findings before drafting. Skills are methods, not a requirement for eight agents or repeated archive reviews.

Retrieve the current Word, matching record if assistant-written, separate template and approved examples. Confirm their exact files, evidence revision, decision/recommendation, audience, annex questions and output location; reuse settled choices. Run `python3 scripts/fp.py --version` and retain its version/hashes.

Run `python3 scripts/fp.py prepare FOLDER prepare.json`, then `python3 scripts/fp.py status FOLDER`:

```json
{
  "op_id": "prepare-01", "base_revision": 2, "deal": "example",
  "base": "/work/partial.docx", "template": "/work/template.docx",
  "examples": ["/work/approved-example.docx"],
  "output_dir": "/work/deal/output", "mode": "existing",
  "provenance": "Officer authorised improving this genuine imported draft"
}
```

| Mode | Use |
|---|---|
| `existing` | Authorised first import of a genuine draft; revise a new copy |
| `first` | Base is the configured blank template itself |
| `normal` | Current assistant Word and matching `.sections.json`; protect officer edits |

For Save As, use `fp_docx.py find-record CURRENT.docx` and pass a confirmed `record` in prepare. Missing records do not prove a first draft; similar legacy records are only candidates. Embedded identity prevents resetting protection. Ask when provenance is unclear.

Prepare records input hashes and inspects structure; it does not read examples. Before drafting, the separate Template and Style Reviewer reads the template/examples and records required content, permitted deviations and the primary example's voice/density in Analysis key `preflight`. Set `run.preflight.editorial` to `complete` through a register update. A `run.set` replaces the whole object: retain its other fields.

## Write and build

Plan the whole financing argument and annex conclusions without a sample-section approval gate. Use selected claims, calculations and adopted analysis; keep decision-changing uncertainty in the FP and internal workplans in Analysis. Continue supported drafting through gaps. Required reading, pending impacts, blockers and rechecks prevent clean readiness.

Inspect the current Word with `fp_docx.py inspect CURRENT.docx --markdown` and JSON inspection. Draft Markdown uses `## section-id`, paragraphs, bullets, tables and `**bold**`. `{{keep:N}}` positions fixed content; do not duplicate it. Located tags such as `[S-012 p.45]` are removed from Word and source IDs retained in its record; deliver the located draft too.

Run `python3 scripts/fp.py build FOLDER build.json`:

```json
{
  "op_id": "build-01", "base_revision": 4,
  "content": "/work/deal/draft.md", "out": "FP-v01.docx",
  "protect": ["recommendation"], "support": ["/work/deal/financial-table.json"]
}
```

Build requires saved located claims and preflight. Optional `fields` holds expressly authorised cover replacements; `protect` and `support` are optional. Use a new output name. Officer edits, comments, tracked changes and fixed content remain protected; unapplied replacements go to `.proposals.md`.

Word/record share deal/build IDs. Follow reported retry instructions after interrupted publication or register failure; retain published files. Never bypass refusal through blank reconstruction. Absent headings and predefined-table population are unsupported. Explicitly protect deliberate edits to ignored Word save-noise properties. `built` does not mean ready.

For figures, use `fin_table.py SPREAD.xlsx MAPPING.json --json TABLE.json`. Mapping requires `unit` and `identity` entries for `entity`, `perimeter` and `unit`, each with `value` and selected-sheet `cell` or reviewed external `basis`/`reviewed_by`. Unit labels must agree; no conversion is inferred. Preserve hashes, cells and formulas. Do not enable cached formulas to bypass a refusal.

## Review and deliver

Follow the [review protocol](../../shared/review-protocol.md), rewriting adopted findings and rechecking affected conclusions. Obtain separate style/layout review of the actual Word against examples. Reconcile body, tables and annexes; report resolved gaps, outstanding evidence and officer decisions. Mechanical checks cannot certify house style, mandatory table content or investment judgment.

Run `fp.py bundle FOLDER --out DELIVERY`. It includes Word/record, register/views, client `DDQ.md`, located draft/support, proposals and a hash manifest. This internal bundle is local-only; upload through authorised host tools and reopen saved bytes before claiming persistence. Report file links, applied/unapplied changes and unperformed checks. If Python/access fails, return labelled proposals and the missing handoff.

The officer decides readiness against the current Word hash and evidence revision; record submission exceptions separately. For Credit follow-up, retain the actual question, draft a direct supported answer and revise affected passages. Communications remain drafts.
