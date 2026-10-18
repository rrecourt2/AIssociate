# Install AIssociate 0.6.0

Download `aissociate-0.6.0.zip` from the [0.6.0 pilot release](https://github.com/rrecourt2/AIssociate/releases/tag/v0.6.0). Choose the plugin ZIP, not GitHub's source archive.

In an approved Copilot Cowork environment, use **Customize → Plugins → Upload plugin**, initially **Only you**; Cowork converts the package on upload. If only individual skill upload is available, extract `aissociate-individual-skills-0.6.0.zip` and upload its inner ZIPs. Tenant policy determines availability; see [Microsoft's guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-customize).

Disable FP Assistant and any earlier AIssociate upload to avoid duplicate skills, then confirm that all eight skills appear. Cowork has shown earlier releases with a leading 1 (0.5.4 as 1.5.4), so 0.6.0 may appear as 1.6.0; that is the same release. The register needs Python 3.9+ in Cowork's workspace.

Select **GPT-6.1 Sol** and keep the default reasoning setting initially. The plugin does not select the model or require higher effort.

Saved deal folders from earlier versions may contain `register.xlsx` and `Client-DDQ.md`. These are no longer updated; delete them so that they are not mistaken for the record. Existing `register.json` files remain usable.

## Start small: save and resume an investigation

Use two short real documents about one topic and an approved output folder. State why you are investigating, not just the question. Excerpts test only their supplied scope.

> Use AIssociate to investigate [question] because [purpose], using only these two documents. Use one task and one pass, without extra agents, searches or FP drafting. Give a concise answer with original-document links and at most three material gaps. Save the purpose, evidence, coverage and next decision through the register tools. Upload register.json and Analysis.md to [folder], read them back and return the saved links. Keep hypotheses distinct from agreed decisions. If tools or saving fail, report the failure and stop.

Check one source link in the saved Analysis. Then start a fresh task:

> Reopen [saved register link]. Briefly explain why we are investigating, what is decided versus hypothetical, what the record covers and the next decision. Show one fact with its original source. Do not search, reread the archive, draft or change files.

Finally, supply one short changed source or answer. Ask it to update only affected work, assess any reopened question and save back to the same location. Check that the purpose survives and an old answer is not silently reused.

If these steps work, follow the [whole-workflow pilot](https://github.com/rrecourt2/AIssociate/blob/main/evaluations/pilot-acceptance.md). Do not expand the test until saving and retrieval work. A download link does not prove that a file was saved in the deal folder; the assistant must reopen what it saved.

## Documents

Document Lead edits Word through Cowork's own tools. For the first document test, revise one section of a real draft: expect a new version with tracked changes and your edits intact. For a Term Sheet or contract, request one tracked clause edit with an anchored comment, then reopen the file in Word and check both. If Cowork cannot track a change, expect a located proposal and a stated limitation, not an untracked replacement.
