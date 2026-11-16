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
    if memory is None and files.read(deal, files.OLD_MEMORY) is not None:
        raise Refused(f"{deal} keeps its record where an earlier version of the tool put it. Move it with: upgrade <folder>")
    if memory is None:
        raise Refused(f"{deal} holds no deal. The deal folder comes right after the command, as in: show <folder> facts. "
                      "To start a deal there: start <folder> --name <name>")
    return memory, standard.effective(deal)


def given(path):
    """The JSON handed to a command: a file, or standard input when the path is "-"."""
    return json.load(sys.stdin) if path == "-" else files.read_input(path)


def start(args):
    if any(files.read(args.deal, path) is not None for path in (files.MEMORY, files.OLD_MEMORY)):
        raise Refused(f"{args.deal} already holds a deal")
    std = files.packaged_standard()
    if args.stage not in [stage["id"] for stage in std["stages"]]:
        raise Refused(f"unknown stage {args.stage!r}")
    for name in files.INTERNAL_FOLDERS:  # the client folder comes with its manifest. The data room is an index, not folders
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


def structure(memory, std, scope=None):
    """The subjects with their roles, and the links. With a scope: only the subject or link looked at, and what touches it."""
    held = assess.roles(memory, std)
    shown_as = {kind["id"]: f", {kind['shown_as']}" for kind in std["subject_kinds"] if "shown_as" in kind}
    print("\n## Structure")
    ended = [rid for table in ("subjects", "links") for rid, entry in memory[table].items() if entry.get("state") == "ended"]
    for sid, subject in store.live(memory).items():
        if scope is None or sid in scope:
            print(f"- {sid} {subject.get('name') or 'not yet named'}: {subject['kind']}{shown_as.get(subject['kind'], '')}"
                  + "".join(f", {role}" for role in sorted(held.get(sid, ()))))
    for lid, link in memory["links"].items():
        if (scope is None or lid in scope) and lid not in ended:
            towards = " or ".join(standard.find(std, "link:" + link["type"]).get("counts_for", []))
            why = "one of its ends has ended" if {link["from"], link["to"]} & set(ended) else f"it does not point at a {towards}"
            print(f"- {lid} {pages.name_of(lid, memory)} ({link['state']}"
                  + ("" if assess.counts(link, memory, std) else f"; it gives no role and no checks, because {why}") + ")")
    past = [rid for rid in ended if scope is None or rid in scope]
    if past:
        print(f"- Ended, and kept in the record: {', '.join(past)}")


