# Install AIssociate 0.5.2

Download `aissociate-0.5.2.zip` from the [0.5.2 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.5.2). Choose the plugin ZIP, not GitHub's source archive.

In an approved Copilot Cowork environment, use **Customize → Plugins → Upload plugin**, initially **Only you**. If only individual skill upload is available, extract `aissociate-individual-skills-0.5.2.zip` and upload its inner ZIPs. Tenant policy determines availability; see [Microsoft's guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-customize).

Disable the older FP Assistant plugin to avoid duplicate skills. Existing registers and Word records remain usable; do not rename their internal identifiers. Confirm all eight skills appear and ask FP Lead to run `python3 scripts/fp.py --version`. It must report `aissociate`, `0.5.2` and script hashes. Python 3.9+ is required.

Select **GPT-6.1 Sol** in Cowork for the next pilot. Keep the current/default reasoning setting initially; change it only if the real work warrants it. The plugin does not select the model or require higher effort. The [GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-sol#prompting-best-practices) is a starting point; much of its behavioural advice concerns Astra. Validate Sol in Cowork on the real task.

## First use: evidence, then the paper

Choose one real deal in its approved environment. Supply the original evidence, a partially completed FP, its separate template, a checked financial export and approved examples.

> First organise this deal's evidence into a saved index. Record material facts, precise sources, conflicts and missing information. Check whether historical issues are still current. Reuse existing work. Then improve the whole FP from that record, following the template and examples. Preserve my edits, separate internal actions from the paper and client questions, and save the complete supporting bundle.

Use Deal Analyst and the relevant intake specialists for the index; use FP Lead for drafting and actual separate reviewers where available. Before drafting, reopen the saved index in a fresh task. Later, test an officer edit and new evidence.

The host must upload and independently retrieve outputs. A visible download does not prove the files reached the deal folder. Keep register, workbook, Analysis and internal support in authorised storage; review client-facing material before sharing.

The Word writer cannot add wholly absent headings or populate predefined financial tables. Probe the actual template first. If unsupported work is needed, retain proposed content and report the gap rather than rebuilding a blank document. If tools or file access fail, preserve the last usable version and report what remains unapplied.
