# The standard

The standard says what a deal folder holds and what must be known. `show <ID>` prints an indicator or a check in full. `standard/FRAMEWORK.md` in the repository explains how it is organised.

## Claims

The standard is built on claims. An indicator is one claim: what the lender relies on, in a sentence that can turn out false. Its checks try to disprove it. The indicators sit in nine pillars: the deal, then each party from its surroundings to its money, then the links, then the facility.

A check has one of three jobs:

- A **question** opens the topic or describes it.
- A **test** has an assumption. One answer goes against it.
- A **mitigant** is asked once a test has gone against the claim. It asks what limits the damage.

For each claim, and each party or link it is made about, the tool says where it stands:

| The claim | Means |
|---|---|
| is **not tested** | No test is answered, or the answers rest only on someone's own word. |
| **stands** | Tests are answered, none goes against it, and at least one rests on more than someone's word. |
| is **challenged** | A test went against it. The tool lists the mitigants: each holds, fails or is not known. |
| is **contested** | Two facts answer a test differently. |

`status` shows the claims by pillar and lists those that are challenged, contested or to look at again. A claim made about several parties counts once, at its worst.

Who says something matters. An answer that goes against a claim is believed whatever it rests on. A favourable answer that rests only on what a party said is marked as **someone's own word**, and a claim does not stand on that alone. Set `said_by` on every fact.

## Discovery

The checks of the first pillar are about the deal: what is asked for, how the loan is repaid, who is in it and what kind of business it is. Answer them first. Many other checks wait for them: `status` says how many.

- The kind of credit (`OBS_SECTOR_001`) and the sector (`OBS_SECTOR_002`) decide which checks apply. If one party is of another kind than the rest of the deal, record the answer for that party with `"for"`.
- Some answers call for structure: a party, a link, an asset, a project or a contract. `status` lists these under "Structure still open". Add what is missing, and the link brings its own checks. If nothing needs to be added, record a decision that `covers` the check, with the reason.

## Checks

A check is asked about the deal, about whoever holds a role, or about a link. A check answers by facts: put it in the fact's `answers`.

| State | Meaning |
|---|---|
| `open` | It can be answered now. |
| `waiting` | An earlier check comes first, or the role is not yet held by anyone. |
| `not relevant` | An earlier answer made it so. |
| `answered` | A fact answers it. `thin`: the evidence is weaker than is ideal at this stage. `old`: it is older than is ideal. |
| `contested` | Two facts answer it differently, or the fact is disputed. |
| `parked`, `off` | Switched off for now, or for this deal. |

For a test the tool also says whether the answer goes against the assumption. A reference point such as "above 20" is the standard's own, with its reason in `why`. It can be changed with `adjust`.

Evidence has three strengths: `best`, `supporting`, and `stated` for what someone said. Each check lists which kinds of source count as which. Each stage names the strength that is ideal by then. Nothing is demanded. The tool shows what an answer rests on.

## A gap with an agreed action

A check can stay open with an agreed action: a condition, a covenant or a task with an owner and a date. Record a decision that `covers` the check. See [recording](recording.md). The check then leaves the list of checks to answer and appears under "Gaps with an agreed action".

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

## The institution's layer

`Internal/standard/institution.json` holds what the institution set for all its deals: its names for the stages, its own checks, what it locked, and the fields of its systems. Do not change it.

`show sheet` prints each system with its fields: the value, the fact and the source, or **missing**. To fill a field, add its ID to a fact's `fills`.
