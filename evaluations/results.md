# Validation results — AIssociate 0.6.0

Checked locally on 18 October 2026. These checks establish tool behaviour, not model quality or tenant integration.

| Check | Result |
|---|---|
| Regression suite | `uv run pytest -q -W error`: 165 passed. The Word-writer tests left with the writer; two regression tests cover the register fixes below. |
| Register fixes | Correcting a source's title or link no longer marks its facts for recheck or reopens closed answers. An answer closed in the same change set as a correction to its claim is no longer silently reopened. |
| Readable record | `Analysis.md` lists every fact with a link to its original document and locator, and every source with its version, coverage and any replacement. A save writes only `register.json` and `Analysis.md`; the client DDQ is printed on request. |
| Extracted packages | Both the plugin ZIP and the individual-skill ZIPs create, save and resume an evidence record outside the repository. |

The package holds eight skills, six shared references and two scripts: 42 files and about 0.5 MB unpacked, down from 48 files and 0.8 MB.

Cowork displayed earlier releases with a leading 1: FP Assistant 0.3.0 as 1.3.0, and AIssociate 0.5.3 and 0.5.4 as 1.5.3 and 1.5.4. The pattern is consistent and points to Cowork's conversion on upload rather than a different build.

## Still for the work-PC pilot

Start with [save/resume](../INSTALL.md), then one requested [real workflow](pilot-acceptance.md). Check accessible sources, connected assumptions and gaps, cloud readback and preserved purpose. Measure Investment Officer correction effort and actual credits.

No live Cowork run took place here. Cowork's own Word editing (tracked changes, anchored comments, template tables) replaces the removed local writer and is untested for this plugin; check it on one real draft before a full FP. Whole-document quality and institutional system integration remain unvalidated.