def status(args):
    memory, std = load(args.deal)
    rows, scope = assess.assess(memory, std), None
    if args.about:  # only what concerns one subject or link, and for a subject the links that touch it
        if args.about != store.DEAL and store.table_of(memory, args.about) not in ("subjects", "links"):
            raise Refused(f"--for takes the ID of a subject or a link, or {store.DEAL}, and {args.about!r} is none of them")
        scope = {args.about} | {lid for lid, link in memory["links"].items() if args.about in (link["from"], link["to"])}
        rows = [row for row in rows if row["for"] in scope]
    listed = files.read_json(args.deal, files.MANIFEST, {"documents": []})["documents"]
    todo = assess.next_list(memory, std, rows, in_folder={doc["slot"] for doc in listed}, scope=scope)
    found = assess.claims(rows, memory, std)
    if args.json:
        print(json.dumps({"deal": memory["deal"], "revision": store.revision(memory), "checks": rows,
                          "claims": found, "next": todo}, indent=1, ensure_ascii=False))
        return
    deal, titles = memory["deal"], std["stage_titles"]
    print(f"# {deal['name']}: stage {titles[deal['stage']]}, revision {store.revision(memory)}, standard {deal['standard']}")
    if scope is None:
        print("\nThe record holds: " + ", ".join(f"{table} {len(memory[table])}" for table in store.TABLES) + ".")
    if scope:
        print(f"\nOnly what concerns {pages.name_of(args.about, memory)} ({args.about}).")
    structure(memory, std, None if args.about == store.DEAL else scope)
    entries = memory["log"][-5:] if args.since is None else [entry for entry in memory["log"] if entry["n"] > args.since]
    if scope is None or args.since is not None:
        print("\n## What changed")
        for entry in entries:
            touched = len(entry["added"]) + len(entry["changed"])
            print(f"- {entry['n']}. {entry['at'][:10]} {entry['by']}: {entry['note']} ({touched} records)")
    counts = {}
    for row in rows:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    print("\n## Next\n\nChecks: " + (", ".join(f"{count} {state}" for state, count in counts.items()) or "none apply yet") + ".")
    due = [row["due_by"] for row in rows if row["state"] == "open"]
    if due:  # most open checks are work for a later stage
        print("Open, by the stage each is ideally answered by: "
              + ", ".join(f"{titles[stage]} {due.count(stage)}" for stage in std["stage_ids"] if stage in due) + ".")
    waits = [row for row in rows if row["state"] == "waiting"]
    if waits:  # a check that waits needs no work now
        others = [row["for"] for row in waits if not std["checks"][row["check"]].get("mitigant")]
        seats = sum(sid in memory["subjects"] and not memory["subjects"][sid].get("name") for sid in others)
        mitigants = len(waits) - len(others)
        parts = [(mitigants, f"mitigant{'s' * (mitigants != 1)}, asked only if a test goes against its claim"),
                 (seats, "for a party that is not yet named"), (len(others) - seats, "for an earlier answer")]
        print("Waiting: " + "; ".join(f"{count} {why}" for count, why in parts if count) + ".")
    print("\n## Where the claims stand\n")
    for pillar in std["pillars"]:
        counts = assess.view(found, std)[pillar["id"]]
        if scope is None or any(counts):
            print(f"- {pillar['title']}: " + (", ".join(f"{count} {name}" for name, count in zip(assess.VERDICTS, counts)
                                                        if count) or "no claim applies yet"))
    urgent = [line[2:] for line in pages.claim_lines(found, memory, std) if not line.startswith("- **Claims:**")]
    lines = []
    for row in todo["checks"]:
        waits = f"; {row['unlocks']} check{'s wait' if row['unlocks'] > 1 else ' waits'} on it" if row["unlocks"] else ""
        state = ", ".join([row["state"], *row["flags"]])
        check = std["checks"][row["check"]]
        lines.append(f"{check['question']} ({pages.name_of(row['for'], memory)}; ideally by {titles[row['due_by']]}; "
                     f"{state}{waits}) [{row['check']}: {standard.takes(check)}]")
    limit = None if args.all else 15
    group("Claims that are challenged, contested or to look at again", urgent, limit)
    group("Structure still open", todo["structure"], limit)
    group("Checks to answer or strengthen", lines, limit)
    group("Gaps with an agreed action", todo["actions"], limit)
    if scope is None:
        group("Documents not in the folder", [f"{doc['slot']} {doc['title']}: {doc['why']}" for doc in todo["documents"]], limit)
    group("Questions without an answer", [f"{q['id']} to {q['asked_of']}, " + (f"asked {q['asked']}" if q.get("asked") else
                                          "not sent yet") + f": {q['text']}" for q in todo["questions"]], limit)
    group("Facts that rest on a replaced source", todo["replaced"], limit)
    if scope is None:
        group("System fields without a value", todo["fields"], limit)
    if todo["stray"]:
        group("Answers to a check that is not asked or not relevant there", todo["stray"], limit)
    if std["notes"] and scope is None:
        group("Notes on the standard", std["notes"], limit)


