# The standard

`show <deal> <ID>` prints a check of the standard, the Bankability DDQ, in full, or an indicator with its checks and the answer each takes. `status <deal> --for <pillar> --all` lists the checks of one pillar that are to answer: the pillars are `deal`, `environment`, `business`, `governance`, `cash_flow`, `liquidity`, `es_impact`, `links` and `facility`.

## Claims

The standard holds 70 claims in nine pillars. An indicator is one claim: what the lender relies on, in a sentence that can turn out false. Its checks try to disprove it. Start from the claims: `show <deal> claims` lists every claim that applies, and `show <deal> <indicator>` prints one with all its checks.

A **question** opens the topic or describes it. A **test** has an assumption, and one answer goes against it. A **mitigant** is asked once a test has gone against the claim: what limits the damage.

A claim, for each party or link it is made about:

- is **not tested**: no test is answered, or the answers rest only on someone's own word.
- **stands so far**: nothing speaks against it, and work is left. A test is open, waits or is parked, or an answer rests on someone's own word, on evidence the check does not list as supporting or best, or on evidence that is weak (`thin`) or out of date (`old`) for this stage.
- **stands**: every test is answered in its favour, on evidence the check lists as supporting or best.
- is **challenged**: a test went against it. Each mitigant holds, fails or is not known.
- is **contested**: two facts answer a test, or a question behind the claim, differently, or the fact that answers one is disputed.

A claim is to **look at again** when a source or an answer that bears on it came in after its tests were answered. Read the new source against the tests of the claim. Where an answer changes, record it. Where none does, send the fact that answers one of its tests again, with its `answers` as they are and a sentence added to its `statement` that says what you read it against and when. The claim counts as looked at once one of its tests is answered by a fact whose answers were sent after the source came in. A question of the claim does not count.

In `status`, the line of a pillar counts each claim once, at its worst among the parties it is made about. `show <deal> claims` gives each party its own line.

An answer against a claim is believed whatever it rests on. A favourable answer to a test is **someone's own word** where it rests only on what a party says of itself (`said_by: client`), or only on evidence the check lists as `stated`, such as the notes of a call, whoever recorded it. A claim does not stand on that alone. The page of checks and `show <deal> <check>` mark such an answer `own word`. A question has no favourable answer, so it is not marked. So set `said_by` on every fact.

## Judgement

- **Size.** Where the thing a test asks about is too small to matter for repayment, give the favourable answer and say in the fact how small it is: "One supplier credit in euros, KES 4m, 0.3% of all debt." A size named in a question, such as "about a tenth", is a guide.
- **Answer a test as soon as it is decided.** If today's debt already goes against a test that speaks of "after this loan", record the answer now and say that it is before the new loan. An answer in favour waits for the terms: record today's figure as a fact and leave the test open.
- **Not asked yet is not a no.** A test that asks whether something exists, such as a maintenance plan, is answered no when the company says there is none, or when the place that would hold it has been searched.
- **One case can decide a test against the claim. A favourable answer needs the whole.** If a test asks about five years and the documents cover three, a bad year among the three decides it. Three good years do not: record the figures and ask for the rest.
- **Read the open tests of a claim before you rely on it**, and answer those the record already decides.
- **An answer that turns on your reading** of an accounting or a legal question is an inference. Say so in the fact, and list it in the working notes for the analyst to confirm.
- **Some questions ask for description**: how the business earns its money (`OBS_BUSINESS_MODEL_001`), what is particular about it (`OBS_BUSINESS_MODEL_002`), what the project is (`OBS_FEAS_008`). Their answers feed the pages. Answer them early, and ask early what an owner owes and receives on its own account (`OBS_GROUP_011`, `OBS_GROUP_012`).

## Who is asked what

A check is asked about the opportunity, about whoever holds a role, about a subject of a kind, or about a link: see [recording](recording.md).

