# The standard

The standard says what a deal folder holds and what must be known. It gives the work its rigour. `show <ID>` prints an indicator or a check in full. `standard/FRAMEWORK.md` in the repository explains how it is organised.

## Work from the claims

The standard holds 70 claims. An indicator is one claim: what the lender relies on, in a sentence that can turn out false. The checks behind it try to disprove it. The claims sit in nine pillars: the deal, then each party from its surroundings to its money, then the links, then the facility.

Start from the claims, not from the checks.

- **`show claims`** lists every claim by pillar, one line each:

  ```text
  - Currency risk (Cedar Foods Ltd): challenged; tests answered 1 of 4; against OBS_FX_008; mitigants 5 not known; agreed action D-002 [CAS_FX_001]
  ```

- **`status --for <ID>`** shows only what concerns one subject or link: its claims, its open checks, its questions. For a subject it includes the links that touch it. `status --for DEAL` keeps to the checks about the deal.
- **`show <indicator>`** prints one claim with all its checks and what each rests on.

A check has one of three jobs:

- A **question** opens the topic or describes it.
- A **test** has an assumption. One answer goes against it.
- A **mitigant** is asked once a test has gone against the claim. It asks what limits the damage.

For each claim, and each party or link it is made about, the tool says where it stands:

| The claim | Means |
|---|---|
| is **not tested** | No test is answered, or the answers rest only on someone's own word. |
| **stands so far** | Some tests are answered, none goes against it, and at least one rests on more than someone's word. Other tests are still open. |
| **stands** | Every test is answered, none goes against it, and at least one rests on more than someone's word. |
| is **challenged** | A test went against it. The tool lists the mitigants: each holds, fails or is not known. |
| is **contested** | Two facts answer a test differently. |

`status` shows the claims by pillar and lists those that are challenged, contested or to look at again. A claim made about several parties counts once, at its worst.

Who says something matters. An answer that goes against a claim is believed whatever it rests on. A favourable answer that rests only on what a party said is marked as **someone's own word**, and a claim does not stand on that alone. Set `said_by` on every fact.

## Judgement

The standard is a backbone. It does not replace the analysis.

- **Size.** A test asks about what matters for repayment. Where the thing exists but is too small to matter, give the favourable answer and say in the fact how small it is: "One supplier credit in euros, KES 4m, 0.3% of all debt." The sizes named in questions, such as "about a tenth", are guides.
- **Answer a test as soon as it is decided.** Some tests speak of "this loan included" or "after this loan". If the answer already goes against the assumption on the debt the party owes today, record it now and say that it is before the new loan. Answer again when the terms are known. An answer in favour waits for the terms: until the amount, the currency and the tenor are known, record today's figure as a fact and leave the test open.
- **Read the open tests of a claim before you rely on it.** `show <deal> <indicator>` lists them. The record often decides one that nobody has answered yet.
- **One case can decide a test against the claim. A favourable answer needs the whole.** If a test asks about five years and the documents cover three, a bad year among the three decides it. Three good years do not: record the figures, leave the test open and ask for the rest.
- **Some questions ask for description**, not for a verdict: how the business earns its money (`OBS_BUSINESS_MODEL_001`), what is particular about it (`OBS_BUSINESS_MODEL_002`), what the project is (`OBS_FEAS_008`), and what an owner owes and receives on its own account (`OBS_GROUP_011`, `OBS_GROUP_012`). Their answers feed the pages. Answer them early. `show <deal> <words>` finds the check that asks about something.

## Who is asked what

A check is asked about the deal, about whoever holds a role, about a subject of a kind, or about a link.

- **The loan under review.** A facility is a loan the lender is considering. The roles of borrower and guarantor, and the checks on a guarantee or on security, arise only from links that point at a facility. Debt that already exists is a `lends_to` link and brings the checks on another lender.
- **The perimeter.** The business and its money are examined once, on the party or group whose cash repays the loan. Five pillars are asked of the perimeter: environment, business, cash flow and debt, liquidity and financial risks, and environmental, social and impact. Related parties and a guarantor's capacity are asked the same way. A company that is a member of a group that is asked the same check is not asked it again.
- **The legal entity.** People and governance is asked of each company: its owners, its integrity, its board, its standing. A group is not asked these. Each company you recorded as a member of the group is asked them in its place, whether it borrows or not: the parent of a borrowing subsidiary as well.
- **The tie between them.** Where the borrower is not the whole perimeter, the links between the companies are examined for whether the cash can reach the lender.
- **A person** is asked only what fits a person.
- **A project** is checked only when the loan finances it. It is asked what is its own: whether it can be built and pay, its impact assessment and permits, its land, its neighbours. What concerns the whole business stays with the perimeter.
- **An owner.** `owns` and `sponsors` give their role, and bring the checks on the tie between owner and company, only between parties. Who owns a plant or a project is recorded the same way and brings no checks.

See [recording](recording.md) for how to record each of these.

## Discovery

The checks of the first pillar are about the deal: what is asked for, how the loan is repaid, who is in it and what kind of business it is. Answer them first. Many other checks wait for them: `status` says how many.

- The kind of credit (`OBS_SECTOR_001`) and the sector (`OBS_SECTOR_002`) decide which checks apply. Both go by where the profit comes from: a business that trades more than it makes, and earns most of its profit from what it makes, is a manufacturer. If one party is of another kind than the rest of the deal, record the answer for that party with `"for"`.
- Some answers call for structure: a party, a link, an asset, a project or a contract. `status` lists these under "Structure still open". Add what is missing, and the link brings its own checks. If nothing needs to be added, record a decision that `covers` the check, with the reason and without an owner or a date.