def add(args):
    memory, std = load(args.deal)
    change = given(args.changes)
    if not isinstance(change, dict):
        raise Refused("a set of changes is one JSON object")
    missing = []
    sources = change.get("sources", [])
    for source in sources if isinstance(sources, list) else []:
        known = memory["sources"].get(str(source.get("id")), {}) if isinstance(source, dict) else {}
        if isinstance(source, dict) and source.get("where") and source["where"] != known.get("where"):  # new, or moved
            mark = files.fingerprint(args.deal, source["where"])
            if mark:
                source.setdefault("fingerprint", mark)
            else:
                missing.append(source["where"])
    try:
        entry, names = store.apply(memory, change, std)
    except (TypeError, KeyError, AttributeError) as error:  # nothing is written before apply returns
        raise Refused(f"Nothing was recorded. A value in this set of changes has the wrong shape: {error!r}")
    if entry is None:
        print("Already recorded: this set of changes was applied before.")
        return
    if not args.dry:
        files.write_json(args.deal, files.MEMORY, memory)
    print(("A trial run: nothing was written. It would be recorded" if args.dry else "Recorded")
          + f" as revision {entry['n']}. Added: {', '.join(entry['added']) or 'nothing'}. "
          f"Changed: {', '.join(entry['changed']) or 'nothing'}.")
    for name, rid in names.items():
        print(f"{name} -> {rid}")
    for path in missing:
        print(f"Note: {path} was not found in this copy of the folder, so it has no fingerprint.")
    for line in assess.stray(memory, std, assess.assess(memory, std), [*entry["added"], *entry["changed"]]):
        print(f"Note: {line}. The answer is recorded all the same.")
    cite = [path for path, text in pages.all_pages(args.deal).items()  # what a page says of a changed record may no longer hold
            if set(entry["changed"]) & set(pages.ID.findall(pages.own_text(text)))]
    if cite:
        print("Pages that cite a record this set changed, to read again: " + ", ".join(cite))


def summary(record):
    for key in ("title", "statement", "name", "decision", "text", "type", "note"):
        if record.get(key):
            return str(record[key])
    return ""


def folders(std):
    """Where a document of each data-room slot is filed: the client folder, and the slot its index lists it under."""
    return {slot["id"]: f"{files.CLIENT}, listed under {slot['id']} {slot['title']}" for slot in standard.slots_of(std)}


def show_kinds(std):
    """The kinds of source with the folder each is filed in, the kinds of subject, and the kinds of link with their roles."""
    place = folders(std)
    print("## Kinds of source, and the folder each is filed in\n")
    for kind in std["source_kinds"]:
        print(f"- {kind['id']}: {kind['title']}. Folder: {place.get(kind.get('slot'), 'Internal/sources')}")
    print("\n## Kinds of subject, and the letter its IDs start with\n")
    for kind in std["subject_kinds"]:
        print(f"- {kind['id']} ({kind['prefix']}): {kind['description']}")
    print("\n## Kinds of link, and the role each gives\n")
    for link in std["link_types"]:
        gives = " and ".join(f"{link['role_' + end]} to its '{end}' end" for end in ("from", "to") if "role_" + end in link)
        only = f" It counts only when it points at a {' or '.join(link['counts_for'])}." if "counts_for" in link else ""
        print(f"- {link['id']}: {link['description']} " + (f"Gives the role {gives}." if gives else "Gives no role.") + only)


def show_claims(memory, std, rows):
    """Every claim, by pillar, one line each: where it stands and what that rests on."""
    found = assess.claims(rows, memory, std)
    for pillar in std["pillars"]:
        mine = [claim for claim in found if std["by_id"][claim["indicator"]]["pillar"] == pillar["id"]]
        if mine:
            print(f"## {pillar['title']}\n")
        for claim in mine:
            states = sorted(claim["mitigants"].values())
            answered = claim["tests"] + len(claim["against"]) + len(claim["contested"])
            weak = claim["tests"] - claim["firm"] - claim["own_word"]  # on evidence that is thin, old or not listed
            parts = [claim["stands"], f"tests answered {answered} of {claim['asked']}",
                     claim["against"] and f"against {', '.join(claim['against'])}",
                     claim["contested"] and f"facts disagree on {', '.join(claim['contested'])}",
                     claim["own_word"] and f"answers on someone's own word {claim['own_word']}",
                     weak and f"answers on evidence to strengthen {weak}",
                     states and "mitigants " + ", ".join(f"{states.count(state)} {state}" for state in dict.fromkeys(states)),
                     claim["actions"] and f"decision {', '.join(claim['actions'])}"]
            print(f"- {std['by_id'][claim['indicator']]['title']} ({pages.name_of(claim['for'], memory)}): "
                  f"{'; '.join(filter(None, parts))} [{claim['indicator']}]")
        if mine:
            print()


