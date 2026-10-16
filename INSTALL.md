# Install AIssociate 0.5.5

Download `aissociate-0.5.5.zip` from the [0.5.5 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.5.5). Choose the plugin ZIP, not GitHub's source archive.

In an approved Copilot Cowork environment, use **Customize → Plugins → Upload plugin**, initially **Only you**. If only individual skill upload is available, extract `aissociate-individual-skills-0.5.5.zip` and upload its inner ZIPs. Tenant policy determines availability; see [Microsoft's guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-customize).

Disable the older FP Assistant plugin to avoid duplicate skills. Existing registers and Word records remain usable; do not rename their internal identifiers. Confirm all eight skills appear and ask FP Lead to run `python3 scripts/fp.py --version`. It must report `aissociate`, `0.5.5` and script hashes. Python 3.9+ is required.

The ZIP manifest, processor and delivery manifest use one release version. If Cowork displays another version or the old plugin name, retrieve the installed manifest's path/content and the executed script's path/hashes. Compare those with the release; a chat-reported name alone does not identify the installed code.

Select **GPT-6.1 Sol** for the next pilot and keep the default reasoning setting initially. The plugin does not select the model or require higher effort.

## Start small: save and resume an investigation

Use two short real documents about one topic and an approved output folder. State why you are investigating, not just the question. Excerpts test only their supplied scope.

> Use AIssociate to investigate [question] because [purpose], using only these two documents. Use one task and one pass, without extra agents, searches or FP drafting. Give a concise answer with original-document links and at most three material gaps. Save the purpose, evidence, coverage and next decision through the register tools. Upload register.json and Analysis.md to [folder], read them back and return the saved links. Keep hypotheses distinct from agreed decisions. If tools or saving fail, report the failure and stop.

Check one source link and the saved Analysis. Then start a fresh task:

> Reopen [saved register link]. Briefly explain why we are investigating, what is decided versus hypothetical, what the record covers and the next decision. Show one fact with its original source. Do not search, reread the archive, draft or change files.

Finally, supply one short changed source or answer. Ask it to update only affected work, assess any reopened question and save back to the same location. Check that the purpose survives and an old answer is not silently reused.

If both steps work, follow the [whole-workflow pilot](https://github.com/rrecourt2/AIssociate/blob/main/evaluations/pilot-acceptance.md). Do not expand the test until saving and retrieval work.

The host must upload and independently retrieve outputs. A download link does not prove persistence in the deal folder. Keep internal records in approved storage; workbook and DDQ exports are optional for this small test.

The Word writer cannot add wholly absent headings or populate predefined financial tables. Probe the actual template first. If unsupported work is needed, retain proposed content and report the gap rather than rebuilding a blank document. If tools or file access fail, preserve the last usable version and report what remains unapplied.
