"""The commands. Run as: python -m bankability2 <command> <deal folder>"""
import argparse
import datetime
import json
import re
import sys

from . import __version__, assess, files, pages, standard, store
from .files import Refused


def load(deal):
    memory = files.read_json(deal, files.MEMORY)
    if memory is None:
        raise Refused(f"{deal} holds no deal. Start one with: start <folder> --name <name>")
    return memory, standard.effective(deal)


def given(path):
    """The JSON handed to a command: a file, or standard input when the path is "-"."""
    return json.load(sys.stdin) if path == "-" else files.read_input(path)


def safe(name):
    """A folder name that Windows and OneDrive accept."""
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()


def start(args):
    if files.read(args.deal, files.MEMORY) is not None:
        raise Refused(f"{args.deal} already holds a deal")
    std = files.packaged_standard()
    if args.stage not in [stage["id"] for stage in std["stages"]]:
        raise Refused(f"unknown stage {args.stage!r}")
    for folder in std["dataroom"]["folders"]:
        files.make_folder(args.deal, f"{files.CLIENT}/{folder['id']} {safe(folder['title'])}")
    for name in files.INTERNAL_FOLDERS:
        files.make_folder(args.deal, f"Internal/{name}")
    files.write_json(args.deal, files.BASE, std)
    if args.institution:
        files.write_json(args.deal, files.INSTITUTION, files.read_input(args.institution))
    files.write_json(args.deal, files.MANIFEST, {"documents": []})
    files.write_json(args.deal, files.MEMORY, store.new(args.name, args.stage, std["version"]))
    print(f"Started {args.name} at stage {args.stage}, with standard {std['version']}.")


def group(title, lines, limit):
    print(f"\n### {title} ({len(lines)})")
    for line in lines[:limit]:
        print(f"- {line}")
    if limit and len(lines) > limit:
        print(f"- and {len(lines) - limit} more: use --all")


def status(args):
    memory, std = load(args.deal)
    rows = assess.assess(memory, std)
    listed = files.read_json(args.deal, files.MANIFEST, {"documents": []})["documents"]
    todo = assess.next_list(memory, std, rows, in_folder={doc["slot"] for doc in listed})
    if args.json:
        print(json.dumps({"deal": memory["deal"], "revision": store.revision(memory), "checks": rows,
                          "claims": assess.claims(rows, memory, std), "next": todo}, indent=1, ensure_ascii=False))
        return
    held, deal = assess.roles(memory, std), memory["deal"]
    titles = std["stage_titles"]
    print(f"# {deal['name']}: stage {titles[deal['stage']]}, revision {store.revision(memory)}, standard {deal['standard']}")
    print("\n## Structure")
    for sid, subject in memory["subjects"].items():
        print(f"- {sid} {subject.get('name') or 'not yet named'}: {subject['kind']}"
              + "".join(f", {role}" for role in sorted(held.get(sid, ()))))
    for lid, link in memory["links"].items():
        print(f"- {lid} {pages.name_of(lid, memory)} ({link['state']})")
    print("\n## What changed")
    entries = memory["log"][-5:] if args.since is None else [entry for entry in memory["log"] if entry["n"] > args.since]
    for entry in entries:
        touched = len(entry["added"]) + len(entry["changed"])
        print(f"- {entry['n']}. {entry['at'][:10]} {entry['by']}: {entry['note']} ({touched} records)")
    counts = {}
    for row in rows:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    print("\n## Next\n\nChecks: " + (", ".join(f"{count} {state}" for state, count in counts.items()) or "none apply yet") + ".")
    found = assess.claims(rows, memory, std)
    print("\n## Where the claims stand\n")
    for pillar in std["pillars"]:
        counts = assess.view(found, std)[pillar["id"]]
        print(f"- {pillar['title']}: " + (", ".join(f"{count} {name}" for name, count in zip(assess.VERDICTS, counts) if count)
                                          or "no claim applies yet"))
    limit = None if args.all else 15
    urgent = [line[2:] for line in pages.claim_lines(found, memory, std) if not line.startswith("- **Claims:**")]
    group("Claims that are challenged, contested or to look at again", urgent, limit)
    group("Structure still open", todo["structure"], limit)
    lines = []
    for row in todo["checks"]:
        waits = f"; {row['unlocks']} checks wait on it" if row["unlocks"] else ""
        state = ", ".join([row["state"], *row["flags"]])
        lines.append(f"{std['checks'][row['check']]['question']} ({pages.name_of(row['for'], memory)}; "
                     f"ideally by {titles[row['due_by']]}; {state}{waits}) [{row['check']}]")
    group("Checks to answer or strengthen", lines, limit)
    group("Gaps with an agreed action", todo["actions"], limit)
    group("Documents not in the folder", [f"{doc['slot']} {doc['title']}: {doc['why']}" for doc in todo["documents"]], limit)
    group("Questions without an answer", [f"{q['id']} to {q['asked_of']}, asked {q.get('asked', 'no date')}: {q['text']}"
                                         for q in todo["questions"]], limit)
    group("Facts that rest on a replaced source", todo["replaced"], limit)
    group("System fields without a value", todo["fields"], limit)
    if std["notes"]:
        group("Notes on the standard", std["notes"], limit)


