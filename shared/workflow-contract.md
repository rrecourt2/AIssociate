# Evidence workflow

The register is `register.json` in one approved deal folder; `Analysis.md` is its readable view. The scripts are in this skill's `scripts/` folder and need Python 3.9+; they work on a local copy. To resume, copy the saved `register.json` into a local working folder first. After changes, save `register.json` and `Analysis.md` back to the same approved location.

## Start or resume

Confirm the purpose, the relevant source scope and cutoff, and the save location; reuse choices already recorded. You can start without a template, a borrower or a chosen financing structure. Read the saved brief and coverage before retrieving more evidence.

| Need | Command |
|---|---|
| Start | `python3 scripts/register.py init FOLDER --deal example` |
| Resume | `python3 scripts/register.py summary FOLDER`, then `show FOLDER` |
| Selected records or a document section | `show FOLDER C-001 O-002` or `show FOLDER --section summary` |
| Apply changes | `python3 scripts/register.py apply FOLDER changes.json` |
| Open work, client questions | `lists FOLDER`, `ddq FOLDER` |
| Regenerate Analysis.md | `refresh FOLDER` |

A change request has `base_revision`, a unique `op_id`, `actor`, `summary` and `changes`. A change is `{"sheet":"claims","add":{...}}`, `{"sheet":"claims","update":"C-001","set":{...}}` or `{"sheet":"control","set":{...}}`. Field values are strings; omit unknown values. Field names and allowed values are in `TABLES` and `ALLOWED` at the top of register.py. If a save is interrupted, retry the unchanged request with the same `op_id`; if the register has moved on, re-read it and send a new request against its current revision.

## Keep useful memory

- **Brief:** Analysis key `strategy` holds the purpose, document or stage, author perspective, audience, length and next decision. Keep hypotheses apart from Investment Officer instructions and adopted decisions. Analysis key `timeline` holds dated decisions and their reasons, including rejected alternatives. Update both when intent changes.
- **Sources:** original link, version or hash, entity and period, reviewed scope, coverage and any reusable extract. A new version gets a new ID with `supersedes`; keep unaffected historical facts and obligations. Assess previously unlinked contrary evidence too.
- **Claims:** use `kind` to separate facts, assertions, assumptions, calculations and judgments; record entity, period, located sources and support. An assumption needs a basis and an adoption status, not a claim of verification. Figures add value, unit and definition; calculations add method and located inputs.
- **Analysis:** reasoning, linked claims and sources, and internal actions. Reconcile each specialist finding into the register or mark it unintegrated; temporary reviews are not deal memory.
- **Open items:** what needs verification, why, the evidence or action needed, the owner and the audience (`client`, `internal`, `restricted` or `unknown`). Link the affected claim or risk; distinguish missing knowledge from unread material. Before reopening a historical request or Credit concern, assess whether it is resolved, continuing, superseded or unclear; missing closure evidence alone does not make it current.

Link records by their IDs: `inputs` connects dependent claims, Analysis `claims` connects conclusions, and `fp_map` connects document sections. These links decide what is marked for recheck when evidence changes.

In `answer_source`, cite the located original sources and the claim IDs the assessment relies on; an open item's `link` alone does not trigger reassessment. Changed support reopens affected answers and blocks readiness; earlier assessments stay in the log. Closure needs an assessor, a rationale and current support, or an attributed Investment Officer exception. Receiving an answer or accepting uncertainty is not verification. A recheck need not repeat the client question.

## Answer and save

Stop when enough is known for the next decision. A small investigation needs a concise answer, a register update and the material follow-ups; use Document Lead only when a document is requested.

Cite original documents with page, clause, cell or timestamp. Distinguish quotations, paraphrases and interpretation. Register IDs support traceability but do not replace the original citation.

Save `register.json` and `Analysis.md` with authorised host tools to the canonical location, reopen both and check that they show the same revision. Return their links, the coverage and any unintegrated findings. Produce the client DDQ with `ddq FOLDER` only when asked. The views do not copy sources: keep authorised extracts separately or retrieve originals through their links. Never overwrite a newer saved register. If access or execution fails, report what is unsaved and the handoff needed.

`ready` records that the register's checks passed for the document named in control `word`; it is not institutional approval or contract execution.
