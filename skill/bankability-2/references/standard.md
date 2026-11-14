# The standard

The standard says what a deal folder holds and what must be known. `show <ID>` prints an indicator or a check in full.

## Checks

A check is one question, asked about the deal, about whoever holds a role, or about a link. Most checks test a stated assumption. A check answers by facts: put it in the fact's `answers`.

| State | Meaning |
|---|---|
| `open` | It can be answered now. |
| `waiting` | An earlier check comes first, or the role is not yet held by anyone. |
| `not relevant` | An earlier answer made it so. |
| `answered` | A fact answers it. `thin`: the evidence is weaker than is ideal at this stage. `old`: it is older than is ideal. `flagged`: the answer meets the standard's reference point. |
| `contested` | Two facts answer it differently, or the fact is disputed. |
| `parked`, `off` | Switched off for now, or for this deal. |

For a yes/no check the tool also says whether the assumption **stands** or is **disproved**.

Evidence has three strengths: `best`, `supporting`, and `stated` for what someone said. Each check lists which kinds of source count as which. Each stage names the strength that is ideal by then. Nothing is demanded. The tool shows what an answer rests on.

## Stages

Stages are targets, not gates. "Ideally by concept" means the answer is ideally there for the concept note. Nothing waits for a stage. Move the deal with `{"deal": {"stage": "diligence"}}` in a set of changes.

## Adjusting

The officer adjusts the standard by saying so. You write the adjustment and hand it to `adjust`. Every adjustment needs a `reason`. Add `"by"` with who asked.

```json
[
 {"do": "add", "to": "CAS_INPUT_CONC_001", "by": "officer",
  "reason": "The CFO put the margin drop down to milk prices.",
  "check": {"id": "DEAL_MILK_PRICE_001", "question": "Do the supply contracts cap the raw milk price?",
            "answer": "yes_no", "assumption": "Cedar carries the full risk of the raw milk price",
            "disproved_by": "yes", "after": ["OBS_INPUT_001"]}},
 {"do": "change", "target": "OBS_REV_003", "set": {"due_by": "concept"}, "reason": "Needed for the CIP."},
 {"do": "switch_off", "target": "CAS_COVERAGE_001", "strength": "not_now",
  "reason": "Insurance is reviewed once the term sheet is agreed."},
 {"do": "switch_on", "target": "CAS_COVERAGE_001", "reason": "The term sheet is agreed."}
]
```

- **`add`** a check to an indicator (`to`), or a whole `indicator`. Give a new check an ID that starts with `DEAL_`.
- **`change`** any field of a check or an indicator.
- **`switch_off`** a check or an indicator, in one of two strengths:
  - `not_now`: it leaves the next list and comes back when the stage changes or when a check it follows gets a new answer.
  - `not_for_this_deal`: it is off until someone switches it on.
- **`switch_on`** undoes a switch-off.

The tool refuses an adjustment that names something unknown, lacks a reason, or touches what the institution has locked.

An adjustment that should hold for every deal belongs in the institution's layer. Tell the officer. Moving it there is their step.

## The institution's layer

`Internal/standard/institution.json` holds what the institution set for all its deals: its names for the stages, its own checks, what it locked, and the fields of its systems. Do not change it.

`show sheet` prints each system with its fields: the value, the fact and the source, or **missing**. To fill a field, add its ID to a fact's `fills`.