- **The opportunity first.** The checks of the first pillar ask what is asked for, how the loan is repaid, who is in the deal and what kind of business it is. Answer them first: many other checks wait for them. The kind of credit (`OBS_SECTOR_001`) and the sector (`OBS_SECTOR_002`) decide which checks apply, and go by where the profit comes from. If one party is of another kind than the rest, record the answer for that party with `"for"`.
- **Structure.** Some answers call for a party, a link, an asset, a project or a contract. `status` lists these under "Structure still open". Add what is missing, or record a decision that `covers` the check and says why nothing is needed, without an owner or a date. Name in `about` the subject whose answer it is.
- **Opening questions.** The checks on terms, covenants and conditions wait until terms are on paper (`OBS_TS_011`), and the checks on security until it is known what is offered (`OBS_SECPKG_001`). Leave such a question open while its answer is not known. "None" is an answer only once that is settled, as for a loan that is to be unsecured.
- **An asset, a contract and a customer** are examined when repayment depends on them. A question asks that first (`OBS_ASSET_007`, `OBS_CONT_001`, `OBS_OFFTAKER_001`).

## Checks

A check is answered by a fact, in its `answers`. In `status`, a check that stands the same for several subjects has one line that names them all. Each open check ends with its ID and the answer it takes: `[OBS_ACC_001: yes/no]`, `[OBS_OFFTAKER_002: number, percent]`, `[OBS_LIFECYCLE_001: one of greenfield | expanding | established | distressed]`. "any of" in place of "one of" means that a list of options may be given. A check is in one of these states:

- `open`: it can be answered now.
- `waiting`: an earlier check comes first, or nobody holds the role yet, or it is a mitigant and no test has gone against its claim.
- `not relevant`: an earlier answer made it so.
- `answered`: a fact answers it. `thin`: the evidence is weaker than is ideal at this stage. `old`: it is older than is ideal.
- `contested`: two facts answer it differently, or the fact is disputed.
- `parked`, `off`: switched off for now, or for this deal, or settled for one subject by a decision.

A reference point such as "above 20" is the standard's own, with its reason in `why`. `adjust` can change it.

## The page of checks

Who or what settles a check depends on the deal, so the standard does not say: where it helps, say on an open check what is missing and who could give it, in a note (see "What is missing" below).

The tool writes the page of checks, `Internal/wiki/checks.md`, on every `pages`. It is listed last on the contents page and in the browser view, as "The due diligence list". It holds the count of checks in each state and of the open checks by stage; "What matters most", below; "Names in the record", the parties and people that the record names; then, pillar by pillar and claim by claim, every check with its state, whom it is asked of (one row where it stands the same for several), its answer, what is missing or what it waits for, and the stage it is ideally answered by; and last the documents that are not in the folder.

In the browser view, buttons choose which states show: to answer, waiting, answered, not relevant or off, all. Never edit this page. Send the analyst there when they ask what is left and whether it matters.

**What matters for this deal.** The page lists every check, and most open checks are ordinary due diligence. Mark the ten to twenty the decision turns on, each with one sentence that says why, on the analyst's word or as your own reading, which you then say:

```json
{"do": "change", "target": "OBS_DEBT_008", "by": "assistant",
 "set": {"matters": "The debt schedule decides how much room is left for a new loan."},
 "reason": "Marked as material for this deal."}
```

The page of checks then starts with "What matters most": one row for each of these checks, with its reason, and each subject it is asked of with its state and its answer. `status` lists them under "What matters most" by their ID and reason, each with whom it is open or answered for. An answered check stays on the list, so the analyst sees what was decided. `"matters": null` takes the mark off. Review the marks when the stage changes or a large document comes in.

**What is missing.** Where a check has to stay open, say for the subject it is asked of what is missing to answer it:

```json
{"do": "note", "target": "OBS_REV_004", "for": "P-001", "by": "assistant",
 "reason": "Only figures for the group exist. The company's own figures are asked in Q-004."}
```

The note answers nothing and keeps the check on the list. It is shown beside the open check on the page of checks, in `status` where the check is among those listed (`--all` lists every one) and in `show <deal> <check>`, and no longer once the check is answered. A new note for the same check and subject replaces the old one. The records it names count as cited in the browser view and in `show <ID>`, which lists the check among what uses them, but not in `show <deal> uncited`, which is about the wiki's pages.

## Evidence and kinds of source

Evidence has three strengths: `best`, `supporting`, and `stated` for what someone said. Each check lists under `evidence` which kinds of source count as which. A kind it does not list counts as the weakest, but does not by itself make an answer someone's own word. Nothing is demanded.

So choose the kind of a source for what the document is. An annual report that is not itself audited is `annual_report`, not `audited_annual_report`, and counts as supporting where a check lists it, as a `prospectus` does.

