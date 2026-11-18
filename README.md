# Bankability 2

Bankability 2 keeps the record of one investment deal for an analyst who works with an AI assistant. It holds every fact with its source and the words of that source, the checks of a standard for due diligence, and a wiki that a person reads in a browser. The assistant reads the documents and proposes what to record. The tool records it, links it, and says what is known, what is missing and what to collect next.

It is not an AI. It takes no decision, and it sends nothing anywhere.

## How it is used

1. The analyst creates a folder for the deal, with the tool.
2. The client's documents go into it. The tool files each in its place and keeps an index of what has arrived and what is still missing.
3. The assistant reads a document and hands the tool what it found: each fact with its source and a quotation. The tool records it, or refuses it if it is malformed.
4. The tool reports where each check of the standard stands, and what to ask or collect next.
5. The assistant writes the pages of the wiki. The tool adds the parts it keeps and builds a view for a browser.
6. Before work goes on, the tool checks the record: every quotation against its source, and the log of changes.

A deal folder looks like this:

```text
Cedar Foods/
├── Wiki.html           opens the wiki in a browser
├── Client folder/      the documents the client shared, with an index; can be handed on
└── Internal/           stays with the deal team
    ├── sources/        calls, notes, public sources, and text extracts of the originals
    ├── record/         record.json, and the standard this deal uses
    ├── wiki/           the pages, and the view for a browser
    └── outputs/        drafts
```

## For those who approve software

- **Where it runs.** On the user's machine, or inside the institution's own environment, beside the deal folder. It is run one command at a time and then ends. It has no server and no background process.
- **No network.** The tool opens no network connection. The view for a browser loads no script, style, font or picture from elsewhere.
- **What it needs.** Python 3.9 or later and nothing else: the standard library only, no installation, no service, no configuration file.
- **What it touches.** It reads and writes only inside the deal folder, and refuses any path that leads out of it. It does not delete. It moves a document only within the folder, and refuses to move one onto a name that is taken, so no document is overwritten.
- **Sources.** Every fact carries its source. A fact from a document carries the words of that document. The tool compares each quotation with the text of the source itself, by plain text comparison. No model does this.
- **Changes.** Every change is an entry in a log inside the record: who, when, what, and the earlier value. Each entry carries a fingerprint of the one before. The `check` command reports a record that was altered afterwards outside the tool. The log shows such a change. It does not prevent it, and "who" is what the caller states.
- **The assistant.** The assistant is the institution's own, and its choice. It reads the documents under the host's own controls. The tool does not talk to a model, and neither holds nor needs a key.
- **The institution's layer.** What the institution adds, such as its own stages, its own checks and the fields of its systems, sits in its own file inside its own environment. `start` copies it into a deal when it is named.
- **Size and tests.** The tool is about 2,400 lines of Python in seven files. `tests/test_audit.py` reads the code and fails if it imports anything outside a short list, uses the network, starts another program, reads an environment variable, runs text as code, touches the disk outside one module, or grows beyond 2,500 lines.
- **Licence.** MIT.

The full note for a reviewer, with the limits, is [docs/audit.md](docs/audit.md).

## Try it

From the top of this repository. Nothing to install. The deal is invented. The files under `examples/cedar-foods/changes` are what an assistant would hand to the tool after reading a teaser, an annual report and the notes of a call.

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
cp -r examples/cedar-foods/wiki/. "Cedar Foods/Internal/wiki/" && python3 -m bankability2 pages "Cedar Foods"
```

```bash
python3 -m bankability2 check "Cedar Foods"
```

What to see:

- **`file`** puts the teaser and the annual report into `Client folder`, with an index, and the notes of the call into `Internal/sources`.
- **`add`** prints the ID it gave to each new record, and how many checks moved.
- **`status`** shows the structure of the deal, what changed, and where the claims stand. Two are challenged: the margin fell, and the loan is in euros while all sales are in shillings. It lists what is missing and the checks to answer next.
- **`pages`** copies in the pages an assistant wrote for this deal, fills in the parts the tool keeps, and writes `Wiki.html`. Open it in a browser to read the wiki, the documents and the fact behind each citation. The last entry in its menu lists every check with its state.
- **`check`** prints `No problems found.` It has compared every quotation with its source.

`show "Cedar Foods" facts` lists every current fact, and `show "Cedar Foods" sample` gives ten to compare with their documents.

The tests run with `python3 -m unittest discover -s tests`.

## Where it stands

It has been tried on two real companies, in five rounds, from public documents only, by assistants that had nothing but the guide and the tool. It has not yet been used on a live deal with an analyst. It has not yet been run inside Microsoft Copilot Cowork, the first host it is meant for: how Cowork runs a script from a skill and saves files has to be tested in the institution's own tenant. The standard still needs a review by someone who does credit work. What each round showed is in [standard/CHANGES.md](standard/CHANGES.md).

## Read more

- [skill/bankability-2/SKILL.md](skill/bankability-2/SKILL.md): the guide for the assistant, on how to record, write the wiki and draft.
- [standard/README.md](standard/README.md): the standard, with 70 claims and their checks, as data. An institution and a deal adjust it in their own layer. [standard/FRAMEWORK.md](standard/FRAMEWORK.md) explains how it is built.
- [docs/design.md](docs/design.md): the design.
- [docs/audit.md](docs/audit.md): the note for a security reviewer.

A deal folder made by an earlier version is brought in line with `python3 -m bankability2 upgrade "<deal folder>"`. After a change to the standard, `python3 standard/build.py` rebuilds `bankability2/standard.json` and needs PyYAML. `python3 skill/package.py` packs the guide with the tool into `dist/bankability-2.zip`.

## Licence

MIT, for the standard, the tool and the guide. See [LICENSE](LICENSE).
