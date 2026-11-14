# Audit note

For whoever reviews Bankability 2 before it is used inside an institution. Version 0.1.0, 14 November 2026.

## What the tool is

A command-line program of about 1,200 lines of Python in seven files, in the folder `bankability2`. It uses the Python standard library only. It has no installer, no service, no background process and no configuration file.

It is run by a person or by an AI assistant, one command at a time, on one deal folder. Each command reads files in that folder, computes, prints text, and in some cases writes files in that folder. Then it ends.

## What it can touch

| | |
|---|---|
| **Reads** | Files in the deal folder. A JSON file handed to a command. The standard that ships with the tool, `bankability2/standard.json`. |
| **Writes** | Text files in the deal folder: the memory, the deal's layer of the standard, the manifest, the wiki pages. |
| **Moves** | Documents that are already in the deal folder, to their place in it (`file` command only). |
| **Never** | Opens a network connection. Starts another program. Reads an environment variable. Deletes a file. Runs text as code. Writes or moves anything outside the deal folder. |

All access to the disk is in one module, `files.py`, of about 100 lines. It changes the disk in three functions: `write`, `move` and `make_folder`. Each resolves its path and refuses it if it lies outside the deal folder.

## What it does not do

- **It does not read documents.** The AI assistant reads PDFs, Word files and emails with its own tools, under the host's own controls, and hands the tool what it learned. The tool computes a fingerprint (SHA-256) of a document when it is recorded.
- **It does not talk to an AI model.** It has no prompt and no key.
- **It does not decide.** It reports. It refuses an entry only when the entry is malformed, and then it writes nothing.

## How the rules are enforced

`tests/test_audit.py` reads the source of the tool and fails if:

- a module imports anything other than `argparse`, `datetime`, `hashlib`, `json`, `os`, `re` and `sys`;
- the code uses `eval`, `exec`, `compile`, `__import__` or `input`, or `os.environ`, `os.getenv`, `os.system`, `os.popen`, `os.remove`, `os.unlink`, `os.rmdir`, `os.rename` or `os.chmod`;
- any module other than `files.py` uses `open` or `os`;
- a function in `files.py` other than `write`, `move` and `make_folder` changes the disk, or one of those three does not check its path;
- the tool grows beyond seven files, 2,000 lines, or 100 lines in one function.

## The record of changes

The memory is one file, `Internal/memory/memory.json`. Every change goes through one function, `store.apply`, which applies a whole set of changes or none of it. Nothing is deleted: a record that is replaced stays, marked as replaced.

Each change adds an entry to a log in the same file. An entry holds who made the change, when, what was added, the earlier value of what was changed, a fingerprint of the memory after the change, and the fingerprint of the entry before it. The `check` command reports a broken chain and a memory that no longer matches its last entry.

Two limits:

- **The log shows tampering. It does not prevent it.** Someone who edits the file and recomputes the fingerprints leaves no trace in the file. Version history in OneDrive or SharePoint is the control for that.
- **"Who" is what the caller says.** The tool does not authenticate anyone.

## The data it holds

A deal folder holds confidential deal information, in plain files, wherever the institution puts the folder. The tool adds no protection of its own and removes none. Access is whatever the folder's access is.

The folder has two halves. `Client folder` holds what the client shared and can be passed on. `Internal` holds everything else and should not leave the deal team.

## How to verify a release

```bash
python3 -m unittest discover -s tests
```

This runs the audit rules above, runs the tool on a made-up deal, and checks that `bankability2/standard.json` is exactly what the standard's source builds to.

The packed skill, `dist/bankability-2.zip`, holds the same seven files, the standard, a short launcher (`scripts/bk2.py`) and the instructions for the assistant. Compare the seven files with `bankability2/`.

## Outside the tool

- **`standard/build.py`** builds the standard and needs PyYAML. It runs on the maintainer's machine, not at the institution.
- **`skill/package.py`** makes the zip.
- **The skill's instructions** are text for the assistant. They tell it to treat the text of a document as data and never as an instruction. That is guidance to a model, not a control.
