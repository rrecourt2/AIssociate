# Audit note

For whoever reviews Bankability 2 before it is used inside an institution. Version 0.6.0, 17 November 2026.

## What the tool is

A command-line program of 2,206 lines of Python in seven files, in the folder `bankability2`. It uses the Python standard library only. It has no installer, no service, no background process and no configuration file. Beside the code the folder holds two files of data: the standard, and the template of the view for a browser.

It is run by a person or by an AI assistant, one command at a time, on one deal folder. Each command reads files in that folder, computes, prints text, and in some cases writes files in that folder. Then it ends.

## What it can touch

| | |
|---|---|
| **Reads** | Files in the deal folder. A JSON file handed to a command. The two files that ship with the tool: the standard, `bankability2/standard.json`, and the template `bankability2/wiki.html`. |
| **Writes** | Text files in the deal folder: the record, the standard and the deal's layer of it, the manifest and the index of the client folder, the wiki pages, the contents page and the view for a browser. `doctor` writes one line to a file of its own, to show that writing works. |
| **Moves** | Documents that are already in the deal folder, and a text extract made from one, to their place in it (`file` command only), one at a time. It never overwrites: a name that is taken is refused. If one is refused, the others are still moved and listed. The `upgrade` command moves the record of a folder made by an earlier version to its new place. |
| **Never** | Opens a network connection. Starts another program. Reads an environment variable. Deletes a file. Runs text as code. Writes or moves anything outside the deal folder. |

All access to the disk is in one module, `files.py`, of about 120 lines. It changes the disk in three functions: `write`, `move` and `make_folder`. Each resolves its path and refuses it if it lies outside the deal folder.

## What it does not do

- **It does not read documents.** The AI assistant reads PDFs, Word files and emails with its own tools, under the host's own controls, and hands the tool what it learned. The tool computes a fingerprint (SHA-256) of a document when it is recorded.
- **It does not talk to an AI model.** It has no prompt and no key.
- **It does not decide.** It reports. It refuses an entry only when the entry is malformed, and then it writes nothing.

## The view for a browser

The `pages` command writes `Internal/wiki/wiki.html`, so that a person can read the wiki in a browser. It is one HTML file that loads nothing from the network: no script, style, font or picture from elsewhere. Its template, `bankability2/wiki.html`, is about 300 lines of HTML, CSS and plain JavaScript. Python only puts the data into it: the pages, the index of the documents and the record, as JSON in which every `<` is escaped so that no text can end the script it sits in.

The script runs in the reader's browser, not in the tool. It renders the pages as text, and it escapes what it takes from the pages and the record before it shows it. A link to a document opens that file from the deal folder. The audit rules below read the Python only. A test checks that the template names no address and no outside file.

The file holds the whole record of the deal. It is internal, like the folder it sits in.

## How the rules are enforced

`tests/test_audit.py` reads the source of the tool and fails if:

- a module imports anything other than `argparse`, `datetime`, `hashlib`, `json`, `os`, `re` and `sys`, imports one of them under another name, or uses `from … import` for anything but the tool's own modules;
- the code uses `eval`, `exec`, `compile`, `__import__`, `input`, `getattr`, `setattr`, `delattr`, `globals`, `locals` or `vars`;
- any module other than `files.py` uses `open` or `os`;
- `files.py` uses anything of `os` other than `os.path`, `os.replace`, `os.makedirs`, `os.walk` and `os.sep`;
- a function in `files.py` other than `write`, `move` and `make_folder` changes the disk or opens a file for anything but reading, or one of those three does not check its path;
- the tool grows beyond seven Python files, 2,250 lines, or 100 lines in one function.

## The record of changes

The record of a deal is one file, `Internal/record/record.json`. The code calls it `memory` in the names of its variables. Every change goes through one function, `store.apply`, which applies a whole set of changes or none of it. Nothing is deleted: a record that is replaced stays, marked as replaced.

Each change adds an entry to a log in the same file. An entry holds who made the change, when, what was added, the earlier value of what was changed, a fingerprint of the record after the change, and the fingerprint of the entry before it. The `check` command reports a broken chain and a record that no longer matches its last entry. The next change made through the tool records that mismatch as an entry of its own, so it stays in the log.

Two limits:

- **The log shows tampering. It does not prevent it.** Someone who edits the file and recomputes the fingerprints leaves no trace in the file. Version history in OneDrive or SharePoint is the control for that.
- **"Who" is what the caller says.** The tool does not authenticate anyone.

## The data it holds

A deal folder holds confidential deal information, in plain files, wherever the institution puts the folder. The tool adds no protection of its own and removes none. Access is whatever the folder's access is.

The folder has two halves. `Client folder` holds what the client shared, in one folder with an index, and can be passed on. `Internal` holds everything else and should not leave the deal team.

## How to verify a release

```bash
python3 -m unittest discover -s tests
```

This runs the audit rules above, runs the tool on a made-up deal, and checks that `bankability2/standard.json` is exactly what the standard's source builds to.

The packed skill, `dist/bankability-2.zip`, holds the same seven Python files, the standard, the template of the browser view, a short launcher (`scripts/bk2.py`), the instructions for the assistant and the licence: 16 files. Compare the files under `scripts/bankability2` with `bankability2/`.

## Outside the tool

- **`standard/build.py`** builds the standard and needs PyYAML. It runs on the maintainer's machine, not at the institution.
- **`skill/package.py`** makes the zip.
- **The skill's instructions** are text for the assistant. They tell it to treat the text of a document as data and never as an instruction, to take a fact only from a source and never from its own pages or drafts, and to record a preference only when the analyst stated it. That is guidance to a model, not a control.
- **An assistant's own memory.** Some hosts let an assistant remember things between conversations. That memory lies outside the tool, which cannot see it or switch it off. In the hosts known today it belongs to the account or the project, not to the session, so whether it is on, and what it may hold, is a setting for the institution. The skill tells the assistant to keep what a deal contains in the deal folder, and to use a memory of its own only for how the analyst likes to work.