## Checks

A check answers by facts: put it in the fact's `answers`. In `status`, each open check ends with its ID and the answer it takes:

```text
[OBS_ACC_001: yes/no]   [OBS_OFFTAKER_002: number, percent]   [OBS_LIFECYCLE_001: one of greenfield | expanding | established | distressed]   [OBS_REQUEST_001: text]
```

"any of" in place of "one of" means that several options may be given, as a list.

| State | Meaning |
|---|---|
| `open` | It can be answered now. |
| `waiting` | An earlier check comes first, or the role is not yet held by anyone. |
| `not relevant` | An earlier answer made it so. |
| `answered` | A fact answers it. `thin`: the evidence is weaker than is ideal at this stage. `old`: it is older than is ideal. |
| `contested` | Two facts answer it differently, or the fact is disputed. |
| `parked`, `off` | Switched off for now, or for this deal. |

For a test the tool also says whether the answer goes against the assumption. A reference point such as "above 20" is the standard's own, with its reason in `why`. It can be changed with `adjust`.

## Evidence and kinds of source

Evidence has three strengths: `best`, `supporting`, and `stated` for what someone said. Each check lists which kinds of source count as which. Each stage names the strength that is ideal by then. Nothing is demanded. The tool shows what an answer rests on.

The kind you give a source therefore decides two things: the folder it is filed in, and how strong the evidence of its facts counts. `show kinds` lists every kind with its folder. Choose the kind for what the document is.

| The document | Its kind | Filed in | Counts as |
|---|---|---|---|
| Audited financial statements with the auditor's opinion | `audited_annual_report` | `Client folder` | Best evidence for most financial checks |
| The company's annual report, which is not itself audited | `annual_report` | `Client folder` | Supporting |
| A prospectus or another offering document | `prospectus` | `Client folder` | Supporting |
| A newspaper or news-service article | `press_article` | `Internal/sources` | Supporting, where a check lists it |
| A website, a registry website, market data | `public_source` | `Internal/sources` | Supporting, where a check lists it |

`show <check>` prints the kinds that the check lists under `evidence`. A kind it does not list shows as `unlisted` and counts as the weakest.

## A gap with an agreed action

A check can stay open with an agreed action: a condition, a covenant or a task with an owner and a date. Record a decision that `covers` the check and names the `owner` and the `due` date. See [recording](recording.md). The check then leaves the list of checks to answer and appears under "Gaps with an agreed action".

## Stages

Stages are targets, not gates. "Ideally by concept" means the answer is ideally there for the concept note. Nothing waits for a stage. Move the deal with `{"deal": {"stage": "diligence"}}` in a set of changes.

## Adjusting

The officer adjusts the standard by saying so. You write the adjustment and hand it to `adjust`. Every adjustment needs a `reason`. Add `"by"` with who asked.

```json
[
 {"do": "add", "to": "CAS_INPUT_CONC_001", "by": "officer",
  "reason": "The CFO put the margin drop down to milk prices.",
  "check": {"id": "DEAL_MILK_PRICE_001", "question": "Do the supply contracts cap the raw milk price?",
            "answer": "yes_no", "assumption": "The supply contracts cap the price Cedar pays for raw milk",
            "disproved_by": "no", "when": [{"check": "OBS_INPUT_001", "is": true}]}},
 {"do": "change", "target": "OBS_REV_003", "set": {"due_by": "concept"}, "reason": "Needed for the CIP."},
 {"do": "switch_off", "target": "CAS_COVERAGE_001", "strength": "not_now",
  "reason": "Insurance is reviewed once the term sheet is agreed."},
 {"do": "switch_on", "target": "CAS_COVERAGE_001", "reason": "The term sheet is agreed."}
]
```

- **`add`** a check to an indicator (`to`), or a whole `indicator` with its `id`, `title`, `pillar`, `claim`, `due_by`, `applies_to` and `checks`. Copy the shape from `show` of an existing indicator. Give a new check an ID that starts with `DEAL_`. Write the assumption as what the lender relies on, so that the answer that disproves it is bad news.
- **`change`** any field of a check or an indicator. Set a field to `null` to take it off.
- **`switch_off`** a check or an indicator, in one of two strengths:
  - `not_now`: it leaves the next list and comes back when the stage changes or when a check it follows gets a new answer.
  - `not_for_this_deal`: it is off until someone switches it on.
- **`switch_on`** undoes a switch-off.

The tool refuses an adjustment that names something unknown, lacks a reason, or touches what the institution has locked. A lock on an indicator covers its checks, and a lock on a check covers its indicator.

An adjustment that should hold for every deal belongs in the institution's layer. Tell the officer. Moving it there is their step.

## A newer standard, or an older folder

`upgrade` puts the standard that comes with the tool into the deal folder and records the change of version in the log. It prints the recorded answers that name a check which no longer exists: they stay in the facts and no longer count. Look at each and answer the check that took its place.

A folder made by an earlier version of the tool keeps its record in `Internal/memory/memory.json`. Every command then says so and names the remedy. `upgrade` moves the record to `Internal/record/record.json`. The documents of such a folder stay in the folders they were filed in, and the record still finds them. Only documents filed from then on go flat into `Client folder`.

`doctor` says which version of the standard the tool carries and which the deal uses.

## The institution's layer

`Internal/standard/institution.json` holds what the institution set for all its deals: its names for the stages, its own checks, what it locked, and the fields of its systems. Do not change it.

`show sheet` prints each system with its fields: the value, the fact and the source, or **missing**. To fill a field, add its ID to a fact's `fills`.