## A decision that covers a check

- **A gap with an agreed action**: a condition, a covenant or a task. Record a decision that `covers` the check and names the `owner` and the `due` date. Name in `about` the subject or the link the check is asked of, or leave `about` out to cover the check for everyone it is asked of.
- **Settled for one subject**: one lender's ranking cannot matter here, or a customer is too small to count. Record a decision that `covers` the check, with the reason, and without an owner or a date. Name in `about` the ID of the subject or the link the check is asked of: `show <deal> <check>` names it, and `show <deal> subjects` or `links` gives its ID. For a check on an owner's tie that is the `owns` link, not the owner. The check then shows as `off` there, and stays asked of the others. Where a fact already answers it, the answer stays and the decision shows beside it. Do this on the analyst's word. A check the institution has locked cannot be settled this way. `add` prints a `Note:` when a decision covers a check for a subject it is not asked of.
- **A check that opens others is answered, not settled.** For a plant that carries little, answer `OBS_ASSET_007` no, and the checks on its condition fall away.

## Stages

Stages are targets, not gates: nothing waits for a stage. A set of changes moves the deal to the next one: see [recording](recording.md).

## Adjusting

The analyst adjusts the standard by saying so. You hand `adjust` a list. Every adjustment needs a `reason`. Add `"by"` with who asked.

```json
[
 {"do": "add", "to": "CAS_INPUT_CONC_001", "by": "analyst",
  "reason": "The CFO put the margin drop down to milk prices.",
  "check": {"id": "DEAL_MILK_PRICE_001", "question": "Do the supply contracts cap the raw milk price?",
            "answer": "yes_no", "assumption": "The supply contracts cap the price Cedar pays for raw milk",
            "disproved_by": "no", "when": [{"check": "OBS_INPUT_001", "is": true}]}},
 {"do": "change", "target": "OBS_REV_003", "set": {"due_by": "concept"}, "reason": "Needed for the CIP."},
 {"do": "switch_off", "target": "CAS_COVERAGE_001", "strength": "not_now",
  "reason": "Insurance is reviewed once the term sheet is agreed."}
]
```

- **`add`** a check to an indicator (`to`), or a whole `indicator` with its `id`, `title`, `pillar`, `claim`, `due_by`, `applies_to` and `checks`. Copy the shape from `show` of an existing one. Give a new check an ID that starts with `DEAL_`. Write the assumption as what the lender relies on, so that the answer that disproves it is bad news.
- **`change`** any field of a check or an indicator. `null` takes a field off.
- **`note`** on an open check what is missing for one subject: see "What is missing" above.
- **`switch_off`** a check or an indicator. `not_now`: it comes back when the stage changes or when a check it follows gets a new answer. `not_for_this_deal`: it is off until a `switch_on`, which takes a `target` and a `reason`.

The tool refuses a `change` or a `switch_off` of what the institution has locked. An adjustment that should hold for every deal belongs in the institution's layer: tell the analyst.

## A newer standard, or an older folder

`upgrade` puts the standard that comes with the tool into the deal folder. It moves the pages of an older wiki to the folders this version uses, and takes the records to the names the standard now uses. It prints the answers that name a check which no longer exists, and the checks that are new, gone and changed, and writes the pages again.

- Such an answer no longer counts. Look at the new checks of the same indicator. Where the fact decides one, add that answer to the fact. Where none fits, send the fact's `id` with its `answers` without the old one.
- Read the changed checks that are already answered: an answer may no longer fit its question.
- A check that the deal's or the institution's own layer added with `settled_by` keeps that field, which nothing reads since standard 4.4.0; to take it out, `adjust` with `{"do": "change", "target": "<the check>", "set": {"settled_by": null}, "reason": "No longer read."}`.
- Where a folder keeps its record in `Internal/memory/memory.json`, or its standard in `Internal/standard`, every command says so, and `upgrade` moves it to `Internal/record`. Then remove the empty folder yourself.

## The institution's layer

`Internal/record/institution.json` holds what the institution set for all its deals: its names for the stages, its own checks, what it locked, and the fields of its systems. Do not change it. `show <deal> sheet` prints each system with its fields: the value, the fact and the source, or **missing**. To fill a field, add its ID to a fact's `fills`.