def add(args):
    memory, std = load(args.deal)
    change = given(args.changes)
    if not isinstance(change, dict):
        raise Refused("a set of changes is one JSON object")
    missing = []
    sources = change.get("sources", [])
    for source in sources if isinstance(sources, list) else []:
        if isinstance(source, dict) and source.get("where") and "id" not in source:
            mark = files.fingerprint(args.deal, source["where"])
            if mark:
                source.setdefault("fingerprint", mark)
            else:
                missing.append(source["where"])
    try:
        entry = store.apply(memory, change, std)
    except (TypeError, KeyError, AttributeError) as error:  # nothing is written before apply returns
        raise Refused(f"Nothing was recorded. A value in this set of changes has the wrong shape: {error!r}")
    if entry is None:
        print("Already recorded: this set of changes was applied before.")
        return
    files.write_json(args.deal, files.MEMORY, memory)
    print(f"Recorded as revision {entry['n']}. Added: {', '.join(entry['added']) or 'nothing'}. "
          f"Changed: {', '.join(entry['changed']) or 'nothing'}.")
    for path in missing:
        print(f"Note: {path} was not found in this copy of the folder, so it has no fingerprint.")


def summary(record):
    for key in ("title", "statement", "name", "decision", "text", "type", "note"):
        if record.get(key):
            return str(record[key])
    return ""


def show(args):
    memory, std = load(args.deal)
    what, rows = " ".join(args.what), assess.assess(memory, std)
    if what == "log":
        for entry in memory["log"][-30:]:
            print(f"{entry['n']}. {entry['at']} {entry['by']}: {entry['note']} "
                  f"added {entry['added']} changed {list(entry['changed'])}")
    elif what == "sheet":
        print("\n".join(assess.sheet(memory, std)) or "The institution's layer lists no systems.")
    elif what in std["checks"] or what in std["by_id"]:
        entry = std["checks"].get(what) or std["by_id"][what]
        print(json.dumps({key: value for key, value in entry.items() if key != "checks"}, indent=1, ensure_ascii=False))
        print("\n".join(pages.check_lines([row for row in rows if what in (row["check"], row["indicator"])], memory, std)))
    elif store.table_of(memory, what):
        print(json.dumps(memory[store.table_of(memory, what)][what], indent=1, ensure_ascii=False))
        print("\nUsed by:")
        for table in store.TABLES:
            for rid, record in memory[table].items():
                if rid != what and what in json.dumps(record):
                    print(f"- {rid}: {summary(record)}")
        for path, text in pages.all_pages(args.deal).items():
            if what in pages.own_text(text):
                print(f"- page {path}")
        used = [row for row in rows if row["for"] == what or what in row.get("facts", [])]
        if used:
            print("\n" + "\n".join(pages.check_lines([row for row in used if row["state"] != "not relevant"], memory, std)))
    else:
        hits = [f"- {rid}: {summary(record)}" for table in store.TABLES for rid, record in memory[table].items()
                if what.lower() in json.dumps(record, ensure_ascii=False).lower()]
        print("\n".join(hits) or "Nothing found.")


