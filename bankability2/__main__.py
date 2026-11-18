"""The commands. Run as: python -m bankability2 <command> <deal folder>"""
import argparse
import datetime
import json
import re
import sys
import unicodedata

from . import __version__, assess, files, pages, standard, store
from .files import Refused

TEXT = re.compile(r"\.(md|txt|html?)$", re.I)  # an original that is a text itself
READ = re.compile(r"^[ \t]*\[read from the page\][ \t]*$.*?^[ \t]*\[end\][ \t]*$", re.I | re.M | re.S)  # rows written out from a scan
PAGE = re.compile(r"\f|^=+[^=\n]*\bpage\s+(\d+)\b[^=\n]*=+[ \t]*$", re.I | re.M)  # where a page of a text starts


def older(deal):
    """A line for a folder that keeps its record or its standard where an earlier version of the tool put it."""
    for path, old, what in ((files.MEMORY, files.OLD_MEMORY, "record"), (files.BASE, f"{files.OLD_STANDARD}/base.json", "standard")):
        if files.read(deal, path) is None and files.read(deal, old) is not None:
            return f"{deal} keeps its {what} where an earlier version of the tool put it. Move it with: upgrade <folder>"
    return None


def load(deal):
    memory = files.read_json(deal, files.MEMORY)
    if older(deal):
        raise Refused(older(deal))
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
            short = f" ({subject['short']})" if subject.get("short") else ""
            print(f"- {sid} {subject.get('name') or 'not yet named'}{short}: {subject['kind']}{shown_as.get(subject['kind'], '')}"
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


def marked_lines(rows, memory, std):
    """One line for each check marked as what matters for this deal: its reason, and for whom it is open, answered or in
    another state. Its question is in the list of checks below, and in show <ID>."""
    found = {}
    for row in sorted(rows, key=lambda row: pages.ORDER.index(row["state"])):
        if std["checks"][row["check"]].get("matters"):
            found.setdefault(row["check"], {}).setdefault(row["state"], []).append(  # a link by its ID, to keep the line short
                row["for"] if row["for"] in memory["links"] else pages.name_of(row["for"], memory))
    lines = []
    for cid, states in found.items():
        whom = "; ".join(f"{state} for {', '.join(names[:3])}" + f" and {len(names) - 3} more" * (len(names) > 3)
                         for state, names in states.items())
        lines.append(f"{cid}: {std['checks'][cid]['matters']} {whom[0].upper()}{whom[1:]}.")
    return lines


def status(args):
    memory, std = load(args.deal)
    rows, scope = assess.assess(memory, std), None
    part = {pillar["id"]: pillar["title"] for pillar in std["pillars"]}.get(args.about)
    if part:  # only the checks of one pillar, and whom they are asked of
        rows = [row for row in rows if std["by_id"][row["indicator"]]["pillar"] == args.about]
        scope = {row["for"] for row in rows}
    elif args.about:  # only what concerns one subject or link, and for a subject the links that touch it
        if args.about != store.DEAL and store.table_of(memory, args.about) not in ("subjects", "links"):
            raise Refused(f"--for takes the ID of a subject or a link, {store.DEAL} or a pillar "
                          f"({', '.join(pillar['id'] for pillar in std['pillars'])}), and {args.about!r} is none of them")
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
        if deal.get("avoid"):
            print("Wordings to avoid: " + "; ".join(deal["avoid"]) + ".")
        bare = sum(fact["state"] != "outdated" and fact.get("said_by") != "inference"
                   and not (fact.get("quote") or fact.get("nothing_found"))  # a search that found nothing has no words to quote
                   and bool(memory["sources"][fact["source"]].get("where")) for fact in memory["facts"].values())
        if bare:
            print(f"Facts from a document that carry no quotation: {bare}.")
        loose = sum(map(len, uncited(args.deal, memory).values()))
        if loose:
            print(f"Facts that no page cites: {loose}. List them with: show <deal> uncited")
    if scope:
        print(f"\nOnly what concerns {part or pages.name_of(args.about, memory)} ({args.about}).")
    structure(memory, std, None if args.about == store.DEAL else scope)
    entries = memory["log"][-5:] if args.since is None else [entry for entry in memory["log"] if entry["n"] > args.since]
    if scope is None or args.since is not None:
        print("\n## What changed")
        for entry in entries:
            touched = len(entry["added"]) + len(entry["changed"])
            print(f"- {entry['n']}. {entry['at'][:10]} {entry['by']}: {entry['note']} ({touched} record{'s' * (touched != 1)})")
    print("\n## Next\n\nChecks: " + (", ".join(f"{count} {state}" for state, count in assess.tally(rows).items())
                                    or "none apply yet") + ".")
    due = pages.by_stage(rows, std)
    if due:
        print(f"Open, by the stage each is ideally answered by: {due}.")
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
    lines = {}  # one line for a check that stands the same for several subjects
    for row in todo["checks"]:
        waits = f"; {row['unlocks']} check{'s wait' if row['unlocks'] > 1 else ' waits'} on it" if row["unlocks"] else ""
        rest = f"ideally by {titles[row['due_by']]}; {pages.shown_state(row)}{waits}"
        rest += f"; missing: {row.get('missing')}" * ("missing" in row)
        lines.setdefault((row["check"], rest), []).append(pages.name_of(row["for"], memory))
    lines = [f"{std['checks'][cid]['question']} ({'; '.join(names)}; {rest}) [{cid}: {standard.takes(std['checks'][cid])}]"
             for (cid, rest), names in lines.items()]
    limit = None if args.all else 15
    group("Claims that are challenged, contested or to look at again", urgent, limit)
    group("Structure still open", todo["structure"], limit)
    group("What matters most", marked_lines(rows, memory, std), limit)
    group("Checks to answer or strengthen", lines, limit)
    group("Gaps with an agreed action", todo["actions"], limit)
    if scope is None:
        group("Documents not in the folder", [f"{doc['slot']} {doc['title']}: {doc['why']}" for doc in todo["documents"]], limit)
        named = {source.get(key) for source in memory["sources"].values() for key in ("where", "extract")}
        group("Documents filed and not recorded", [path for folder in (files.CLIENT, "Internal/sources") for path in files.listing(
            args.deal, folder) if path not in named | {files.MANIFEST, files.CLIENT + "/index.md"}], limit)
    group("Questions without an answer", [f"{q['id']} to {q['asked_of']}, " + (f"asked {q['asked']}" if q.get("asked") else
                                          "not sent yet") + f": {q['text']}" for q in todo["questions"]], limit)
    group("Facts that rest on a replaced source", todo["replaced"], limit)
    copied = copied_quotes(args.deal, memory) if scope is None else []
    if copied:
        group("Quotations to compare with the page", copied, limit)
    if scope is None:
        group("System fields without a value", todo["fields"], limit)
    if todo["stray"]:
        group("Answers and decisions for a check that is not asked or not relevant there", todo["stray"], limit)
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
    before = assess.assess(memory, std)
    was, wanted = assess.tally(before), assess.called_for(before, memory, std)
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
    rows = assess.assess(memory, std)
    now = assess.tally(rows)
    moved = [f"{now.get(state, 0) - was.get(state, 0):+d} {state}" for state in {**was, **now} if now.get(state) != was.get(state)]
    if moved:
        print(f"Checks: {', '.join(moved)}.")
    for line in assess.stray(memory, std, rows, [*entry["added"], *entry["changed"]]):
        print(f"Note: {line}. It is recorded all the same.")
    for call in assess.called_for(rows, memory, std):
        if call not in wanted:
            print(f"Note: the answer to {call['check']} for {call['for']} calls for {call['wanted']}, and there is none.")
    for line in quote_problems(args.deal, memory, [*entry["added"], *entry["changed"]]):  # before a trial run is made real
        print(f"Note: {line}.")
    cite = [path for path, text in pages.all_pages(args.deal).items()  # what a page says of a changed record may no longer hold
            if set(entry["changed"]) & set(pages.ID.findall(pages.own_text(text)))]
    if cite:
        print("Pages that cite a record this set changed, to read again: " + ", ".join(cite))


def uncited(deal, memory):
    """The current facts that no page of the wiki cites, by source. A citation in a draft, or in a part the tool writes, does not count."""
    cited = set(pages.ID.findall(" ".join(map(pages.own_text, pages.all_pages(deal).values()))))
    found = {}
    for fid, fact in memory["facts"].items():
        if fact["state"] == "current" and fid not in cited:
            words = fact.get("label") or " ".join(fact["statement"].split()[:8]) + " ..." * (len(fact["statement"].split()) > 8)
            found.setdefault(fact["source"], []).append(f"- {fid}: {words}")
    return found


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
    print("## Kinds of source, and the folder each is filed in when the client supplied it\n")
    for kind in std["source_kinds"]:
        print(f"- {kind['id']}: {kind['title']}. Folder: {place.get(kind.get('slot'), 'Internal/sources')}. {kind['description']}")
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
            parts = [claim["stands"], f"tests answered {answered} of {claim['asked']}",
                     claim["against"] and f"against {', '.join(claim['against'])}",
                     claim["contested"] and f"facts disagree on {', '.join(claim['contested'])}",
                     claim["own_word"] and f"answers on someone's own word {claim['own_word']}",
                     claim["to_strengthen"] and f"answers on evidence to strengthen {claim['to_strengthen']}",
                     states and "mitigants " + ", ".join(f"{states.count(state)} {state}" for state in dict.fromkeys(states)),
                     claim["actions"] and f"decision {', '.join(claim['actions'])}"]
            print(f"- {std['by_id'][claim['indicator']]['title']} ({pages.name_of(claim['for'], memory)}): "
                  f"{'; '.join(filter(None, parts))} [{claim['indicator']}]")
        if mine:
            print()


def fact_lines(memory, terms, dated=False):
    """One line per fact that is current or disputed. With IDs or words: every fact whose line holds one of them, such as
    the facts about a subject, from a source or in answer to a check, a fact named by its ID, or the facts with a word.
    Dated: only the current or disputed facts that have a date, in the order of that date, each line led by it."""
    lines, ids = [], {term.upper() for term in terms} & set(memory["facts"])  # a fact named by its ID: that fact, in full
    words = [term for term in terms if term.upper() not in ids]
    for fid, fact in sorted(memory["facts"].items(), key=lambda item: str(item[1].get("as_of"))) if dated else memory["facts"].items():
        if dated and (not fact.get("as_of") or fact["state"] == "outdated"):
            continue
        state = "" if fact["state"] == "current" else f" ({fact['state']})"
        value = f" {fact.get('label', 'Value')}: {fact.get('value')} {fact.get('unit', '')}".rstrip() + "."
        answers = ", ".join(f"{answer['check']}: {pages.shown(answer['value'])[:None if fid in ids else 60]}"
                            for answer in fact.get("answers", []))
        where = [fact["source"], fact.get("place"), not dated and fact.get("as_of") and f"as of {fact['as_of']}", fact.get("said_by"),
                 answers and f"answers {answers}", fid in ids and fact.get("quote") and f'quote: "{fact["quote"]}"']
        line = (f"- {fid}{state} about {fact['about']}: {fact['statement']}{value if 'value' in fact else ''} "
                f"({'; '.join(filter(None, where))})")
        named = fid in ids or any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", line, re.I) for term in words)
        if named or (not terms and fact["state"] != "outdated"):  # a long statement is cut in the list of all facts
            cut = not terms and len(fact["statement"]) > 300
            line = line.replace(fact["statement"], fact["statement"][:300] + " ...") if cut else line
            lines.append(f"- {fact['as_of']} {line[2:]}" if dated else line)
    return lines


def text_paths(source):
    """Where the text of a source is: its extract, and its original where that is a text file."""
    return ([source["extract"]] if source.get("extract") else []) + ([source["where"]] if TEXT.search(source.get("where") or "") else [])


def text_pages(text):
    """The text of each page, by its number. A page starts at a form feed, or at a line such as "===== page 14 =====".
    A text without either is one page. What comes before the first page goes with it."""
    found, number, start = {}, 1, 0
    for mark in PAGE.finditer(text):
        found[number] = found.get(number, "") + text[start:mark.start()]
        number, start = int(mark.group(1)) if mark.group(1) else number + 1, mark.end()
    found[number] = found.get(number, "") + text[start:]
    return {n: part for n, part in found.items() if part.strip()} or {1: text}


def show_text(deal, memory, terms):
    """From the text of a source: one page, the lines that hold all the words with their page, or the pages."""
    source = memory["sources"].get(terms[0].upper()) if terms else None
    if source is None:
        raise Refused("show text takes the ID of a source, then a page or words, as in: show <folder> text S-002 14")
    path = text = None
    for path in text_paths(source):  # the extract first
        text = files.read(deal, path)
        if text:
            break
    if not text:
        raise Refused(f"{terms[0]} has no text in this copy of the folder: no extract, and no original in .md, .txt or .html")
    parts = text_pages(text)
    if len(terms) == 3 and terms[1].lower() in ("page", "p.", "p") and terms[2].isdigit():  # "page 14" as well as "14"
        terms = [terms[0], terms[2]]
    if len(terms) == 2 and terms[1].isdigit():
        print(parts.get(int(terms[1]), "").strip() or f"{path} has no page {terms[1]}. Its pages run from {min(parts)} to {max(parts)}.")
    elif len(terms) > 1:
        words = [word.casefold() for word in terms[1:]]
        hits = [f"- page {n}: {line.strip()}" for n, part in parts.items() for line in part.splitlines()
                if all(word in line.casefold() for word in words)]
        print("\n".join(hits[:40]) or "Nothing found.")
        if len(hits) > 40:
            print(f"And {len(hits) - 40} more lines hold these words.")
    else:
        print(f"The lines on each page of {path}: " + "; ".join(f"page {n}, {len(part.strip().splitlines())}" for n, part in parts.items()) + ".")


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
    elif what == "uncited":  # what the pages have not taken in yet, by source in the order of their IDs
        found = uncited(args.deal, memory)
        print("\n\n".join(f"## {sid} {source['title']} ({len(found[sid])})\n" + "\n".join(found[sid])
                          for sid, source in memory["sources"].items() if sid in found) or "Every current fact is cited on a page.")
        if found:
            print(f"\nFacts that no page cites: {sum(map(len, found.values()))}, from {len(found)} source{'s' * (len(found) != 1)}.")
    elif args.what[0] == "text":
        show_text(args.deal, memory, args.what[1:])
    elif args.what[0] == "dated":  # for the page of the history
        print("\n".join(fact_lines(memory, args.what[1:], dated=True)) or "Nothing found.")
    elif args.what[0] == "facts" or (len(args.what) > 1 and all(term.upper() in memory["facts"] for term in args.what)):
        print("\n".join(fact_lines(memory, args.what[args.what[0] == "facts":])) or "Nothing found.")
        outdated = sum(fact["state"] == "outdated" for fact in memory["facts"].values())
        if outdated and len(args.what) == 1:
            print(f"\nOutdated facts not listed: {outdated}. Name one, or a word it holds, to see it.")
    elif what == "sample":  # ten facts that are not inferences, spread over the record, to compare with the place each names
        taken = [fid for fid, fact in memory["facts"].items() if fact["state"] == "current" and fact.get("said_by") != "inference"]
        some = min(10, len(taken))  # another ten after each change to the record
        picked = [taken[(store.revision(memory) + i * len(taken) // some) % len(taken)] for i in range(some)]
        print("\n".join(fact_lines(memory, picked) if picked else []) or "Nothing found.")
    elif what in store.TABLES:  # every record of one kind, one line each
        print("\n".join(f"- {rid}: {pages.name_of(rid, memory) if what == 'links' else summary(record)}"
                        + f" ({record.get('state')})" * (record.get("state", "current") != "current")
                        for rid, record in memory[what].items()) or "Nothing found.")
    elif what in std["checks"] or what in std["by_id"]:
        entry = std["checks"].get(what) or std["by_id"][what]
        shown = {key: value for key, value in entry.items() if key not in ("checks", "missing")}  # a note shows with the rows
        print(json.dumps(shown, indent=1, ensure_ascii=False))
        print("\n".join(f"- {cid}: {check['question']} [{standard.takes(check)}]" for cid, check in std["checks"].items()
                        if check["indicator"] == what))
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
        used = [row for row in rows if row["for"] == what or what in row.get("facts", []) + pages.ID.findall(row.get("missing", ""))]
        if used:
            print("\n" + "\n".join(pages.check_lines([row for row in used if row["state"] != "not relevant"], memory, std)))
    else:
        hits = []
        for table in store.TABLES:
            for rid, record in memory[table].items():  # with the fields that hold the words
                keys = [key for key, value in record.items() if what.lower() in json.dumps(value, ensure_ascii=False).lower()]
                if keys:
                    hits.append(f"- {rid}: {summary(record)}" + f" ({record.get('state')})" * (record.get("state", "current")
                                                                                              != "current") + f" [in {', '.join(keys)}]")
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
    words = {path[len(files.WIKI) + 1:]: sum(bool(re.search(r"\w", word)) for word in pages.ID.sub("", pages.own_text(text)).split())
             for path, text in pages.all_pages(args.deal).items()}  # without the citations
    print(f"Words you wrote: {sum(words.values()):,} in all; " + ", ".join(f"{path} {n:,}" for path, n in words.items()) + ".")
    print(f"Wrote the contents page, the sources page, {'the timeline, ' * pages.own_timeline(args.deal)}the page of checks and the "
          f"view for a browser, {files.WIKI}/wiki.html, which Wiki.html in the deal folder opens.")
    if not pages.own_timeline(args.deal):
        print(f"Wrote no timeline: {files.WIKI}/timeline.md is a page the tool did not write. Rename it, and pages writes the timeline.")


def file_problems(deal, memory):
    """Documents that are missing, changed or not listed. Skipped where the documents are not present."""
    listed = {doc["path"]: doc for doc in files.read_json(deal, files.MANIFEST, {"documents": []})["documents"]}
    present = [path for path in files.listing(deal, files.CLIENT) if path not in (files.MANIFEST, files.CLIENT + "/index.md")]
    wheres = [source["where"] for source in memory["sources"].values() if source.get("where")]
    if (listed or wheres) and not present and not any(files.fingerprint(deal, where) for where in wheres):
        return ["The documents are not in this copy of the folder, so files were not checked, "
                "and a quotation only where its text is here."]
    away = not present and any(path.startswith(files.CLIENT + "/") for path in [*listed, *wheres])  # a copy without it
    found = ["The documents of the client folder are not in this copy of the folder, so they were not checked, "
             "and a quotation only where its text is here."] * away
    found += [f"{path}: in the client folder but not in the manifest" for path in present if path not in listed]
    for path, doc in {} if away else listed.items():
        mark = files.fingerprint(deal, path)
        if mark != doc["fingerprint"]:
            found.append(f"{path}: {'missing' if mark is None else 'changed since it was filed'}")
    for sid, source in memory["sources"].items():
        mark = files.fingerprint(deal, source["where"]) if source.get("where") else None
        if source.get("where") and mark is None and not (away and source["where"].startswith(files.CLIENT + "/")):
            found.append(f"{sid}: {source['where']} was not found in this copy of the folder")
        elif mark and source.get("fingerprint") not in (None, mark):
            found.append(f"{sid}: {source['where']} changed since it was recorded")
        if source.get("extract") and files.fingerprint(deal, source["extract"]) is None:
            found.append(f"{sid}: the extract {source['extract']} was not found in this copy of the folder")
    return found


def plain(text):
    """A text as a quotation is compared: without the marks of Markdown, the tags of HTML or the bars of a table, in one
    case, with single spaces, an accented letter in one spelling. A tag starts with a letter and ends on its line."""
    return " ".join(re.sub(r"</?[A-Za-z][^<>\n]*>|[*_`|]", "", unicodedata.normalize("NFC", text)).split()).casefold()


def quote_problems(deal, memory, only=None):
    """Quotations that are not in the text of their source: its extract, or its original where that is a text file."""
    found, texts = [], {}
    for fid, fact in memory["facts"].items():
        sid, source = fact["source"], memory["sources"][fact["source"]]
        if not fact.get("quote") or fact["state"] == "outdated" or (only is not None and fid not in only):
            continue
        if sid not in texts:
            paths = text_paths(source)
            try:
                texts[sid] = [plain(text) for text in (files.read(deal, path) for path in paths) if text]
            except UnicodeDecodeError:
                texts[sid] = found.append(f"{sid}: its text is not UTF-8, so its quotations were not checked") or []
            if not paths:
                found.append(f"{sid}: facts quote it, and it has no extract to check them against")
        if texts[sid] and not any(plain(fact["quote"]) in text for text in texts[sid]):
            found.append(f"{fid}: its quotation is not in the text of {sid}. Copy the words as the text has them, with nothing left out")
    return found


def copied_quotes(deal, memory):
    """Facts whose quotation is found only in the lines an assistant wrote out from a scan, between "[read from the page]"
    and "[end]": it was compared with that transcription, not with the document."""
    found, texts = [], {}
    for fid, fact in memory["facts"].items():
        sid = fact["source"]
        if not fact.get("quote") or fact["state"] == "outdated":
            continue
        if sid not in texts:
            try:
                raw = [files.read(deal, path) or "" for path in text_paths(memory["sources"][sid])]
            except UnicodeDecodeError:
                raw = []  # `check` reports it
            texts[sid] = [(plain(text), plain(READ.sub(" ", text))) for text in raw] if any(map(READ.search, raw)) else []
        quote = plain(fact["quote"])
        if any(quote in whole for whole, _ in texts[sid]) and not any(quote in rest for _, rest in texts[sid]):
            found.append(f"{fid}, from {sid}, {fact.get('place') or 'no place given'}")
    return found


def check(args):
    memory, std = load(args.deal)
    if args.page:  # one page or draft, and nothing else
        given, known = args.page.replace("\\", "/"), [*pages.all_pages(args.deal), *pages.drafts(args.deal)]
        known = {files.inside(args.deal, path): path for path in known}  # a path in any form: relative, with ./, or whole
        page = next(filter(None, (known.get(files.inside(args.deal, path)) for path in (given, f"{files.WIKI}/{given}"))), None)
        if page is None:
            raise Refused(f"{args.page} is no page of the wiki and no draft. Give its path as check prints it.")
        print("\n".join(f"- {line}" for line in pages.problems(args.deal, memory) if line.startswith(page + ":")) or "No problems found.")
        return
    found = store.verify(memory) + std["notes"] + file_problems(args.deal, memory) + pages.problems(args.deal, memory)
    found += quote_problems(args.deal, memory)
    found += [f"{did}: the decision names nothing it rests on" for did, decision in memory["decisions"].items()
              if not decision.get("rests_on")]
    notes = {cid: {"note": " ".join(check["missing"].values())} for cid, check in std["checks"].items() if "missing" in check}
    for records, keys in ((memory["facts"], ["statement"]), (memory["decisions"], ["decision", "reason"]), (memory["links"], ["why"]),
                          (memory["subjects"], ["note"]), (memory["questions"], ["note"]), (notes, ["note"])):  # notes: on what is missing
        for rid, record in records.items():  # still in use, and names a fact that was replaced
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
    named = [store.DEAL, *memory["subjects"], *memory["links"]]  # what a note on what is missing can be for
    if any(item.get("do") == "note" and item.get("for") not in named for item in items):
        raise Refused("a note names in 'for' the subject or the link the check is asked of, or DEAL: the standard was not changed")
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
    store.record(memory, ", ".join(dict.fromkeys(str(item.get("by", "unknown")) for item in items)), f"Adjusted the standard: {done}")
    files.write_json(args.deal, files.MEMORY, memory)
    print(f"Adjusted the standard for this deal: {done}.")
    opened = {(row["check"], row["for"]) for row in assess.assess(memory, standard.effective(args.deal)) if row["state"] == "open"}
    print("".join(f"Note: {item['target']} is not open for {item['for']}, so its note shows only while it is.\n" for item in items
                  if item["do"] == "note" and (item["target"], item["for"]) not in opened), end="")


def file_documents(args):
    """Move each document to its place: the client folder if the client supplied it and its kind has a slot in the data
    room, the internal sources if not. A text extract made from it goes to the extracts. Then write the index of the client folder."""
    memory, std = load(args.deal)
    kinds = {kind["id"]: kind for kind in std["source_kinds"]}
    items, refused = given(args.filing), []
    items = items if isinstance(items, list) else [items]
    for item in items:
        if (not isinstance(item, dict) or item.get("kind") not in kinds or not isinstance(item.get("file"), str)
                or not isinstance(item.get("extract", ""), str) or not isinstance(item.get("from", "client"), str)):
            raise Refused(f"a filing is a list, and each document in it needs a 'file' and a known 'kind', and may name "
                          f"who it is 'from': {item!r}\nKnown kinds: {', '.join(kinds)}")
    manifest, made = files.read_json(args.deal, files.MANIFEST, {"documents": []}), []
    for item in items:
        name, extract = (item.get(key, "").replace("\\", "/").split("/")[-1] for key in ("file", "extract"))
        slot = kinds[item["kind"]].get("slot") if item.get("from", "client").strip().casefold() == "client" else None  # not the client's: internal
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
        made.append({"ref": f"s{len(made) + 1}", "title": item.get("title", name), "kind": item["kind"], "where": target,
                     **({"extract": f"{files.EXTRACTS}/{extract}"} if extract else {})})
    files.write(args.deal, f"{files.CLIENT}/index.md", pages.documents(memory["deal"]["name"], manifest["documents"], std))
    if made:  # filing records nothing: the documents become sources with the next `add`
        print("Filed, not yet recorded. As sources for `add`, each with its date, what was read and a note:\n"
              + ",\n".join(json.dumps(source, ensure_ascii=False) for source in made))
    if refused:
        raise Refused("Not filed. The tool never overwrites a file: where a name is taken, give the document a name of its "
                      "own and file it again.\n" + "\n".join(refused))


def reshelve(deal):
    """Take the pages of a folder made before the shelves changed to their places, and repoint the links between them:
    the page of the deal becomes the page of the opportunity, the other pages of deal/ go to assets/, those of terms/ to deal/."""
    texts, cut = pages.all_pages(deal), len(files.WIKI) + 1
    old = f"{files.WIKI}/deal/deal.md" in texts and f"{files.WIKI}/{pages.START}" not in texts

    def place(path):
        rel = path[cut:]
        return f"{files.WIKI}/" + (pages.START if rel == "deal/deal.md" else "assets/" + rel[5:] if rel.startswith("deal/")
                                   else "deal/" + rel[6:] if rel.startswith("terms/") else rel)

    for path, text in texts.items() if old else []:
        def repoint(found):
            target = files.beside(path, pages.decoded(found.group(1)))
            return f"]({'../' * place(path)[cut:].count('/')}{pages.encoded(place(target)[cut:])})" if target in texts else found.group()

        files.move(deal, path, place(path))
        files.write(deal, place(path), re.sub(r"\]\((?![a-z]+:)([^)#\s]+\.md)\)", repoint, text))
    if old:
        print("Moved the pages of the wiki to the shelves this version uses, and repointed the links between them.")


def upgrade(args):
    """Put the standard that comes with the tool into the deal folder, say which answers it leaves without a check
    and which checks are new, gone or changed, and write the pages again.
    A record that an earlier version of the tool kept elsewhere is first moved to its place."""
    if files.read(args.deal, files.MEMORY) is None and files.read(args.deal, files.OLD_MEMORY) is not None:
        files.move(args.deal, files.OLD_MEMORY, files.MEMORY)
        print(f"Moved the record to {files.MEMORY}. It was in {files.OLD_MEMORY}.")
    moved = [path for path in (files.BASE, files.INSTITUTION, files.DEAL_LAYER) if files.read(args.deal, path) is None
             and files.read(args.deal, f"{files.OLD_STANDARD}/{path.split('/')[-1]}") is not None]
    for path in moved:  # the standard, beside the record
        files.move(args.deal, f"{files.OLD_STANDARD}/{path.split('/')[-1]}", path)
    if moved:
        left = files.listing(args.deal, files.OLD_STANDARD)
        print(f"Moved {', '.join(path.split('/')[-1] for path in moved)} to Internal/record. They were in {files.OLD_STANDARD}, which "
              + (f"still holds {', '.join(left)}." if left else "is empty now. The tool deletes nothing: remove that folder yourself."))
    reshelve(args.deal)
    memory, was = load(args.deal)
    new, old = files.packaged_standard(), memory["deal"]["standard"]
    if files.read_json(args.deal, files.BASE) == new:
        print(f"The deal already uses the standard that comes with the tool: {old}.")
        refresh(args)
        return
    files.write_json(args.deal, files.BASE, new)
    std = standard.effective(args.deal)  # with the layers of the institution and the deal on top
    store.note_outside_change(memory)
    memory["deal"]["standard"] = new["version"]
    names, before = new.get("renamed", {}), {store.DEAL: {"standard": old}}
    for table, key in (("sources", "kind"), ("facts", "said_by"), ("decisions", "by"), ("decisions", "owner")):  # where such a name is
        for rid, record in memory[table].items():
            if record.get(key) in names:
                before.setdefault(rid, {})[key], record[key] = record[key], names[record[key]]
    store.record(memory, "tool", f"Standard changed from {old} to {new['version']}", changed=before)
    files.write_json(args.deal, files.MEMORY, memory)
    print(f"The deal now uses standard {new['version']}. It used {old}.")
    if len(before) > 1:
        print(f"Records taken to the names the standard now uses ({', '.join(was + ' to ' + now for was, now in names.items())}): "
              f"{len(before) - 1}.")
    gone = [f"{fid}: {answer['check']}" for fid, fact in memory["facts"].items() if fact["state"] != "outdated"
            for answer in fact.get("answers", []) if answer["check"] not in std["checks"]]
    print("Answers that name a check that no longer exists. They stay in the facts and no longer count:\n- "
          + "\n- ".join(gone) if gone else "Every recorded answer still names a check of the standard.")
    was, now = was["checks"], std["checks"]

    def asked(check):  # what an answer depends on: not the evidence a check lists, nor the settled_by of a standard before 4.4.0
        return {key: value for key, value in check.items() if key not in ("settled_by", "ask_whom", "evidence")}

    for title, ids in (("New checks", now.keys() - was.keys()), ("Checks that are gone", was.keys() - now.keys()),
                       ("Checks that changed", [cid for cid in now.keys() & was.keys() if asked(now[cid]) != asked(was[cid])])):
        if ids:  # with the indicator of each, where the check that took the place of a removed one is found
            print(f"{title}: " + (f"{len(ids)} checks. `show <check>` has each." if len(ids) > 40 else ", ".join(
                f"{cid} ({(now.get(cid) or was[cid])['indicator']})" for cid in sorted(ids)) + "."))
    for note in std["notes"]:
        print(f"Note: {note}")
    refresh(args)


def doctor(args):
    packaged = files.packaged_standard()["version"]
    print(f"bankability2, the tool of AIssociate, version {__version__}, with standard {packaged}.")
    print(f"Python {sys.version.split()[0]} on {sys.platform}.")
    if args.deal:
        memory = files.read_json(args.deal, files.MEMORY)
        if memory is None or older(args.deal):
            print(older(args.deal) or f"{args.deal} holds no deal yet.")
            return
        standard.effective(args.deal)  # refuses a folder whose standard is not there
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
    sub.add_argument("--for", dest="about", metavar="ID", help="only what concerns this subject or link, or this pillar")
    sub.add_argument("--since", type=int, help="show changes after this revision")
    sub.add_argument("--json", action="store_true")
    sub = command("add", add, "record a set of changes")
    sub.add_argument("changes", help="a JSON file, or - for standard input")
    sub.add_argument("--try", dest="dry", action="store_true", help="say what the set would record, and write nothing")
    command("show", show, "look something up").add_argument(
        "what", nargs="+", help="an ID, 'log', 'sheet', 'kinds', 'claims', 'sample', 'uncited', 'facts', 'facts <IDs or words>', 'dated', 'text <source>', the name of a "
                                 "kind of record such as 'decisions', or words to search for")
    command("pages", refresh, "fill in the tool's parts of the wiki pages, and write the view for a browser")
    command("check", check, "report what looks wrong").add_argument("page", nargs="?", help="only this page or draft")
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
