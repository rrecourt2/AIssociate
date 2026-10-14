# AIssociate

AIssociate helps a deal team turn scattered documents into a reusable evidence index, then use that record to write a financing proposal (FP).

Financial statements, contracts, interviews and emails often contain conflicting or outdated information. Asking AI to read the folder again for each draft costs time and loses earlier work. AIssociate stores material facts with their sources, review status and open questions so the next task can continue from them.

## How the pilot works

1. **Organise evidence.** Deal Analyst indexes sources by type, entity, period and version. Report-reading and correspondence specialists extract located facts and gaps. Originals stay in place.
2. **Check and analyse.** Financial specialists explain performance, debt and repayment. Deal Analyst reconciles claims and checks whether historical issues still matter. The index can be used and saved before any FP exists.
3. **Write and review.** FP Lead selects the financing argument from that record. Approved examples set the voice; the template sets required content. Separate reviewers challenge the case and check presentation. The officer decides.

Use specialists only for relevant work. A new email should update affected facts and passages, not restart the archive review. This is a supervised pilot: faster drafting and lower cost are outcomes to measure, not promises.

## What's in the package

Eight skills cover evidence organisation, correspondence, annual reports, financial performance, repayment, drafting, challenge and presentation. A skill is a method; it does not require its own agent on every run.

| Tool | Purpose |
|---|---|
| `register.py` | Stores sources, claims, analysis and gaps in `register.json`; generates an internal workbook, Analysis and client DDQ |
| `fp.py` | Prepares Word inputs, builds controlled revisions and bundles evidence or the full paper for delivery |
| `fp_docx.py` | Preserves officer edits and protected content; retains unapplied revisions as proposals |
| `fin_table.py` | Transfers checked figures with entity, period, unit and cell references |

The tools use Python 3.9+ and the standard library. Development tests and synthetic fixtures stay outside the install package. The host supplies the model, authorised connectors and execution environment. No database service or hosted backend is required.

## Install and test

Download **`aissociate-0.5.2.zip`** from the [0.5.2 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.5.2). Follow [INSTALL.md](INSTALL.md) and the [whole-workflow pilot](evaluations/pilot-acceptance.md).

AIssociate replaces FP Assistant as the package and repository name. Keep existing deal registers and Word records; disable the older plugin to avoid duplicate skills. Word compatibility identifiers are unchanged.

## Data security

The plugin contains instructions and code, not deal data. Use approved accounts and storage. Host services process authorised files, and session copies may be created; the plugin does not control tenant access or retention. Treat the index and analysis bundle as internal. Share only reviewed, intended outputs. See the short [operating rules](shared/operating-rules.md).

## Development

```sh
uv run pytest -q
python3 scripts/package.py
python3 scripts/package.py --check
```

`skills/` holds only skill instructions. `shared/` and `tools/` hold one copy of each reference and processor. The builder makes self-contained upload ZIPs in `dist/`; it never writes generated copies back into the source tree. [Design](docs/design.md) · [Validation](evaluations/results.md).

Client-prepared deal folders and reuse across lenders are future possibilities. If this pilot works, its evidence format could contribute to a wider **Bankability** standard.