def refresh(args):
    memory, std = load(args.deal)
    rows = assess.assess(memory, std)
    created = pages.refresh(args.deal, memory, std, rows, assess.roles(memory, std))
    print(f"The pages are up to date. New pages to write: {', '.join(created) or 'none'}.")


def file_problems(deal, memory):
    """Documents that are missing, changed or not listed. Skipped where the documents are not present."""
    listed = {doc["path"]: doc for doc in files.read_json(deal, files.MANIFEST, {"documents": []})["documents"]}
    present = [path for path in files.listing(deal, files.CLIENT) if path != files.MANIFEST]
    wheres = [source["where"] for source in memory["sources"].values() if source.get("where")]
    if (listed or wheres) and not present and not any(files.fingerprint(deal, where) for where in wheres):
        return ["The documents are not in this copy of the folder, so files were not checked."]
    found = [f"{path}: in the client folder but not in the manifest" for path in present if path not in listed]
    for path, doc in listed.items():
        mark = files.fingerprint(deal, path)
        if mark != doc["fingerprint"]:
            found.append(f"{path}: {'missing' if mark is None else 'changed since it was filed'}")
    for sid, source in memory["sources"].items():
        mark = files.fingerprint(deal, source["where"]) if source.get("where") else None
        if source.get("where") and mark is None:
            found.append(f"{sid}: {source['where']} was not found in this copy of the folder")
        elif mark and source.get("fingerprint") not in (None, mark):
            found.append(f"{sid}: {source['where']} changed since it was recorded")
    return found


def check(args):
    memory, std = load(args.deal)
    found = store.verify(memory) + std["notes"] + file_problems(args.deal, memory) + pages.problems(args.deal, memory)
    found += [f"{did}: the decision names no fact it rests on" for did, decision in memory["decisions"].items()
              if not decision.get("rests_on")]
    print("\n".join(f"- {line}" for line in found) or "No problems found.")


def adjust(args):
    memory, std = load(args.deal)
    items = given(args.adjustment)
    items = items if isinstance(items, list) else [items]
    if not items or not all(isinstance(item, dict) for item in items):
        raise Refused("an adjustment is a JSON object, or a list of them")
    stamp = {"date": datetime.date.today().isoformat(), "rev": store.revision(memory), "stage": memory["deal"]["stage"]}
    items = [{**item, **stamp} for item in items]
    new = [note for note in standard.effective(args.deal, extra=items)["notes"] if note not in std["notes"]]
    if new:
        raise Refused("The standard was not changed.\n" + "\n".join(new))
    layer = files.read_json(args.deal, files.DEAL_LAYER, {"layer": "deal", "adjustments": []})
    layer["adjustments"] += items
    files.write_json(args.deal, files.DEAL_LAYER, layer)
    done = "; ".join(f"{item['do']} {item.get('target') or (item.get('check') or item.get('indicator'))['id']}" for item in items)
    store.note_outside_change(memory)
    store.record(memory, items[0].get("by", "unknown"), f"Adjusted the standard: {done}")
    files.write_json(args.deal, files.MEMORY, memory)
    print(f"Adjusted the standard for this deal: {done}.")


