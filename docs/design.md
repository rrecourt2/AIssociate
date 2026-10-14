# AIssociate pilot design

Version 0.5.2. Build reusable deal evidence first, then analyse and write. Keep one local JSON master and one writer; the host provides authorised retrieval, model execution, separate tasks and remote delivery.

## Evidence → analysis → paper

**Intake:** Deal Analyst owns document organisation. Annual Report Review reads accounts and notes; Deal Updates processes emails/interviews; financial methods check material figures and debt. Each returns located claims and gaps. Sources are grouped logically, not moved. The index can be saved and resumed without a template or FP.

**Analysis:** Deal Analyst reconciles evidence, integrates specialist conclusions and assesses current relevance. Prior approval questions remain dated historical evidence until classified as resolved, continuing, superseded or unclear. Do not resurrect old work merely because its closure document is missing.

**Writing:** FP Lead uses selected claims, adopted analysis and current gaps. The template and approved examples are read before drafting. Separate reviewers assess the financing argument and presentation. Review material changes; use a fresh arbiter only for unresolved material disagreement. The officer retains recommendation and approval decisions.

No new agent framework is needed. Eight reusable skills support these stages; one financial context can use several methods. Indexing everything is not a prerequisite to useful work, but drafting must start from saved located evidence.

## Persistent records

`register.json` contains source versions, material claims, analysis, risks, open questions, findings and section links. `register.xlsx`, `Analysis.md` and the client DDQ are generated views. Claim support, attribution and qualifications remain distinct from judgments; originals remain authoritative.

New source versions preserve earlier evidence and mark linked work for recheck. New unlinked evidence still needs impact assessment. Reuse requires matching source bytes and reviewed scope. This uses explicit links, not a general knowledge graph or automatic archive ingestion.

Revision checks and request digests protect the single-writer workflow. Old registers migrate explicitly with a backup. Those checks are not cloud locks. A received answer still needs assessment before closure; only explicitly client-facing open/promised requests enter the DDQ.

## Execution and limits

Use `register.py` for the evidence stage and `fp.py` for preparation, protected Word builds and evidence/full-paper bundles. The [workflow contract](../shared/workflow-contract.md) defines the calls. Local bundles carry hashes and outstanding checks; verify the host's upload by reading the saved files back.

Word builds use a new copy and matching identity record, preserve officer edits and fixed content, and support interrupted-save recovery. Blocked replacements remain in proposals. Missing headings and predefined-table population remain unsupported. The actual template, layout and whole-paper quality require human review.

The package makes no network calls and stores no credentials. Host services may download and process documents in a session workspace; their access and retention rules still apply. Internal records may contain sensitive information. Keep them within their authorised audience; labels are not access controls. The [operating rules](../shared/operating-rules.md) cover handling.

## Pilot, not platform

The [acceptance test](../evaluations/pilot-acceptance.md) follows one real deal from index through FP and a subsequent update. Measure usefulness, correction time, elapsed time and actual recorded cost. Local tests only protect tool behaviour.

Client-managed folders, reuse in other systems and a common lender standard are later possibilities. No client portal, sharing service, automatic sending or performance guarantee is included.
