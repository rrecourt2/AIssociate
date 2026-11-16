"""The wiki: pages the assistant writes, with the parts the tool fills in, and the same pages as one file for a browser.

A page names what it is about at the top. The tool owns the text between its pairs of markers:
"At a glance", "Key values" and "Sources". It never touches the rest.
"""
import json
import re

from . import files
from .assess import MAIN, VERDICTS, central, claims, holds_still, view
from .store import DEAL, TABLES, live, table_of

SHELVES = ("deal", "parties", "people", "context", "topics", "terms", "work")
BRIEF = SHELVES[2:]  # a page on one of these shelves gets one line that names what it is about
BEGIN, END = "<!-- tool:begin {} -->", "<!-- tool:end -->"
PART = BEGIN + "((?!<!-- tool:begin).)*?" + END  # a begin marker, its lines and its own end marker
ID = re.compile(r"\b[A-Z]-\d{3,}\b")
NUMBER = re.compile(r"\d[\d,.]*\d|\d")
ROUND = str.maketrans("[]", "()")  # square brackets in a title would end the link that carries it
STALE = ("outdated", "disputed", "replaced")  # the states of a record that something newer took the place of
# One of those words and a colon, at the start of a paragraph, of a sentence or of a bracket. What follows may cite a
# record in that state: "Disputed:" a disputed one, "Outdated:" or "Replaced:" one that something newer took the place of.
MARKED = re.compile(r"(?:^|[.!?|][*_]*\s+|\()[*_]*(" + "|".join(STALE) + r")[*_]*:", re.I)
SKELETON = """---
title: {title}
about: {about}
checked:
---

# {title}

## What it is


## At a glance

<!-- tool:begin glance -->
<!-- tool:end -->

## What we know


## Assumptions and open points


## Sources

<!-- tool:begin sources -->
<!-- tool:end -->
"""


def front(text):
    """The lines between the two "---" at the top of a page, as a dict."""
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        return {}
    head = text[4:text.index("\n---", 4)]
    return {key.strip(): value.strip().strip("\"'") for key, _, value in (line.partition(":") for line in head.splitlines())}


def own_text(text):
    """What the assistant wrote: the page without its top lines, its headings and the parts the tool fills in."""
    if text.startswith("---\n") and "\n---" in text[4:]:
        text = text[text.index("\n---", 4) + 4:]
    text = re.sub(PART.format(r"\w+"), "", text, flags=re.S)
    return re.sub(r"^#.*$", "", text, flags=re.M)


def fill(text, name, lines, heading=""):
    """Put lines between a pair of markers. A page without the markers gets them at the end, under the heading."""
    body = "\n".join([BEGIN.format(name), *lines, END])
    found = re.search(PART.format(name), text, flags=re.S)
    if found:
        return text[:found.start()] + body + text[found.end():]
    return text.rstrip() + "\n\n" + heading + body + "\n"


def blocks(text):
    """The paragraphs, list items and table rows of a text, each as one line without its list marker. The head row of a
    table is left out: it names the columns."""
    found = [""]
    for line in text.splitlines():
        start = re.match(r"\s*(?:[-*+>]\s+|\d+[.)]\s+|\|)", line)
        if re.match(r"\s*\|?\s*:?-+:?\s*\|", line):  # the line of dashes under a head row
            found[-1] = ""
        elif start or not line.strip():
            found.append(line[start.end():].strip() if start else "")
        else:
            found[-1] = (found[-1] + " " + line.strip()).strip()
    return [block for block in found if block]


def lead(text):
    """The first sentence the assistant wrote on a page, or a note that the page is not written yet."""
    words = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", next(iter(blocks(own_text(text))), ""))  # a link becomes its words
    words = re.sub(r"\s*\[[^\]]*\]", "", words)  # leave the citations out
    for stop in re.finditer(r"[.!?](?=\s+[A-Z\"'(\[*_]|\s*$)", words):  # a capital letter starts the next sentence
        if not re.search(r"\b[A-Z][a-z]?$|\.[a-z]$", words[:stop.start()]):  # not an initial or an abbreviation: J., Co., e.g.
            return words[:stop.end()]
    return words or "*not written yet*"


