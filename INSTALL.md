# Install AIssociate 0.5.3

Download `aissociate-0.5.3.zip` from the [0.5.3 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.5.3). Choose the plugin ZIP, not GitHub's source archive.

In an approved Copilot Cowork environment, use **Customize → Plugins → Upload plugin**, initially **Only you**. If only individual skill upload is available, extract `aissociate-individual-skills-0.5.3.zip` and upload its inner ZIPs. Tenant policy determines availability; see [Microsoft's guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-customize).

Disable the older FP Assistant plugin to avoid duplicate skills. Existing registers and Word records remain usable; do not rename their internal identifiers. Confirm all eight skills appear and ask FP Lead to run `python3 scripts/fp.py --version`. It must report `aissociate`, `0.5.3` and script hashes. Python 3.9+ is required.

Select **GPT-6.1 Sol** in Cowork for the next pilot. Keep the current/default reasoning setting initially; change it only if the real work warrants it. The plugin does not select the model or require higher effort. The [GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-sol#prompting-best-practices) is a starting point; much of its behavioural advice concerns Astra. Validate Sol in Cowork on the real task.

## Start small: a gap assessment

Use two short real documents about one topic: an interview note or transcript excerpt and a recent email or status note. Keep the total to a few pages and choose an approved test output folder. Excerpts test only their supplied scope. Paste this prompt, filling in the topic and folder:

> Use AIssociate for a gap assessment of [topic], using only these two documents. Confirm version 0.5.3 with the packaged version command. Use one task, with no extra agents, archive/email searches or FP drafting. Make one pass. Save located facts and material gaps using the packaged register tools in [folder]. Distinguish questions raised in the sources from gaps you identify, and unread material from genuinely missing information. Show at most five priority gaps with why they matter, what would resolve them, and whether the next step is internal or client-facing. Save and verify the evidence-only bundle; return working file links and stop. If tools or saving fail, report the failure without repair loops.

Check one fact's source, the relevance of the gaps, and whether the saved files open. Internal tasks must stay out of the client DDQ. Then start a fresh task:

> Reopen [saved register link]. Show one recorded fact with its source and any remaining priority gaps, at most two. Reuse the record; do not search, reread the documents, draft an FP or change files. Stop after this check.

If both steps work, follow the [whole-workflow pilot](https://github.com/rrecourt2/AIssociate/blob/main/evaluations/pilot-acceptance.md). Do not expand the test until saving and retrieval work.

The host must upload and independently retrieve outputs. A visible download does not prove the files reached the deal folder. Keep register, workbook, Analysis and internal support in authorised storage; review client-facing material before sharing.

The Word writer cannot add wholly absent headings or populate predefined financial tables. Probe the actual template first. If unsupported work is needed, retain proposed content and report the gap rather than rebuilding a blank document. If tools or file access fail, preserve the last usable version and report what remains unapplied.
