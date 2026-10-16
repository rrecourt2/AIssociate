# Evidence workflow

Use the shipped Python 3.9+ scripts in the host workspace; the host supplies storage connectors. One task owns `register.json`; specialists propose changes against its revision.

## Start or resume

Confirm the purpose, relevant source scope/cutoff and approved save location; reuse settled choices. Start here without a template, borrower or selected financing structure. Read the saved brief and coverage before retrieving more evidence.

| Need | Command |
|---|---|
| Start | `python3 scripts/register.py init FOLDER --deal example` |
| Resume | `python3 scripts/register.py show FOLDER` |
| Selected records / document section | `python3 scripts/register.py show FOLDER C-001 O-002` / `show FOLDER --section summary` |
| Apply changes | `python3 scripts/register.py apply FOLDER changes.json` |
| Open work / client questions | `python3 scripts/register.py lists FOLDER` / `ddq FOLDER` |
| Restore views / upgrade | `python3 scripts/register.py refresh FOLDER` / `migrate FOLDER` |

A change request has `base_revision`, unique `op_id`, `actor`, `summary` and `changes`. Changes use `{"sheet":"claims","add":{...}}`, `{"sheet":"claims","update":"C-001","set":{...}}` or `{"sheet":"control","set":{...}}`. Table fields are strings; omit unavailable values. Consult the relevant `TABLES`/`ALLOWED` definitions. Retry unchanged requests with the original ID; reconcile stale revisions. Migration retains a backup and history.

## Keep useful memory

- **Brief:** use Analysis key `strategy` for purpose, document/stage, author perspective, audience, length and next decision. Keep hypotheses distinct from Investment Officer instructions and adopted decisions. Use `timeline` for dated decisions and reasons, including rejected alternatives. Update when intent changes; no fixed questionnaire is required.
- **Sources:** original reference, version/hash, entity/period, reviewed scope, coverage and reusable extract path. New versions get a new ID and `supersedes`; preserve unaffected historical facts and obligations. Assess previously unlinked contrary evidence too.
- **Claims:** distinguish facts, assertions, assumptions, calculations and judgments using `kind`; retain entity/period, sources and support status. Assumptions need an explicit basis and adoption status, not a claim of verification. Figures add value, unit and definition; calculations add method and located inputs.
- **Analysis:** reasoning, linked claims/sources and internal actions. Reconcile specialist findings into this record or mark them unintegrated; temporary reviews are not saved deal memory.
- **Open items:** what needs verification, why, evidence/action needed, owner and audience: `client`, `internal`, `restricted` or `unknown`. Link to the affected claim/risk; distinguish missing knowledge from unread material. Check historical relevance. Only client-facing open/promised questions enter the DDQ.

Reuse stable IDs: `inputs` connects dependent claims/assumptions/calculations; Analysis `claims` and document mappings connect conclusions and passages. Keep these links explicit so changes trigger the affected rechecks. The structured record can support later system-field mapping; do not invent target fields or treat unverified data as approved system input.

In `answer_source`, cite located original sources and the claim IDs the assessment relies on; an open-item `link` alone does not trigger reassessment. Changed support reopens affected answers and blocks readiness; prior assessments remain in the log. Closure needs an assessor, rationale and current support, or an attributed Investment Officer exception. Assess before clearing rechecks. Receipt or accepted uncertainty is not verification; recheck need not repeat the client question.

## Answer and save

Stop when enough is known for the next decision; a small investigation needs a concise answer, record update and material follow-ups. Use Document Lead only when drafting is requested. Preserve prior deliverables when switching purpose: tools track one current Word build. Early-stage work can be useful with open diligence; `ready` checks the current Word and register, not institutional approval or contract execution.

Cite original documents with page, clause, cell or timestamp in user-facing answers. Distinguish quotations, paraphrases and interpretation. Keep internal IDs for traceability; a register citation alone does not replace the original source.

Save `register.json` and generated `Analysis.md` through authorised host tools to one canonical location. Reopen both and verify content/hashes and matching revision; return links, coverage and unintegrated findings. Deliver Excel or client DDQ views when useful. Retain authorised caches separately or retrieve originals through their references; views do not copy sources. Local revision checks are not cloud locks. Report unsaved work and the required handoff if access or execution fails.
