# Bankability 2

Bankability 2 is a memory for an investment deal. It keeps everything that is shared about a deal in one folder, in a form that a person and any AI assistant can pick up again later. It knows how the deal is structured, what is known, what is assumed and what is missing, and it says what to do and collect next.

It is made for a development finance institution and for an investment officer who works with an AI assistant. It is a rebuild from scratch of the first Bankability. It takes that project's standard and none of its code.

## Where it stands

Built on 14 November 2026. It has run on a made-up deal only.

- **Not yet tried in Microsoft Copilot Cowork.** How Cowork saves files and runs a script from a skill has to be tested in the tenant first.
- **Not yet used on a real deal.**
- **The standard needs a review by someone who does credit work**, above all the field that says which answer disproves an assumption. See [standard/CHANGES.md](standard/CHANGES.md).

## Try it

Python 3.9 or later. Nothing to install.

```bash
python3 -m bankability2 start "Cedar Foods" --name "Cedar Foods" --institution examples/institution.example.json
```

```bash
mkdir "Cedar Foods/Inbox" && cp examples/cedar-foods/documents/* "Cedar Foods/Inbox/"
```

```bash
python3 -m bankability2 file "Cedar Foods" examples/cedar-foods/changes/0-filing.json
```

```bash
for step in 1-teaser 2-annual-report 3-call; do python3 -m bankability2 add "Cedar Foods" examples/cedar-foods/changes/$step.json; done
```

```bash
python3 -m bankability2 status "Cedar Foods"
```

```bash
python3 -m bankability2 pages "Cedar Foods"
```

The deal is invented. The steps under `examples/cedar-foods/changes` are what an assistant would hand to the tool after reading a teaser, an annual report and the notes of a call.

## The parts

```text
bankability2/    the tool: six small modules, Python standard library only
standard/        the standard: lists, a data-room structure and 267 checks, as data
skill/           the instructions that tell an assistant how to work with the tool
examples/        a made-up deal, and an invented example of an institution's layer
tests/           three test files; one enforces the audit rules
docs/            the design and the audit note
```

| Part | What it does |
|---|---|
| **Standard** | Says what a deal folder holds and what must be known. An institution and a deal adjust it in their own layer. A build step turns it into pages a website can publish. See [standard/README.md](standard/README.md). |
| **Tool** | Records what the assistant hands it, and computes from the records: who holds which role, where each check stands, what is missing. It refuses only what is malformed. |
| **Skill** | Tells the assistant how to record, how to write the wiki pages and how to adjust the standard. See [skill/bankability-2/SKILL.md](skill/bankability-2/SKILL.md). |
| **Deal folder** | One per deal: a client folder that can be shared, and an internal folder with the memory, the wiki and the drafts. |

[docs/design.md](docs/design.md) explains the design.

## Kept simple

The tool is about 1,200 lines in seven files. These rules hold, and `tests/test_audit.py` fails if the code breaks one:

- Python standard library only.
- No network access, no starting of other programs, no `eval`, no reading of environment variables, no deleting.
- One module touches the disk. It writes through three functions, and each refuses a path outside the deal folder.
- No function longer than 100 lines. The whole tool stays under 2,000 lines.

[docs/audit.md](docs/audit.md) is the note for a security reviewer.

## Work on it

```bash
python3 -m unittest discover -s tests
```

```bash
python3 standard/build.py
```

```bash
python3 skill/package.py
```

The first runs the tests. The second rebuilds `bankability2/standard.json` after a change to the standard, and needs PyYAML. The third packs the skill with the tool into `dist/bankability-2.zip`.

## Licence

The standard is under Apache 2.0, as it was in the first Bankability. No licence has been chosen for the tool and the skill yet.