def fact_lines(memory, terms):
    """One line per fact that is current or disputed. With IDs or words: every fact whose line holds one of them, such as
    the facts about a subject, from a source or in answer to a check, a fact named by its ID, or the facts with a word."""
    lines = []
    for fid, fact in memory["facts"].items():
        state = "" if fact["state"] == "current" else f" ({fact['state']})"
        value = f" {fact.get('label', 'Value')}: {fact.get('value')} {fact.get('unit', '')}".rstrip() + "."
        answers = ", ".join(f"{answer['check']}: {pages.shown(answer['value'])[:60]}" for answer in fact.get("answers", []))
        where = [fact["source"], fact.get("place"), fact.get("as_of") and f"as of {fact['as_of']}", fact.get("said_by"),
                 answers and f"answers {answers}"]
        line = (f"- {fid}{state} about {fact['about']}: {fact['statement']}{value if 'value' in fact else ''} "
                f"({'; '.join(filter(None, where))})")
        named = any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", line, re.I) for term in terms)
        if named or (not terms and fact["state"] != "outdated"):  # a long statement is cut, unless the fact is named by its ID
            cut = fid not in map(str.upper, terms) and len(fact["statement"]) > 300
            lines.append(line.replace(fact["statement"], fact["statement"][:300] + " ...") if cut else line)
    return lines


def show(args):
    memory, std = load(args.deal)
    what, rows = " ".join(args.what), assess.assess(memory, std)
    if what == "log":
        if len(memory["log"]) > 30:
            print(f"The last 30 of {len(memory['log'])} entries.")
        for entry in memory["log"][-30:]:
            print(f"{entry['n']}. {entry['at']} {entry['by']}: {entry['note']} "
                  f"added {entry['added']} changed {list(entry['changed'])}")
    elif what == "sheet":
        print("\n".join(assess.sheet(memory, std)) or "The institution's layer lists no systems.")
    elif what == "kinds":
        show_kinds(std)
    elif what == "claims":
        show_claims(memory, std, rows)
    elif args.what[0] == "facts":
        print("\n".join(fact_lines(memory, args.what[1:])) or "Nothing found.")
        outdated = sum(fact["state"] == "outdated" for fact in memory["facts"].values())
        if outdated and len(args.what) == 1:
            print(f"\nOutdated facts not listed: {outdated}. Name one, or a word it holds, to see it.")
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
        hits = [f"- {rid} ({record.get('state', 'current')}): {summary(record)}"
                for table in store.TABLES for rid, record in memory[table].items()
                if what.lower() in json.dumps(record, ensure_ascii=False).lower()]
        hits += [f"- {cid}: {check['question']}" for cid, check in std["checks"].items()  # and the checks of the standard
                 if what.lower() in f"{check['question']} {check.get('assumption', '')}".lower()]
        print("\n".join(hits) or "Nothing found.")


def refresh(args):
    def counted(number):
        return f"{number} page" + ("" if number == 1 else "s")

    memory, std = load(args.deal)
    rows = assess.assess(memory, std)
    created, changed, same = pages.refresh(args.deal, memory, std, rows, assess.roles(memory, std))
    if created:
        print(f"Created {counted(len(created))} for you to write: {', '.join(created)}.")
    if changed or same:
        print(f"Updated the tool's parts of {counted(len(changed))}. {counted(same)} needed no change.")
    print(f"Wrote the contents page, the sources page and the view for a browser: {files.WIKI}/wiki.html.")


def file_problems(deal, memory):
    """Documents that are missing, changed or not listed. Skipped where the documents are not present."""
    listed = {doc["path"]: doc for doc in files.read_json(deal, files.MANIFEST, {"documents": []})["documents"]}
    present = [path for path in files.listing(deal, files.CLIENT) if path not in (files.MANIFEST, files.CLIENT + "/index.md")]
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
        if source.get("extract") and files.fingerprint(deal, source["extract"]) is None:
            found.append(f"{sid}: the extract {source['extract']} was not found in this copy of the folder")
    return found


