---
name: fp-lead
description: Draft or revise opportunity scans, Clearance in Principle documents, Term Sheets, contracting proposals, Financial Proposals, external Investment Memoranda or Credit replies. Integrate evidence and reviews for the intended audience.
---

# Document Lead

Invoked as `fp-lead`. Reuse the deal record for the requested document.

Apply [operating rules](../../shared/operating-rules.md), [writing guidance](../../shared/writing.md) and the [evidence workflow](../../shared/workflow-contract.md). Use [fp.py](../../tools/fp.py), with [release metadata](../../.claude-plugin/plugin.json), and processors [register.py](../../tools/register.py), [fp_docx.py](../../tools/fp_docx.py) and [fin_table.py](../../tools/fin_table.py); execute without reading their whole implementation.

## Prepare

Follow the Investment Officer's brief; ask only where consequential details are unclear. For an external memorandum, use the stated client/adviser/institution perspective and cleared information. Commission relevant updates and reconcile findings before drafting.

Choose the route before drafting: local Word needs a base, template and approved example; otherwise provide labelled content/proposals and missing calibration. Use tracked review for negotiated text. Record `python3 scripts/fp.py --version` and its hashes.

## Tracked review: Term Sheets and contracting

Follow the supplied template and precedents. Distinguish proposed, agreed and executed terms; flag departures and legal questions for Investment Officer instruction and specialist clearance.

Use a capable host Word tool for **Track Changes** in a new version and anchored **comments** for questions/rationale. Preserve existing revisions, threads, authorship and negotiated text; do not accept/reject or resolve them without instruction. Reopen the saved file to verify tracked edits and comment anchors; report the version and open points.

The packaged writer preserves revisions/comments but cannot create them. If the host cannot create and verify them, return clause-located original/proposed wording and comment text; state that tracked editing was not performed. Never substitute an untracked rewrite. Specialists and signatories retain legal clearance and execution.

## Protected local Word route

Retrieve the current Word, matching record if assistant-written, template and examples. Confirm exact files, evidence revision, required annexes and output location. Retain prior documents and their records when changing the current build.

Run `python3 scripts/fp.py prepare FOLDER prepare.json`, then `python3 scripts/fp.py status FOLDER`:

```json
{
  "op_id": "prepare-01", "base_revision": 2, "deal": "example",
  "base": "/work/partial.docx", "template": "/work/template.docx",
  "examples": ["/work/approved-example.docx"],
  "output_dir": "/work/deal/output", "mode": "existing",
  "provenance": "Investment Officer authorised improving this genuine imported draft"
}
```

| Mode | Use |
|---|---|
| `existing` | Authorised first import of a genuine draft; revise a new copy |
| `first` | Base is the configured blank template itself |
| `normal` | Current assistant Word and matching `.sections.json`; protect Investment Officer edits |

For Save As, use `fp_docx.py find-record CURRENT.docx` and pass a confirmed `record` in prepare. Missing records do not prove a first draft; similar legacy records are only candidates. Embedded identity prevents resetting protection. Ask when provenance is unclear.

Prepare records input hashes and inspects structure; it does not read examples. Before drafting, the separate Template and Style Reviewer reads the template/examples and records required content, permitted deviations and the primary example's voice/density in Analysis key `preflight`. Set `run.preflight.editorial` to `complete` through a register update. A `run.set` replaces the whole object: retain its other fields.

## Write and build

Plan the whole requested document without a sample-section approval gate. Use selected claims, calculations and adopted analysis; keep decision-changing uncertainty visible and internal workplans in Analysis. Continue supported drafting through gaps without claiming they are resolved.

Inspect the current Word with `fp_docx.py inspect CURRENT.docx --markdown` and JSON inspection. Draft Markdown uses `## section-id`, paragraphs, bullets, tables and `**bold**`. `{{keep:N}}` positions fixed content; do not duplicate it. Located tags such as `[S-012 p.45]` are removed from Word and source IDs retained in its record; deliver the located draft too.

Run `python3 scripts/fp.py build FOLDER build.json`:

```json
{
  "op_id": "build-01", "base_revision": 4,
  "content": "/work/deal/draft.md", "out": "Document-v01.docx",
  "protect": ["recommendation"], "support": ["/work/deal/financial-table.json"]
}
```

Build requires saved located claims and preflight. Optional `fields` holds expressly authorised cover replacements; `protect` and `support` are optional. Use a new output name. Investment Officer edits, comments, tracked changes and fixed content remain protected; unapplied replacements go to `.proposals.md`.

Word/record share deal/build IDs. Follow reported retry instructions after interrupted publication or register failure; retain published files. Never bypass refusal through blank reconstruction. Absent headings and predefined-table population are unsupported. Explicitly protect deliberate edits to ignored Word save-noise properties. `built` does not mean ready.

For figures, use `fin_table.py SPREAD.xlsx MAPPING.json --json TABLE.json`. Mapping requires `unit` and `identity` entries for `entity`, `perimeter` and `unit`, each with `value` and selected-sheet `cell` or reviewed external `basis`/`reviewed_by`. Unit labels must agree; no conversion is inferred. Preserve hashes, cells and formulas. Do not enable cached formulas to bypass a refusal.

## Review and deliver

Follow the [review protocol](../../shared/review-protocol.md). Obtain separate style/layout review against the applicable template/examples, including revisions/comments when used. Report resolved gaps, outstanding evidence and Investment Officer decisions. Mechanical checks cannot certify house style, mandatory content or legal/investment judgment.

For a local build, run `fp.py bundle FOLDER --out DELIVERY` to collect its Word/record, evidence views, located draft/support, proposals and manifest. For host-tracked edits, save and reopen the exact reviewed document separately with register/Analysis; record its link/version in `timeline`. Do not bundle a previous local build as the host result or fabricate a sidecar. Use authorised host tools and verify saved outputs before claiming persistence. Return links, unapplied proposals and unperformed checks.

Record readiness for the exact document/evidence revision; it is not approval or permission to circulate. Keep internal bundles separate from external copies. For Credit follow-up, retain the actual question and revise affected passages. Communications remain drafts.
