# AIssociate

An Investment Officer may spend months taking a transaction from screening to approval and contracting. The team checks financials, tests assumptions, negotiates terms and resolves questions. Much of this work ends up scattered across files, correspondence and successive drafts. When a new AI task starts, it can repeat the research, miss a decision or rely on a figure that has since changed.

AIssociate is a Copilot Cowork plugin for carrying this work forward. It maintains a deal record of facts, assumptions, calculations, decisions and open questions, linked to their sources and to each other. If a forecast changes, the record helps identify which conclusions and document sections need to be reassessed.

Documents become outputs of that record: a two-page opportunity scan, Clearance in Principle, Term Sheet, contracting support, Financial Proposal (FP) or external Investment Memorandum. Later, the same data could populate institutional systems through agreed field mappings and validation. That integration is outside this pilot.

## How the pilot works

1. **Record the evidence.** Deal Analyst records the purpose, sources and earlier decisions. Facts and assumptions stay distinct. Each source keeps its entity, period and version; originals stay in place.
2. **Analyse and identify gaps.** The relevant specialist methods are applied to the evidence. Deal Analyst reconciles the findings and identifies what still needs to be learned, why it matters and what would resolve it.
3. **Prepare the requested output.** Document Lead follows the Investment Officer's brief, template and examples, and writes in Word through Cowork. Reviewers challenge material conclusions and check presentation. Approval stays with authorised decision-makers.

The scope can be small. A new email may change one assumption and the conclusion that depends on it. The assistant should follow those links and update the affected work. A question about a deal need not turn into a full proposal.

For a short investigation, the result is an answer with source links, the saved `register.json` and a readable `Analysis.md` that lists each fact with a link to its original document. The next task resumes from that record. This pilot tests whether that continuity saves Investment Officer time and reduces repeated work.

## What's in the package

Eight skills cover evidence organisation, correspondence, annual reports, financial performance, repayment, drafting, challenge and presentation. A skill is a method applied in the main task; only independent reviews run as separate agents.

| Tool | Purpose |
|---|---|
| `register.py` | Keeps the deal record in `register.json`: sources, facts and assumptions, analysis and open questions, with their links. Regenerates `Analysis.md` and prints the client DDQ on request |
| `fin_table.py` | Transfers checked spread figures with entity, period, unit and cell references |

The tools use Python 3.9+ and the standard library. Cowork supplies the model, the authorised connectors, Word editing and the execution environment. No database service or hosted backend is required. Documents are revised as new versions with tracked changes; where Cowork cannot make an edit, the assistant returns a located proposal instead. The [writing guidance](shared/writing.md) keeps each output proportionate.

## Install and test

Download **`aissociate-0.6.0.zip`** from the [0.6.0 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.6.0). Follow [INSTALL.md](INSTALL.md) and the [whole-workflow pilot](evaluations/pilot-acceptance.md).

AIssociate replaces FP Assistant. Disable the older plugin to avoid duplicate skills. Document Lead and Template and Style Reviewer keep the commands `fp-lead` and `fp-template-style-reviewer`; existing registers remain usable.

## Data security

The plugin contains instructions and code, not deal data. Use approved accounts and storage. Host services process authorised files, and session copies may be created; the plugin does not control tenant access or retention. Treat the register and Analysis as internal. Share only reviewed, intended outputs. See the short [operating rules](shared/operating-rules.md).

## Development

```sh
uv run pytest -q
python3 scripts/package.py
python3 scripts/package.py --check
```

`skills/` holds only skill instructions. `shared/` and `tools/` hold one copy of each reference and processor. The builder makes self-contained upload ZIPs in `dist/`; it never writes generated copies back into the source tree. [Validation](evaluations/results.md).

To release, publish a GitHub release whose tag `vX.Y.Z` matches `plugin.json` (a pre-release while piloting); the release workflow builds both ZIPs and attaches them.

Client-prepared deal folders and reuse across lenders are future possibilities. If this pilot works, its evidence format could contribute to a wider **Bankability** standard.