def check(args):
    memory, std = load(args.deal)
    found = store.verify(memory) + std["notes"] + file_problems(args.deal, memory) + pages.problems(args.deal, memory)
    found += [f"{did}: the decision names nothing it rests on" for did, decision in memory["decisions"].items()
              if not decision.get("rests_on")]
    for table, keys in (("facts", ["statement"]), ("decisions", ["decision", "reason"]), ("links", ["why"]), ("subjects", ["note"])):
        for rid, record in memory[table].items():  # a record that is still in use and names a fact that was replaced
            text = " ".join(str(record.get(key, "")) for key in keys)
            found += [f"{rid}: names {fid}, which is outdated (replaced by {fact.get('replaced_by')})"
                      for fid, fact in memory["facts"].items() if fact["state"] == "outdated" and fact.get("replaced_by") != rid
                      and record.get("state") not in ("outdated", "ended") and re.search(rf"\b{fid}\b", text)]
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
    """Move each document to its place: the client folder if its kind has a slot in the data room, the internal sources
    if not. A text extract made from it goes to the extracts. Then write the index of the client folder."""
    memory, std = load(args.deal)
    kinds = {kind["id"]: kind for kind in std["source_kinds"]}
    items, refused = given(args.filing), []
    items = items if isinstance(items, list) else [items]
    for item in items:
        if (not isinstance(item, dict) or item.get("kind") not in kinds or not isinstance(item.get("file"), str)
                or not isinstance(item.get("extract", ""), str)):
            raise Refused(f"a filing is a list, and each document in it needs a 'file' and a known 'kind': {item!r}\n"
                          f"Known kinds: {', '.join(kinds)}")
    manifest = files.read_json(args.deal, files.MANIFEST, {"documents": []})
    for item in items:
        name, extract = (item.get(key, "").replace("\\", "/").split("/")[-1] for key in ("file", "extract"))
        slot = kinds[item["kind"]].get("slot")
        target, moved = f"{files.CLIENT if slot else 'Internal/sources'}/{name}", False
        try:
            if name in ("index.md", "manifest.json") and slot:
                raise Refused(f"{target} is a name the tool keeps for itself")
            files.move(args.deal, item["file"], target)  # refuses to overwrite another document of that name
            moved = True
            if extract:
                files.move(args.deal, item["extract"], f"{files.EXTRACTS}/{extract}")
        except Refused as refusal:
            refused.append(f"{item['extract' if moved else 'file']}: {refusal}")
            if not moved:
                continue
            extract = ""  # the document is filed, without its extract
        manifest["documents"] = [doc for doc in manifest["documents"] if doc["path"] not in (target, item["file"])]
        if slot:
            manifest["documents"].append({"path": target, "slot": slot, "kind": item["kind"], "title": item.get("title", name),
                                          "party": item.get("party"), "period": item.get("period"),
                                          "fingerprint": files.fingerprint(args.deal, target),
                                          **({"extract": f"{files.EXTRACTS}/{extract}"} if extract else {})})
        files.write_json(args.deal, files.MANIFEST, manifest)  # after each move, so the list never lags the folder
        print(f"{item['file']} -> {target}" + (f", with its extract {files.EXTRACTS}/{extract}" if extract else ""))
    files.write(args.deal, f"{files.CLIENT}/index.md", pages.documents(memory["deal"]["name"], manifest["documents"], std))
    if refused:
        raise Refused("Not filed. The tool never overwrites a file: where a name is taken, give the document a name of its "
                      "own and file it again.\n" + "\n".join(refused))


