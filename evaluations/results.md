# Validation results — AIssociate 0.5.2

Checked locally on 14 October 2026. Version 0.5.2 refines instructions for the planned GPT-6.1 Sol pilot; runtime code is unchanged from 0.5.1. These results establish tool behaviour, not model improvement, financing judgment or writing quality.

| Check | Result |
|---|---|
| Current package checks | `uv run pytest -q tests/test_package.py -W error`: 20 passed, including both extracted workflows below |
| Prior 0.5.1 full regression suite | `uv run pytest -q -W error`: 293 passed; runtime unchanged in 0.5.2 |
| Extracted plugin and individual-skill ZIPs | Fresh processes outside repository imports: index → evidence-only bundle → reopen index → preflight → Word → full bundle → new evidence and protected revision |
| Prior 0.5.0 check: actual Microsoft Word 16.113.4 save | Old FP Assistant identity/record accepted; officer edited Summary in Word; the next revision preserved Summary and Recommendation while updating the untouched financial table |
| Partial changes and retry | Protected replacements returned as proposals with `partial` status; Word and bundle retries preserved identical bytes |
| Runtime diagnostics | Synthetic fixture helpers moved to development tests; the three `selftest` commands were removed. Use `--help`, `fp.py --version` and the installed workflow. |
| Package review | Both archives built; canonical references resolved into standalone companions; building left source files unchanged |
| Source checks | No broken relative Markdown links or confidential-name matches; `git diff --check` clean |

Version 0.5.2 adds brief stage confirmations, removes repeated instructions and a fixed drafting order, and clarifies reusable calculations and protection of approved assumptions. Independent review found no lost requirements or new approval gates. Unique skill/reference text fell from 5,731 to 5,698 words. No code, test cases, dependencies or model-routing layer were added.

The prior 0.5.1 cleanup removed 33.1% of instruction text and 166 runtime lines. Tests and fixture generators stay in development and are not loaded during FP work. All eight skills remain available. Actual Word was not rerun because document-processing behaviour was unchanged.

## What the work-PC pilot must prove

Follow [pilot-acceptance.md](pilot-acceptance.md) on one real deal. Still unverified:

- Cowork imports this exact package and invokes its scripts.
- An evidence index saved through the authorised connector can be retrieved in a fresh task, with accessible source references/extracts.
- The actual partially filled FP and separate template work within the writer's supported operations.
- The whole FP matches the examples, keeps internal tasks out, and reduces officer correction work.
- Actual recorded credits and elapsed time improve; tool counts are not cost measurements.

Missing headings and predefined-table population remain unsupported. Native Word checks used synthetic content and do not establish private-template acceptance or full visual quality. The reported failed pilot named installed version 1.3.0; parity with this repository was not established. Record the next run's version and script hashes.

Earlier synthetic skill runs are diagnostic history, not a model qualification or a substitute for this pilot. Keep real deal inputs and results in the approved work environment.
