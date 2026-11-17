# Bankability 2

Bankability 2 keeps the record of an investment deal. It keeps everything that is shared about a deal in one folder, in a form that a person and any AI assistant can pick up again later. It knows how the deal is structured, what is known, what is assumed and what is missing, and it says what to do and collect next.

It is made for a development finance institution and for an investment analyst who works with an AI assistant. It is a rebuild from scratch of the first Bankability. It takes that project's standard and none of its code.

## Where it stands

Built on 14 November 2026, and repaired on 15 and 16 November after three rounds of a trial.

- **Tried three times on a real company**, from its public documents only, by assistants that had nothing but the skill and the tool. The record they built was accurate, and each assistant could pick the deal up where the last had stopped. The first round showed that the tool asked too much, and asked some of it of the wrong subjects. The second, with the repaired tool, asked about half as much, kept the original documents beside their extracts and gave a wiki that describes the business before it measures it. The third widened the wiki to the company's history, its market and its country, assessed where the decisions of a subsidiary are taken, and acted on a credit colleague's review of the open checks. An independent reader then judged about two in three of the checks still open to be material. What each round showed and what changed is in [standard/CHANGES.md](standard/CHANGES.md). The trial itself is private and not in this repository.
- **Not yet tried in Microsoft Copilot Cowork.** How Cowork saves files and runs a script from a skill has to be tested in the tenant first.
- **Not yet used on a live deal with an analyst.**
- **The standard was rebuilt on a new framework** (version 4): it starts from how the loan is repaid, keeps the deal, each party, the links and the facility apart, and puts every check under a claim that can turn out false. See [standard/FRAMEWORK.md](standard/FRAMEWORK.md).
- **The standard needs a review by someone who does credit work.** Blind judges agreed with the direction of its tests, and two reviewers' findings are applied. Its reference points and its strictness remain open questions, listed in [standard/CHANGES.md](standard/CHANGES.md).

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

```bash
cp -r examples/cedar-foods/wiki/. "Cedar Foods/Internal/wiki/" && python3 -m bankability2 pages "Cedar Foods"
```

```bash
python3 -m bankability2 check "Cedar Foods"
```

The deal is invented. The steps under `examples/cedar-foods/changes` are what an assistant would hand to the tool after reading a teaser, an annual report and the notes of a call.

- **`file`** puts the two documents of the client into `Cedar Foods/Client folder` and writes `index.md` there: the documents by the folders of the data room, and the slots that are still empty. The notes of the call go to `Cedar Foods/Internal/sources`.
- **`add`** prints the ID it gave to each new record.
- **`status`** shows where the claims stand in each pillar. Two are challenged: the margin fell, and the loan is in euros while all sales are in shillings. It lists what the answers call for and the structure lacks (the suppliers, the lenders, a guarantor with a name), one gap with an agreed action, and the checks to answer next. `status "Cedar Foods" --for P-001` keeps to the borrower.
- **`pages`** creates three pages for an assistant to write: the deal, the borrower and the project the loan pays for. The line after it copies in the pages an assistant wrote for this deal, from `examples/cedar-foods/wiki`. `pages` then fills in the parts that the tool keeps and writes `Cedar Foods/Internal/wiki/wiki.html`. Open that file in a browser to read the wiki, the documents and the facts behind each citation.
- **`check`** finds nothing wrong.

More to look at: `show "Cedar Foods" claims` lists every claim by pillar, `show "Cedar Foods" facts` every current fact, `show "Cedar Foods" facts S-002` the facts from one source, and `show "Cedar Foods" kinds` the kinds of source, subject and link.

## The parts

```text
bankability2/    the tool: seven small Python files, standard library only, and the template of the view for a browser
standard/        the standard: a framework, lists, a data-room structure and 551 checks under 70 claims, as data
skill/           the instructions that tell an assistant how to work with the tool
examples/        a made-up deal, and an invented example of an institution's layer
tests/           three test files; one enforces the audit rules
docs/            the design and the audit note
```

| Part | What it does |
|---|---|
| **Standard** | Says what a deal folder holds and what must be known. An institution and a deal adjust it in their own layer. A build step turns it into pages a website can publish. See [standard/README.md](standard/README.md). |
| **Tool** | Records what the assistant hands it, and computes from the record: who holds which role, where each claim and each check stands, what is missing. It refuses only what is malformed. |
| **Skill** | Tells the assistant how to record, how to write the wiki pages, how to adjust the standard and how to draft. See [skill/bankability-2/SKILL.md](skill/bankability-2/SKILL.md). |
| **Deal folder** | One per deal: a client folder that can be shared, with every document in it and an index, and an internal folder with the record, the wiki and the drafts. |

The record holds what is known: exact, sourced and written only by the tool. The wiki holds what is understood, and cites the record. The standard is a backbone for the analysis, not a script: it says where to look and keeps the record honest.

[docs/design.md](docs/design.md) explains the design.

## Kept simple

The tool is under 2,000 lines of Python in seven files. These rules hold, and `tests/test_audit.py` fails if the code breaks one:

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

A deal folder made by an earlier version is brought in line with `python3 -m bankability2 upgrade "<deal folder>"`.

## Licence

MIT, for the standard, the tool and the skill. See [LICENSE](LICENSE).