def upgrade(args):
    """Put the standard that comes with the tool into the deal folder, and say which answers it leaves without a check.
    A record that an earlier version of the tool kept elsewhere is first moved to its place."""
    if files.read(args.deal, files.MEMORY) is None and files.read(args.deal, files.OLD_MEMORY) is not None:
        files.move(args.deal, files.OLD_MEMORY, files.MEMORY)
        print(f"Moved the record to {files.MEMORY}. It was in {files.OLD_MEMORY}.")
    memory, _ = load(args.deal)
    new, old = files.packaged_standard(), memory["deal"]["standard"]
    before = files.read_json(args.deal, files.BASE)
    if before == new:
        print(f"The deal already uses the standard that comes with the tool: {old}.")
        return
    files.write_json(args.deal, files.BASE, new)
    std = standard.effective(args.deal)  # with the layers of the institution and the deal on top
    store.note_outside_change(memory)
    memory["deal"]["standard"] = new["version"]
    note = f"Standard changed from {old} to {new['version']}"
    store.record(memory, "tool", note, changed={store.DEAL: {"standard": old}})
    files.write_json(args.deal, files.MEMORY, memory)
    print(f"The deal now uses standard {new['version']}. It used {old}.")
    gone = [f"{fid}: {answer['check']}" for fid, fact in memory["facts"].items() if fact["state"] != "outdated"
            for answer in fact.get("answers", []) if answer["check"] not in std["checks"]]
    print("Answers that name a check that no longer exists. They stay in the facts and no longer count:\n- "
          + "\n- ".join(gone) if gone else "Every recorded answer still names a check of the standard.")
    was, now = ({check["id"]: (ind["id"], check, {key: value for key, value in ind.items() if key != "checks"})
                 for ind in base["indicators"] for check in ind["checks"]} for base in (before, new))  # a check with its claim
    for title, ids in (("New checks", now.keys() - was.keys()), ("Checks that are gone", was.keys() - now.keys()),
                       ("Checks that changed", [cid for cid in now.keys() & was.keys() if now[cid] != was[cid]])):
        if ids:  # with the indicator of each, where the check that took the place of a removed one is found
            print(f"{title}: " + ", ".join(f"{cid} ({(now.get(cid) or was[cid])[0]})" for cid in sorted(ids)) + ".")
    for note in std["notes"]:
        print(f"Note: {note}")


def doctor(args):
    packaged = files.packaged_standard()["version"]
    print(f"Bankability 2 version {__version__}, with standard {packaged}.")
    print(f"Python {sys.version.split()[0]} on {sys.platform}.")
    if args.deal:
        memory = files.read_json(args.deal, files.MEMORY)
        if memory is None:
            old = files.read(args.deal, files.OLD_MEMORY) is not None
            print(f"{args.deal} keeps its record where an earlier version of the tool put it. Move it with: upgrade <folder>"
                  if old else f"{args.deal} holds no deal yet.")
            return
        print(f"Deal {memory['deal']['name']}: revision {store.revision(memory)}, standard {memory['deal']['standard']}.")
        if memory["deal"]["standard"] != packaged:
            print("Note: the deal uses another version of the standard than this tool carries. `upgrade` brings it in line.")
        files.write(args.deal, "Internal/record/doctor.txt", f"Checked on {datetime.date.today().isoformat()}\n")
        print("Writing to the deal folder works.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bankability2", description="Keeps the record of an investment deal.")
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
    sub.add_argument("--for", dest="about", metavar="ID", help="only what concerns this subject or link")
    sub.add_argument("--since", type=int, help="show changes after this revision")
    sub.add_argument("--json", action="store_true")
    sub = command("add", add, "record a set of changes")
    sub.add_argument("changes", help="a JSON file, or - for standard input")
    sub.add_argument("--try", dest="dry", action="store_true", help="say what the set would record, and write nothing")
    command("show", show, "look something up").add_argument(
        "what", nargs="+", help="an ID, 'log', 'sheet', 'kinds', 'claims', 'facts', 'facts <IDs or words>', or words to search for")
    command("pages", refresh, "fill in the tool's parts of the wiki pages, and write the view for a browser")
    command("check", check, "report what looks wrong")
    command("adjust", adjust, "adjust the standard for this deal").add_argument("adjustment", help="a JSON file, or -")
    command("file", file_documents, "file documents and index the client folder").add_argument("filing", help="a JSON file, or -")
    command("upgrade", upgrade, "put the standard that comes with the tool into the deal folder")
    command("doctor", doctor, "report where the tool runs", deal="optional")
    args = parser.parse_args(argv)
    for stream in filter(None, (sys.__stdin__, sys.__stdout__)):
        stream.reconfigure(encoding="utf-8")  # Windows would use its own code page when the tool is piped
    code = 0
    try:
        try:
            args.run(args)
        except BrokenPipeError:
            raise
        except (Refused, json.JSONDecodeError, UnicodeDecodeError, OSError) as refusal:
            print(f"Refused: {refusal}")
            code = 1
        if files.WRITTEN:  # also after a refusal: `file` may have moved documents before it was refused
            print("Wrote: " + ", ".join(dict.fromkeys(files.WRITTEN)))
        print(end="", flush=True)
    except BrokenPipeError:  # the reader stopped reading, as in `show ... | head`. That is not a refusal.
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main())
