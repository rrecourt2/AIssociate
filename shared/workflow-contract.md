# Evidence workflow

Use the shipped Python 3.9+ scripts in the host workspace. They do not run on the officer's computer or provide storage connectors. One task owns `register.json`; specialists return proposed changes against its revision.

## Start or resume

Confirm the purpose, relevant source scope/cutoff and approved save location; reuse settled choices. Start here without a template, borrower or selected financing structure. Read the saved brief and coverage before retrieving more evidence.

| Need | Command |
|---|---|
| Start | `python3 scripts/register.py init FOLDER --deal example` |
| Resume | `python3 scripts/register.py show FOLDER` |
| Selected records / FP section | `python3 scripts/register.py show FOLDER C-001 O-002` / `show FOLDER --section summary` |
| Apply changes | `python3 scripts/register.py apply FOLDER changes.json` |
| Open work / client questions | `python3 scripts/register.py lists FOLDER` / `ddq FOLDER` |
| Restore views / upgrade | `python3 scripts/register.py refresh FOLDER` / `migrate FOLDER` |

A change request has `base_revision`, unique `op_id`, `actor`, `summary` and `changes`. Changes use `{"sheet":"claims","add":{...}}`, `{"sheet":"claims","update":"C-001","set":{...}}` or `{"sheet":"control","set":{...}}`. Table fields are strings; omit unavailable values. Consult the relevant `TABLES`/`ALLOWED` definitions. Retry unchanged requests with the original ID; reconcile stale revisions. Migration retains a backup and history.

## Keep useful memory

- **Brief:** use Analysis key `strategy` for the purpose, current stage, hypotheses/alternatives and next decision or action. Distinguish officer instructions from reported assertions and suggested steps. Use `timeline` for dated decisions and their reasons, including rejected alternatives that explain the current direction. Update these when intent changes; no fixed questionnaire is required.
- **Sources:** original reference, version/hash, entity/period, reviewed scope, coverage and reusable extract path. New versions get a new ID and `supersedes`; preserve unaffected historical facts and obligations. Assess previously unlinked contrary evidence too.
- **Claims:** material assertion, kind, entity/period, located sources, support and qualifications. Figures add value, unit and definition; calculations add method and located inputs. Keep attribution and conflicting evidence.
- **Analysis:** reasoning, linked claims/sources and internal actions. Reconcile specialist findings into this record or mark them unintegrated; temporary reviews are not saved deal memory.
- **Open items:** purpose, evidence/action needed, owner and explicit audience: `client`, `internal`, `restricted` or `unknown`. Distinguish missing knowledge from unread material. Check whether historical issues still apply. Only client-facing open/promised questions enter the DDQ.

Changed answer sources or cited calculations reopen affected answers for reassessment and block readiness. Prior assessments remain in the log. Closure needs an assessor, rationale and current located support; reliance on superseded evidence alone requires an attributed officer exception. Assess the change before clearing rechecks. A received answer or accepted uncertainty is not an established fact. Recheck does not automatically repeat the client question.

## Answer and save

Match the output to the request: a small investigation usually needs a concise answer, record update and a few material follow-ups. Stop when enough is known for the next decision. Gap assessments prioritise what still needs evidence, action or judgment; FP drafting is optional and uses FP Lead's Word workflow.

Cite original documents with page, clause, cell or timestamp in user-facing answers. Distinguish quotations, paraphrases and interpretation. Keep internal IDs for traceability; a register citation alone does not replace the original source.

The evidence owner can save `register.json` and generated `Analysis.md` directly through authorised host tools to one canonical case location. Reopen both saved files and verify content/hashes and matching revision before claiming persistence; return both links and state coverage or unintegrated findings. Deliver generated Excel or client DDQ views only when useful or requested. Preserve authorised caches separately or retrieve originals through their references; generated views do not copy source documents. Local revision checks are not cloud locks. If access or execution fails, identify the unsaved work and required handoff.
