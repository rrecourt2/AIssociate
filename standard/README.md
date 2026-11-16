# The Bankability Standard

The standard says what a deal folder holds and what must be known about a deal. It is data only: lists, a data-room structure and checks. No meaning lives in code.

Version 4.2.0 holds 70 indicators with 551 checks in nine pillars, a data room of 10 folders with 64 slots, and 82 kinds of source.

- [FRAMEWORK.md](FRAMEWORK.md) explains how the standard is organised, and why. Read it first.
- [CHANGES.md](CHANGES.md) lists what changed: after two trials on a real company, and from the first Bankability's standard.

## The files

```text
standard/
├── FRAMEWORK.md            the thinking behind the standard
├── standard.yaml           name and version
├── lists/
│   ├── stages.yaml         the stages of a deal, and the evidence that is ideal at each
│   ├── pillars.yaml        the nine pillars, each in one layer
│   ├── subject-kinds.yaml  party, person, facility, contract, asset, project, group
│   ├── link-types.yaml     how subjects are linked, and the role a link gives
│   └── source-kinds.yaml   kinds of document, call and note, each with its slot in the data room
├── dataroom.yaml           folders, sub-folders and slots: an index of where a document belongs
├── indicators/             one file per indicator, in a folder per pillar
└── build.py                checks the standard and builds it
```

## The lists

A few fields in the lists decide who is asked what. The tool only applies them.

| List | Field | Meaning |
|---|---|---|
| `pillars.yaml` | `asked_of` | `perimeter`: the pillar is asked once, of the party or group whose cash repays the loan, and not again of a member of a group that is asked the same check. `entity`: it is asked of each legal entity, and never of a group. |
| `subject-kinds.yaml` | `prefix` | The letter that the IDs of such subjects start with. |
| | `asked_only` | The only indicators a subject of this kind is asked. Set for `person`. |
| | `shown_as` | Words the tool adds when it shows such a subject. A facility is shown as the loan under review. |
| `link-types.yaml` | `role_from`, `role_to` | The role the link gives to the subject at that end. |
| | `counts_for` | The kinds of subject the link must point at to give its role and to be asked its checks. `borrows`, `guarantees`, `supports` and `secures` count for a facility only. `owns` counts for a party or a group. |
| `source-kinds.yaml` | `slot` | The slot of the data room where such a document belongs. A kind without a slot is internal. |

The data room is an index. A deal folder keeps every document of the client in one folder, and lists them by these folders and slots.

## An indicator

An indicator is one claim: what the lender relies on, in a sentence that can turn out false. It holds the checks that try to disprove it.

| Field | Meaning |
|---|---|
| `id`, `title` | The ID never changes and is never used again for something else. |
| `pillar` | The pillar it belongs to. |
| `claim` | What the lender relies on. |
| `due_by` | The stage its checks are ideally answered by. A target, not a gate. |
| `applies_to` | Who or what it is asked about: `deal`, a role such as `borrower` or `financed_project`, a kind of subject such as `facility`, or a kind of link such as `guarantees`. |
| `applies_when` | Optional. It applies only when discovery has given one of these answers. Until then its checks wait. |
| `matters_more_when`, `matters_less_when` | Optional. Answers that raise or lower its importance, each with the reason. |
| `look_again_when` | Optional. A new source of a kind, or an answer, that should make someone look at the claim again. |
| `checks` | The checks. |

## A check

A check has one of three jobs.

- A **question** opens the topic or describes it. It tests nothing.
- A **test** can disprove the claim. It has an `assumption`, and `disproved_by` or `flag_when`.
- A **mitigant** is asked once a test has gone against the claim. It has `mitigant: true`.

| Field | Meaning |
|---|---|
| `id`, `question` | |
| `answer` | `yes_no`, `number`, `choice` or `text`. A `choice` has `options`, and `many: true` if several may apply. A `number` has a `unit`. |
| `assumption` | On a test or a mitigant: the statement the check tests. It is good news when it stands. |
| `disproved_by` | On a yes/no check: the answer that disproves the assumption, `yes` or `no`. |
| `flag_when` | On a number or a choice: the reference point, such as `above 20`, `is merchant` or `is poor or end_of_life`. An answer that meets it goes against the assumption. |
| `why` | Why the question is asked. With `flag_when`: why the reference point is where it is. |
| `mitigant` | `true` on a mitigant. |
| `due_by` | Only if it differs from the indicator's. |
| `applies_to` | Only if it differs from the indicator's. |
| `when` | Asked only when one of these conditions holds. |
| `after` | Asked once these checks have an answer. |
| `calls_for` | Answers that mean a link or a subject must be in the structure. |
| `look_in` | The data-room slots where the answer is usually found. |
| `evidence` | Kinds of source by strength: `best`, `supporting`, and `stated` for what someone said. |
| `ask` | How to put the question to the client. |
| `ask_whom` | `lender` if the question is about the lender itself. |
| `if_unknown` | What not knowing means. |
| `note` | A caution for whoever answers. |
| `leads_to` | An indicator to look at when the answer is as given, with the reason. |

A condition names a check and what its answer must be: `{check: OBS_REV_001, is: true}`, `{check: OBS_REV_001, answered: true}`, or `{check: OBS_DEBT_008, against: true}` for an answer that goes against that check's own assumption. Several conditions mean any of them.

A condition is looked up for the same party or link the check is asked about, and then for the deal. It never looks at another party.

`calls_for` is a list: `{is: true, link: [guarantees, supports]}` means that a yes calls for a link of one of these kinds, and `{is: greenfield, kind: project}` for a subject of that kind. `end: to` or `end: from` says which end of the link the party asked about must be: an owner is called for with `{is: company, link: [owns], end: to}`.

## Build it

```bash
python3 standard/build.py
```

This checks the standard and writes `bankability2/standard.json`, the one file the tool reads. It needs PyYAML. The tool does not.

It refuses a standard in which an ID is used twice, a reference points at nothing, an assumption has no answer that can go against it, a reference point has no reason, a condition names an answer the check cannot have, a link counts for a kind of subject that does not exist, or a kind of subject is asked only an indicator that does not exist.

```bash
python3 standard/build.py --site site
```

This also writes one Markdown page per indicator and per data-room folder, an index and the lists. A site generator can publish that folder as it is.

## Change it

Edit the YAML and build. Give a new check or indicator a new ID. An ID is never used again, and a check whose meaning changes gets a new one. Raise the version in `standard.yaml`.

A deal folder holds a copy of the standard it started with. The tool's `upgrade` command puts the newer standard into it and names the recorded answers whose check is gone.

An institution or a deal does not edit these files. It adjusts the standard in its own layer, which the tool applies on top: it can add checks, change a reference point, and switch a check off with a reason.

## Licence

MIT. See [LICENSE](../LICENSE).
