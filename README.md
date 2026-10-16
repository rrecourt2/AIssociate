# AIssociate

AIssociate helps Investment Officers build a reusable deal record: what is known, assumed, still to be verified, and how it connects. Each material fact or conclusion retains its source and review status so work can continue across tasks.

Financial statements, contracts, interviews and emails often contain conflicting or outdated information. Asking AI to read the folder again for each draft costs time and loses earlier work. AIssociate links source evidence, assumptions, calculations, conclusions and open questions in one record.

That record supports investigations and documents: a two-page opportunity scan, Clearance in Principle, Term Sheet, contracting support, Financial Proposal (FP) or external Investment Memorandum. Later, its structured data could populate institutional systems through agreed field mappings and validation. No system integration is included in this pilot.

## How the pilot works

1. **Start or resume.** Deal Analyst retains the purpose and current direction, keeping facts, assumptions and decisions distinct. It indexes sources by type, entity, period and version. Originals stay in place.
2. **Check and analyse.** Financial specialists explain performance, debt and repayment. Deal Analyst reconciles claims and checks whether historical issues still matter. Ask for a standalone gap assessment: what remains unknown, why it matters and what would resolve it. No FP is required.
3. **Write when requested.** Document Lead uses the Investment Officer's brief to match purpose, audience and depth. Approved examples set the voice; the applicable template sets required content. Reviewers challenge material conclusions and check presentation. Approval stays with authorised decision-makers.

Use specialists only for relevant work. A new email should update affected facts and passages, not restart the archive review. This is a supervised pilot: faster drafting and lower cost are outcomes to measure, not promises.

For a small investigation, deliver a concise answer with original-source links and save the register plus its readable Analysis view in one approved location. Include other exports when useful. A later task resumes from the saved record, with its coverage and remaining gaps visible.

## What's in the package

Eight skills cover evidence organisation, correspondence, annual reports, financial performance, repayment, drafting, challenge and presentation. A skill is a method; it does not require its own agent on every run.

| Tool | Purpose |
|---|---|
| `register.py` | Stores linked sources, facts/assumptions, analysis and verification gaps in `register.json`; generates internal views and client DDQ |
| `fp.py` | Prepares supported Word inputs, builds protected revisions and bundles outputs for internal delivery |
| `fp_docx.py` | Preserves Investment Officer edits and protected content; retains unapplied revisions as proposals |
| `fin_table.py` | Transfers checked figures with entity, period, unit and cell references |

The tools use Python 3.9+ and the standard library. Development tests and synthetic fixtures stay outside the install package. The host supplies the model, authorised connectors and execution environment. No database service or hosted backend is required.

Term Sheets follow the supplied template. Negotiated edits use Track Changes and comments through a capable host Word tool, with specialist clearance. The Python writer preserves existing revisions/comments but cannot create them or fill arbitrary template structures. When unsupported, it returns located proposals. The [writing guidance](shared/writing.md) keeps each output proportionate.

## Install and test

Download **`aissociate-0.5.6.zip`** from the [0.5.6 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.5.6). Follow [INSTALL.md](INSTALL.md) and the [whole-workflow pilot](evaluations/pilot-acceptance.md).

AIssociate replaces FP Assistant. Disable the older plugin to avoid duplicate skills. Document Lead and Template and Style Reviewer retain the commands `fp-lead` and `fp-template-style-reviewer`; existing records and compatibility identifiers remain usable.

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
