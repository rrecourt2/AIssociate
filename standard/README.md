# The Bankability Standard

The standard says what a deal folder holds and what must be known about a deal. It is data only: lists, a data-room structure and checks. No meaning lives in code.

Version 3.0.0 holds 50 indicators with 267 checks, a data room of 10 folders with 64 slots, and 79 kinds of source. It continues the first Bankability's standard, version 2.0.0. [CHANGES.md](CHANGES.md) lists what changed.

## The files

```text
standard/
├── standard.yaml           name and version
├── lists/
│   ├── stages.yaml         the stages of a deal, and the evidence that is ideal at each
│   ├── workstreams.yaml    the eight groups of indicators
│   ├── subject-kinds.yaml  party, facility, contract, asset, project, group
│   ├── link-types.yaml     how subjects are linked, and the role a link gives
│   └── source-kinds.yaml   kinds of document, call and note
├── dataroom.yaml           folders, sub-folders and slots
├── indicators/             one file per indicator
└── build.py                checks the standard and builds it
```

## An indicator

An indicator is one topic, such as revenue or sanctions. It holds the checks for that topic.

| Field | Meaning |
|---|---|
| `id`, `title` | The ID never changes and is never used again for something else. |
| `workstream` | The group it belongs to. |
| `due_by` | The stage its checks are ideally answered by. A target, not a gate. |
| `applies_to` | Who or what it is asked about: `deal`, a role such as `borrower`, a kind of subject such as `facility`, or a kind of link such as `guarantees`. |
| `applies_when` | Optional. It applies only when one of these answers is given. |
| `why_it_matters` | Optional. Why a lender or an equity investor cares. |
| `matters_more_when`, `matters_less_when` | Optional. Answers that raise or lower its importance, each with the reason. |
| `risk`, `mitigant` | Optional. A statement of the risk and of what mitigates it, each with the checks that test it. |
| `look_again_when` | Optional. What should make someone look at the topic again. |
| `checks` | The checks. |

## A check

A check is one question. Most checks test a stated assumption.

| Field | Meaning |
|---|---|
| `id`, `question` | |
| `answer` | `yes_no`, `number`, `choice` or `text`. A `choice` has `options`, and `many: true` if several may apply. A `number` has a `unit`. |
| `assumption` | The statement the check tests. |
| `disproved_by` | For a yes/no check: the answer that disproves the assumption, `yes` or `no`. |
| `flag_when` | For other checks: the standard's reference point, such as `above 20` or `is single_source`. An answer that meets it speaks against the assumption. |
| `why` | Why the question is asked, where it tests no assumption. |
| `due_by` | Only if it differs from the indicator's. |
| `applies_to` | Only if it differs from the indicator's. |
| `after` | Checks that are answered first. |
| `when` | Asked only when one of these answers is given. |
| `look_in` | The data-room slots where the answer is usually found. |
| `evidence` | Kinds of source by strength: `best`, `supporting`, and `stated` for what someone said. |
| `ask` | How to put the question to the client. |
| `ask_whom` | `lender` if the question is about the lender itself. |
| `if_unknown` | What not knowing means. |
| `note` | A caution for whoever answers. |
| `leads_to` | An indicator to look at when the answer is as given, with the reason. |

A condition in `when`, `applies_when` and the like names a check and the answer: `{check: OBS_REV_001, is: true}`.

## Build it

```bash
python3 standard/build.py
```

This checks that every ID is unique and that every reference points at something that exists, and writes `bankability2/standard.json`, the one file the tool reads. It needs PyYAML. The tool does not.

```bash
python3 standard/build.py --site site
```

This also writes one Markdown page per indicator and per data-room folder, an index and the lists. A site generator can publish that folder as it is.

## Change it

Edit the YAML and build. Give a new check or indicator a new ID. Raise the version in `standard.yaml`.

An institution or a deal does not edit these files. It adjusts the standard in its own layer, which the tool applies on top.

## Licence

Apache 2.0. See [LICENSE](LICENSE).