def encoded(path):
    """A path as the target of a Markdown link."""
    return re.sub(r"[ ()#?%]", lambda found: f"%{ord(found.group()):02X}", path)


def name_of(rid, memory):
    if rid == DEAL:
        return "the deal"
    if rid in memory["subjects"]:
        return memory["subjects"][rid].get("name") or f"the {memory['subjects'][rid]['kind']} not yet named ({rid})"
    if rid in memory["links"]:
        link = memory["links"][rid]
        return f"{name_of(link['from'], memory)} {link['type']} {name_of(link['to'], memory)}"
    return rid


def shown(value):
    """An answer as a person reads it."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)) and abs(value) >= 10000:
        return f"{value:,}"  # a large number is read more easily with separators. A year stays as it is
    return ", ".join(map(str, value)) if isinstance(value, list) else str(value)


def check_lines(rows, memory, std):
    """A table of checks with their state, their answer, the assumption they test and what they rest on."""
    lines = ["| Check | For | State | Answer | Assumption | Rests on |", "|---|---|---|---|---|---|"]
    for row in rows:
        check = std["checks"][row["check"]]
        state = ", ".join([row["state"], *row["flags"]]) + (f", decision {row['action']}" if "action" in row else "")
        tested = ("Mitigant: " if check.get("mitigant") else "") + check.get("assumption", "")
        if "against" in row:
            tested += " (**the answer goes against it**)" if row["against"] else (
                " (**stands" + (", on someone's own word" if row.get("own_word") else "") + "**)")
        rests = ", ".join(row.get("facts", [])) + (f" ({row['evidence']})" if "evidence" in row else "")
        lines.append(f"| {row['check']} {check['question']} | {name_of(row['for'], memory)} | {state} | "
                     f"{shown(row.get('value', ''))} | {tested} | {rests} |")
    return lines


def claim_lines(found, memory, std):
    """The claims that need attention, one per line, and a count of the others."""
    lines, counts = [], {}
    for claim in found:
        ind = std["by_id"][claim["indicator"]]
        counts[claim["stands"]] = counts.get(claim["stands"], 0) + 1
        about = f"{ind['title']} ({name_of(claim['for'], memory)})"
        if claim["stands"] == "challenged":
            tested = "; ".join(f"{std['checks'][cid]['assumption']} [{cid}]" for cid in claim["against"])
            parts = [f"- **Challenged:** {about}. The claim: {ind['claim']} The answers go against: {tested}."]
            known = [f"{std['checks'][cid]['assumption']} [{cid}]: {state}" for cid, state in claim["mitigants"].items()
                     if state != "not known"]
            unknown = [cid for cid, state in claim["mitigants"].items() if state == "not known"]
            if known:
                parts.append("Mitigants: " + "; ".join(known) + ".")
            if unknown:
                parts.append(f"Mitigants not known yet: {', '.join(unknown)}.")
            if claim["actions"]:
                parts.append(f"Decision: {', '.join(claim['actions'])}.")
            lines.append(" ".join(parts))
        elif claim["stands"] == "contested":
            lines.append(f"- **Contested:** {about}. Facts disagree on {', '.join(claim['contested'])}.")
        lines += [f"- **Look again:** {about}. {reason}." for reason in claim["look_again"]]
    said = sum(claim["own_word"] for claim in found)
    if counts:
        lines.append("- **Claims:** " + ", ".join(f"{counts[name]} {name}" for name in VERDICTS if name in counts)
                     + (f". Answers that rest only on someone's own word: {said}" if said else "") + ".")
    return lines


def linked(rid, memory, where, here):
    """The name of the deal, a subject or a link. Each name is a relative link to its page, where it has another page."""
    if rid in memory["links"]:
        link = memory["links"][rid]
        return (f"{linked(link['from'], memory, where, here)} {link['type'].replace('_', ' ')} "
                f"{linked(link['to'], memory, where, here)}")
    name = name_of(rid, memory)
    return f"[{name}]({'../' * here.count('/')}{encoded(where[rid])})" if where.get(rid, here) != here else name


def described(sid, memory, std, held):
    """The kind of a subject and the roles it holds, or that it has ended."""
    kind = next(kind for kind in std["subject_kinds"] if kind["id"] == memory["subjects"][sid]["kind"])
    ended = ["ended"] if memory["subjects"][sid].get("state") == "ended" else []
    return ", ".join([kind["id"], *filter(None, [kind.get("shown_as")]), *sorted(held.get(sid, ())), *ended]).replace("_", " ")


def challenges(found, std, name):
    """One line per claim that is challenged or contested: the tests against it, its mitigants and any decision on it."""
    lines = []
    for claim in found:
        about = f"{std['by_id'][claim['indicator']]['title']} ({name(claim['for'])})"
        if claim["stands"] == "challenged":
            states = sorted(claim["mitigants"].values())
            tested = "; ".join(f"{std['checks'][cid]['assumption']} ({cid})" for cid in claim["against"])
            parts = [f"The answers go against: {tested}"]
            if states:
                parts.append("Mitigants: " + ", ".join(f"{states.count(state)} {state}" for state in dict.fromkeys(states)))
            if claim["actions"]:
                parts.append(f"Decision: {', '.join(claim['actions'])}")
            lines.append(f"- **Challenged:** {about}. {'. '.join(parts)}.")
        elif claim["stands"] == "contested":
            lines.append(f"- **Contested:** {about}. Facts disagree on {', '.join(claim['contested'])}.")
    return lines


def about_line(ids, found, memory, std, name):
    """One line that names what a page is about. An indicator comes with where its claim stands, for each subject."""
    named = []
    for rid in ids:
        if rid in std["by_id"]:
            stands = ", ".join(f"{claim['stands']} for {name(claim['for'])}" for claim in found if claim["indicator"] == rid)
            named.append(f"{std['by_id'][rid]['title']} ({rid}): {stands or 'not asked yet'}")
        else:
            known = rid == DEAL or table_of(memory, rid) in ("subjects", "links")
            named.append(name(rid) if known else f"{rid}, which the record does not hold")
    return [f"- **About:** {'; '.join(named)}."] if named else []


def brief(ids, memory, here):
    """Whether a page gets one line that names what it is about and no more: by its shelf, or because it is not about subjects."""
    return here.split("/")[0] in BRIEF or not all(rid == DEAL or rid in memory["subjects"] for rid in ids)


def glance(ids, memory, std, rows, held, where, here):
    """What the record holds on what a page is about, kept short. Names link to their pages. The page of the deal gets
    the subjects at its centre and the claims, the page of a subject its links, questions and decisions, any other one
    line. Links and subjects that have ended are left out: `show` has them."""
    def name(rid):
        return linked(rid, memory, where, here)

    found, lines = claims(rows, memory, std), []
    if brief(ids, memory, here):
        return about_line(ids, found, memory, std, name)
    for rid in ids:
        near = [(lid, link) for lid, link in memory["links"].items()
                if rid in (DEAL, link["from"], link["to"]) and holds_still(link, memory)]
        mine = [claim for claim in found if rid == DEAL or claim["for"] in (rid, *(lid for lid, _ in near))]
        if rid == DEAL:
            deal = memory["deal"]
            lines.append(f"- **Stage:** {std['stage_titles'][deal['stage']]}. **Standard:** {deal['standard']}. "
                         f"**Revision:** {memory['log'][-1]['n']}.")
            for sid, subject in live(memory).items():  # the loan and the main roles, each with the links that start there
                if not central(sid, memory, held):
                    continue
                does = "; ".join(f"{link['type'].replace('_', ' ')} {name_of(link['to'], memory)} ({lid}"
                                 + ("" if link["state"] == "confirmed" else f", {link['state']}") + ")"
                                 for lid, link in near if link["from"] == sid)
                lines.append(f"- {sid} {name(sid) if subject.get('name') else 'not yet named'}: "
                             f"{described(sid, memory, std, held)}" + (f". {does[0].upper()}{does[1:]}." if does else ""))
        else:
            lines.append(f"- **{rid}:** {described(rid, memory, std, held)}")
            lines += [f"- {lid}: {name(lid)} ({link['state']})" for lid, link in near]
        if rid == DEAL:
            lines.append(f"- Every other subject is on the [contents page]({'../' * here.count('/')}index.md).")
            lines += ["", "| Pillar | " + " | ".join(verdict.capitalize() for verdict in VERDICTS) + " |",
                      "|---|" + "---|" * len(VERDICTS)]
            lines += [f"| {pillar['title']} | " + " | ".join(map(str, view(found, std)[pillar["id"]])) + " |"
                      for pillar in std["pillars"]]
        lines += ["", *challenges(mine, std, name)]
        if rid != DEAL:
            lines += [f"- **Open question** {qid} to {q['asked_of']}: {q['text']}" for qid, q in memory["questions"].items()
                      if q["state"] == "open" and q.get("about") == rid]
            lines += [f"- **Decision** {did}: {d['decision']}" for did, d in memory["decisions"].items() if d.get("about") == rid]
        lines.append("")
    while lines and not lines[-1]:
        lines.pop()
    return lines


def key_values(ids, memory, here):
    """The latest value under each label of the facts about the deal or the subjects of a page, as a table."""
    rows = []
    for rid in [] if brief(ids, memory, here) else ids:
        latest, whose = {}, f" ({name_of(rid, memory)})" if len(ids) > 1 else ""
        for fid, fact in memory["facts"].items():
            if (fact["about"] == rid and fact["state"] == "current" and fact.get("label")
                    and str(fact.get("as_of", "")) >= str(latest.get(fact["label"], (None, {}))[1].get("as_of", ""))):
                latest[fact["label"]] = (fid, fact)
        rows += [f"| {label}{whose} | {shown(fact.get('value', ''))} {fact.get('unit', '')}".rstrip()
                 + f" | {fact.get('as_of', '')} | {fid} |" for label, (fid, fact) in latest.items()]
    return ["| Key value | Value | As of | Fact |", "|---|---|---|---|", *rows] if rows else []


def cited_sources(text, memory, here):
    """The sources a page cites, directly or through the facts it cites, each with a link from the page to its document."""
    lines, seen = [], set()
    for rid in ID.findall(own_text(text)):
        sid = memory["facts"][rid]["source"] if rid in memory["facts"] else rid
        if sid in memory["sources"] and sid not in seen:
            seen.add(sid)
            source = memory["sources"][sid]
            up = "../" * (here.count("/") + files.WIKI.count("/") + 1)  # from the page to the deal folder
            where = f", [{source['where']}]({up}{encoded(source['where'])})" if source.get("where") else ""
            read = f", read: {source['read']}" if source.get("read") not in (None, "full") else ""  # what was not read in full
            lines.append(f"- {sid} {source['title']}: {source['kind']}, {source.get('date', 'no date')}{read}{where}")
    return lines


def source_lines(memory):
    """Every source of the record on one page: what it is, how far it was read, how many facts rest on it, and links
    from the wiki folder to its original and its extract."""
    lines = [f"# {memory['deal']['name']}: sources", "", "Every source of the record, with the number of facts taken "
             "from it and links to the original and to its extract.", ""]
    for sid, source in memory["sources"].items():
        facts = sum(fact["source"] == sid for fact in memory["facts"].values())
        notes = [source["kind"], source.get("date", "no date"), source.get("read") and f"read: {source['read']}",
                 source["state"] != "current" and source["state"], f"facts: {facts}"]
        held = "".join(f" [{name}](../../{encoded(source[key])})" for key, name in (("where", "Original"), ("extract", "Extract"))
                       if source.get(key))
        lines.append(f"- {sid} {source['title']}: {', '.join(filter(None, notes))}.{held}")
    return lines + [""]


def all_pages(deal):
    paths = [path for path in files.listing(deal, files.WIKI)
             if path.endswith(".md") and path[len(files.WIKI) + 1:] not in ("index.md", "sources.md")]
    return {path: files.read(deal, path) for path in paths}


def about(text):
    """The IDs a page says it is about."""
    return [rid.strip() for rid in front(text).get("about", "").split(",") if rid.strip()]


def documents(name, listed, std):
    """The index of the client folder: each document under its folder and sub-folder of the data room, with a link from
    the client folder, then the slots that are always expected and still empty."""
    kinds = {kind["id"]: kind["title"] for kind in std["source_kinds"]}
    lines = [f"# {name}: documents", "", "Every document the client shared is in this folder. They are listed here by the "
             "folders of the data room.", ""]
    missing = []
    for folder in std["dataroom"]["folders"]:
        held = []
        for sub in folder["sub_folders"]:
            docs = [f"- [{doc['title'].translate(ROUND)}]({encoded(doc['path'][len(files.CLIENT) + 1:])}): "
                    + ", ".join(filter(None, [kinds.get(doc["kind"], doc["kind"]), doc.get("party"), doc.get("period")]))
                    + f". Slot {slot['id']} {slot['title']}."
                    for slot in sub["slots"] for doc in listed if doc["slot"] == slot["id"]]
            if docs:
                held += [f"### {sub['id']} {sub['title']}", "", *docs, ""]
            missing += [f"- {slot['id']} {slot['title']}" for slot in sub["slots"]
                        if slot["expected"] == "always" and not any(doc["slot"] == slot["id"] for doc in listed)]
        if held:
            lines += [f"## {folder['id']} {folder['title']}", "", *held]
    return "\n".join([*lines, "## Always expected and not here yet", "", *(missing or ["*nothing*"]), ""])


def refresh(deal, memory, std, rows, held):
    """Create the pages the structure calls for, fill in the tool's parts of every page, and write the contents page and
    the browser view. Returns the pages it created, the other pages it changed and the number it left as they were."""
    pages, cut = all_pages(deal), len(files.WIKI) + 1
    named = [(path[cut:], about(text)) for path, text in sorted(pages.items())]
    where = {}  # the page of the deal and of each subject, as a path from the wiki folder. First its own page: a page
    for path, ids in named:  # belongs to the first ID it names, and a page about people, context or a topic to nobody
        if ids and path.split("/")[0] not in BRIEF:
            where.setdefault(ids[0], path)
    created, changed = [], []
    wanted = [sid for sid, subject in memory["subjects"].items() if subject.get("name") and held.get(sid, set()) & MAIN]
    for rid in [DEAL, *wanted]:
        if rid not in where:
            kind = "deal" if rid == DEAL else memory["subjects"][rid]["kind"]
            shelf = "parties" if kind in ("party", "group", "person") else "deal"
            name = memory["deal"]["name"] if rid == DEAL else memory["subjects"][rid]["name"]
            slug = "deal" if rid == DEAL else re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or rid.lower()
            path = f"{files.WIKI}/{shelf}/{slug}.md"
            if path in pages:  # another subject has the same name
                path = f"{files.WIKI}/{shelf}/{slug}-{rid.lower()}.md"
            pages[path], where[rid] = SKELETON.format(title=name, about=rid), path[cut:]
            created.append(path)
    for path, ids in named:  # what has no page of its own is found on the first page that names it
        for rid in ids:
            where.setdefault(rid, path)
    contents = {shelf: [] for shelf in SHELVES}
    for path, text in sorted(pages.items()):
        new = fill(text, "glance", glance(about(text), memory, std, rows, held, where, path[cut:]))
        values = key_values(about(text), memory, path[cut:])
        if values or BEGIN.format("values") in new:  # a page that has no key values gets no part for them
            new = fill(new, "values", values, "## Key values\n\n")
        new = fill(new, "sources", cited_sources(text, memory, path[cut:]))
        if new != text or path in created:
            files.write(deal, path, new)
            if path not in created:
                changed.append(path)
        pages[path], title = new, front(text).get("title") or path[cut:]
        contents.setdefault(path[cut:].split("/")[0], []).append(
            f"- [{title}]({encoded(path[cut:])}): {lead(text)}")
    index = [f"# {memory['deal']['name']}: contents", "", "[Sources](sources.md) lists every source of the record. "
             f"[Documents](../../{encoded(files.CLIENT)}/index.md) lists what the client shared.", ""]
    for shelf, lines in contents.items():
        if lines:
            index += [f"## {shelf.capitalize()}", "", *lines, ""]
    others = [f"- {sid} {subject.get('name') or 'not yet named'}: {described(sid, memory, std, held)}"
              + (f". {subject['note']}" if subject.get("note") else "")
              for sid, subject in live(memory).items() if sid not in where]
    if others:
        index += ["## Subjects without a page", "", *others, ""]
    sources = "\n".join(source_lines(memory))
    files.write(deal, f"{files.WIKI}/index.md", "\n".join(index))
    files.write(deal, f"{files.WIKI}/sources.md", sources)
    listed = files.read_json(deal, files.MANIFEST, {"documents": []})["documents"]
    client = f"../../{files.CLIENT}/index.md"  # the index of the client folder, as a path from the wiki folder
    texts = {"index.md": "\n".join(index), "sources.md": sources, **{path[cut:]: text for path, text in sorted(pages.items())},
             client: documents(memory["deal"]["name"], listed, std)}
    data = {"name": memory["deal"]["name"], "revision": memory["log"][-1]["n"], "shelves": SHELVES, "pages": texts,
            "documents": client, "where": where, **{table: memory[table] for table in TABLES}}
    filled = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")  # so that no text can end the script it sits in
    files.write(deal, f"{files.WIKI}/wiki.html", files.packaged("wiki.html").replace("{{DATA}}", filled))
    return created, changed, len(pages) - len(created) - len(changed)


def numbers(text):
    found = set()
    for token in NUMBER.findall(text):
        try:
            found.add(float(token.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return found


def problems(deal, memory):
    """What looks wrong on the pages and in the drafts: citations and links that lead nowhere, citations of a record that
    was replaced and is not marked so, numbers that no record cited in the same paragraph holds, and a page that no
    other page links to."""
    found, there, pages, reached = [], set(files.listing(deal, files.WIKI)), all_pages(deal), set()
    drafts = {path: files.read(deal, path) for path in files.listing(deal, files.OUTPUTS)  # not those in a sub-folder
              if path.endswith(".md") and "/" not in path[len(files.OUTPUTS) + 1:]}
    for path, text in sorted({**pages, **drafts}.items()):
        body = own_text(text)
        notes = path == f"{files.WIKI}/work/working-notes.md"  # they say how to work, and need not cite the record
        cited = list(dict.fromkeys(ID.findall(body)))
        found += [f"{path}: cites {rid}, which does not exist" for rid in cited if not table_of(memory, rid)]
        if len(ID.sub("", body).split()) > 40 and not notes and not any(table_of(memory, rid) for rid in cited):
            found.append(f"{path}: has text and cites nothing")
        for link in re.findall(r"\]\((?![a-z]+:)([^)#\s]+\.md)", text):  # a link to another page, also in the tool's parts
            target = files.beside(path, re.sub(r"%([0-9A-Fa-f]{2})", lambda code: chr(int(code.group(1), 16)), link))
            if path in pages and target != path:
                reached.add(target)
            if target.startswith(files.WIKI + "/") and target not in there:
                found.append(f"{path}: links to {link}, which is not there")
        stale = {}
        for block in blocks(body):
            marks, held = list(MARKED.finditer(block)), ""
            for cite in ID.finditer(block):
                entry = memory.get(table_of(memory, cite.group()), {}).get(cite.group(), {})
                word = [mark.group(1).lower() for mark in marks if mark.start() < cite.start()][-1:]  # the nearest before it
                if entry.get("state") in STALE and not (word and (entry["state"] == "disputed") == (word[0] == "disputed")):
                    stale[cite.group()] = entry
                source = memory["sources"].get(entry.get("source"), {})  # of a fact's source the title and the date count,
                held += " ".join(f" {value}" for key, value in [*entry.items(), *source.items()]  # not its map of the document
                                 if key not in ("fingerprint", "rev") and (key != "map" or "map" in entry))
            written = re.sub(r"\]\([^)]*\)|\b[A-Z]+_\w+", " ", ID.sub("", block))  # no IDs of records or checks, no link targets
            loose = sorted(n for n in numbers(written) - numbers(held) if n >= 10 or n != int(n))
            if loose and not notes:
                found.append(f"{path}: \"{' '.join(block.split()[:6])} ...\" has {', '.join(f'{n:g}' for n in loose[:8])}, "
                             f"which no record cited in that paragraph holds")
        found += [f"{path}: cites {rid}, which is {entry['state']}" + (f" (replaced by {entry['replaced_by']})" if entry.get(
            "replaced_by") else "") + f". Cite what took its place, or start the sentence with \"{entry['state'].capitalize()}:\""
            for rid, entry in stale.items()]
    return found + [f"{path}: no other page links to it" for path in sorted(pages)  # the page of the deal is the way in
                    if path not in reached and path != f"{files.WIKI}/deal/deal.md" and not path.startswith(f"{files.WIKI}/work/")]