def file_documents(args):
    _, std = load(args.deal)
    kinds = {kind["id"]: kind for kind in std["source_kinds"]}
    place = {slot["id"]: f"{files.CLIENT}/{folder['id']} {safe(folder['title'])}/{sub['id']} {safe(sub['title'])}"
             for folder in std["dataroom"]["folders"] for sub in folder["sub_folders"] for slot in sub["slots"]}
    items = given(args.filing)
    items = items if isinstance(items, list) else [items]
    for item in items:
        if not isinstance(item, dict) or item.get("kind") not in kinds or not isinstance(item.get("file"), str):
            raise Refused(f"a filing is a list, and each document in it needs a 'file' and a known 'kind': {item!r}\n"
                          f"Known kinds: {', '.join(kinds)}")
    manifest = files.read_json(args.deal, files.MANIFEST, {"documents": []})
    for item in items:
        name = item["file"].replace("\\", "/").split("/")[-1]
        slot = kinds[item["kind"]].get("slot")
        target = f"{place[slot]}/{name}" if slot else f"Internal/sources/{name}"
        files.move(args.deal, item["file"], target)
        manifest["documents"] = [doc for doc in manifest["documents"] if doc["path"] not in (target, item["file"])]
        if slot:
            manifest["documents"].append({"path": target, "slot": slot, "kind": item["kind"], "title": item.get("title", name),
                                          "party": item.get("party"), "period": item.get("period"),
                                          "fingerprint": files.fingerprint(args.deal, target)})
        files.write_json(args.deal, files.MANIFEST, manifest)  # after each move, so the list never lags the folder
        print(f"{item['file']} -> {target}")


def doctor(args):
    packaged = files.packaged_standard()["version"]
    print(f"Bankability 2 version {__version__}, with standard {packaged}.")
    print(f"Python {sys.version.split()[0]} on {sys.platform}.")
    if args.deal:
        memory = files.read_json(args.deal, files.MEMORY)
        if memory is None:
            print(f"{args.deal} holds no deal yet.")
            return
        print(f"Deal {memory['deal']['name']}: revision {store.revision(memory)}, standard {memory['deal']['standard']}.")
        if memory["deal"]["standard"] != packaged:
            print("Note: the deal uses another version of the standard than this tool carries.")
        files.write(args.deal, "Internal/memory/doctor.txt", f"Checked on {datetime.date.today().isoformat()}\n")
        print("Writing to the deal folder works.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bankability2", description="A memory for an investment deal.")
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, run, text, deal="deal"):
        sub = commands.add_parser(name, help=text)
        sub.add_argument("deal", nargs="?" if deal == "optional" else None, help="the deal folder")
        sub.set_defaults(run=run)
        return sub

    sub = command("start", start, "create a deal folder")
    sub.add_argument("--name", required=True)
    sub.add_argument("--stage", default="screening")
    sub.add_argument("--institution", help="the institution's layer of the standard, a JSON file")
    sub = command("status", status, "the structure, what changed and what to do next")
    sub.add_argument("--all", action="store_true", help="list every candidate")
    sub.add_argument("--since", type=int, help="show changes after this revision")
    sub.add_argument("--json", action="store_true")
    command("add", add, "record a set of changes").add_argument("changes", help="a JSON file, or - for standard input")
    command("show", show, "look something up").add_argument("what", nargs="+", help="an ID, 'log', 'sheet', or words to search for")
    command("pages", refresh, "fill in the tool's parts of the wiki pages")
    command("check", check, "report what looks wrong")
    command("adjust", adjust, "adjust the standard for this deal").add_argument("adjustment", help="a JSON file, or -")
    command("file", file_documents, "sort documents into the client folder").add_argument("filing", help="a JSON file, or -")
    command("doctor", doctor, "report where the tool runs", deal="optional")
    args = parser.parse_args(argv)
    for stream in filter(None, (sys.__stdin__, sys.__stdout__)):
        stream.reconfigure(encoding="utf-8")  # Windows would use its own code page when the tool is piped
    code = 0
    try:
        args.run(args)
    except (Refused, json.JSONDecodeError, UnicodeDecodeError, OSError) as refusal:
        print(f"Refused: {refusal}")
        code = 1
    if files.WRITTEN:  # also after a refusal: `file` may have moved documents before it was refused
        print("Wrote: " + ", ".join(dict.fromkeys(files.WRITTEN)))
    return code


if __name__ == "__main__":
    sys.exit(main())
