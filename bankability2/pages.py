"""The wiki: pages the assistant writes, with the parts the tool fills in.

A page names what it is about at the top. The tool owns the text between its two pairs of
markers, "At a glance" and "Sources", and never touches the rest.
"""
import re

from . import files
from .store import DEAL, TABLES

SHELVES = ("deal", "parties", "people", "topics", "terms", "work")
BEGIN, END = "<!-- tool:begin {} -->", "<!-- tool:end -->"
ID = re.compile(r"\b[A-Z]-\d{3,}\b")
NUMBER = re.compile(r"\d[\d,.]*\d|\d")
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
    return {key.strip(): value.strip() for key, _, value in (line.partition(":") for line in head.splitlines())}


def own_text(text):
    """What the assistant wrote: the page without its top lines, its headings and the parts the tool fills in."""
    if text.startswith("---\n") and "\n---" in text[4:]:
        text = text[text.index("\n---", 4) + 4:]
    text = re.sub(r"<!-- tool:begin \w+ -->.*?<!-- tool:end -->", "", text, flags=re.S)
    return re.sub(r"^#.*$", "", text, flags=re.M)


def fill(text, name, lines):
    """Put lines between a pair of markers. A page without the markers gets them at the end."""
    begin = BEGIN.format(name)
    body = "\n".join([begin, *lines, END])
    if begin in text and END in text[text.index(begin):]:
        start = text.index(begin)
        return text[:start] + body + text[text.index(END, start) + len(END):]
    return text.rstrip() + "\n\n" + body + "\n"


def lead(text):
    """The first sentence under "What it is", or a note that the page is not written yet."""
    found = re.search(r"^## What it is[ \t]*\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
    words = " ".join(found.group(1).split()) if found else ""
    words = re.sub(r"\s*\[[^\]]*\]", "", words)  # leave the citations out
    return re.split(r"(?<=[.!?])\s", words)[0] if words else "*not written yet*"


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
    return ", ".join(map(str, value)) if isinstance(value, list) else str(value)


def check_lines(rows, memory, std):
    """A table of checks with their state, their answer, the assumption they test and what they rest on."""
    lines = ["| Check | For | State | Answer | Assumption | Rests on |", "|---|---|---|---|---|---|"]
    for row in rows:
        check = std["checks"][row["check"]]
        state = ", ".join([row["state"], *row["flags"]])
        tested = check.get("assumption", "")
        if "assumption" in row:
            tested += f" (**{row['assumption']}**)"
        rests = ", ".join(row.get("facts", [])) + (f" ({row['evidence']})" if "evidence" in row else "")
        lines.append(f"| {row['check']} {check['question']} | {name_of(row['for'], memory)} | {state} | "
                     f"{shown(row.get('value', ''))} | {tested} | {rests} |")
    return lines


def glance(rid, memory, std, rows, held):
    """What the memory holds on one subject, one indicator or the deal."""
    lines = []
    if rid == DEAL:
        deal = memory["deal"]
        lines.append(f"- **Stage:** {std['stage_titles'][deal['stage']]}. **Standard:** {deal['standard']}. "
                     f"**Revision:** {memory['log'][-1]['n']}.")
        lines += [f"- {sid} {subject.get('name') or 'not yet named'}: {subject['kind']}"
                  + "".join(f", {role}" for role in sorted(held.get(sid, ()))) for sid, subject in memory["subjects"].items()]
    elif rid in std["by_id"]:
        own = [row for row in rows if row["indicator"] == rid and row["state"] != "not relevant"]
        return [f"**{std['by_id'][rid]['title']}**", "", *check_lines(own, memory, std)]
    elif rid in memory["subjects"]:
        subject = memory["subjects"][rid]
        lines.append(f"- **{rid}:** {subject['kind']}" + "".join(f", {role}" for role in sorted(held.get(rid, ()))))
    else:
        return [f"- {rid}: not a subject, an indicator or the deal"]
    for lid, link in memory["links"].items():
        if rid == DEAL or rid in (link["from"], link["to"]):
            why = f". {link['why']}" if link.get("why") else ""
            lines.append(f"- {lid}: {name_of(lid, memory)} ({link['state']}){why}")
    about = [(fid, fact) for fid, fact in memory["facts"].items() if fact["about"] == rid and fact["state"] == "current"]
    latest = {}
    for fid, fact in about:
        if fact.get("label") and str(fact.get("as_of", "")) >= str(latest.get(fact["label"], (None, {}))[1].get("as_of", "")):
            latest[fact["label"]] = (fid, fact)
    if latest:
        lines += ["", "| Key value | Value | As of | Fact |", "|---|---|---|---|"]
        lines += [f"| {label} | {fact.get('value', '')} {fact.get('unit', '')}".rstrip() + f" | {fact.get('as_of', '')} | {fid} |"
                  for label, (fid, fact) in latest.items()]
    mine = [row for row in rows if row["for"] == rid]
    counts = {}
    for row in mine:
        for name in [row["state"], *row["flags"]]:
            counts[name] = counts.get(name, 0) + 1
    if counts:
        lines += ["", "- **Checks:** " + ", ".join(f"{count} {name}" for name, count in counts.items())]
    lines += [f"- **Assumption disproved:** {std['checks'][row['check']]['assumption']} ({', '.join(row['facts'])})"
              for row in mine if row.get("assumption") == "disproved"]
    lines += [f"- **Looked for and not found:** {fact['statement']} ({fid})" for fid, fact in about if fact.get("nothing_found")]
    lines += [f"- **Open question** {qid} to {q['asked_of']}: {q['text']}" for qid, q in memory["questions"].items()
              if q["state"] == "open" and q.get("about") == rid]
    lines += [f"- **Decision** {did}: {d['decision']} Reason: {d['reason']}" for did, d in memory["decisions"].items()
              if d.get("about") == rid]
    return lines


def cited_sources(text, memory):
    """The sources a page cites, directly or through the facts it cites."""
    lines, seen = [], set()
    for rid in ID.findall(own_text(text)):
        sid = memory["facts"][rid]["source"] if rid in memory["facts"] else rid
        if sid in memory["sources"] and sid not in seen:
            seen.add(sid)
            source = memory["sources"][sid]
            where = f", `{source['where']}`" if source.get("where") else ""
            lines.append(f"- {sid} {source['title']}: {source['kind']}, {source.get('date', 'no date')}{where}")
    return lines


def all_pages(deal):
    paths = [path for path in files.listing(deal, files.WIKI) if path.endswith(".md") and not path.endswith("/index.md")]
    return {path: files.read(deal, path) for path in paths}


def refresh(deal, memory, std, rows, held):
    """Create the pages the graph calls for, fill in the tool's parts of every page, and write the contents page."""
    pages = all_pages(deal)
    owned = {front(text).get("about", "").split(",")[0].strip() for text in pages.values()}
    created = []
    for rid in [DEAL, *memory["subjects"]]:
        if rid not in owned:
            kind = "deal" if rid == DEAL else memory["subjects"][rid]["kind"]
            shelf = "parties" if kind in ("party", "group") else "deal"
            name = memory["deal"]["name"] if rid == DEAL else memory["subjects"][rid].get("name") or rid
            slug = "deal" if rid == DEAL else re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            path = f"{files.WIKI}/{shelf}/{slug}.md"
            if path not in pages:
                pages[path] = SKELETON.format(title=name, about=rid)
                created.append(path)
    contents = {shelf: [] for shelf in SHELVES}
    for path, text in sorted(pages.items()):
        ids = [rid.strip() for rid in front(text).get("about", "").split(",") if rid.strip()]
        lines = []
        for rid in ids:
            lines += glance(rid, memory, std, rows, held) + [""]
        new = fill(fill(text, "glance", lines[:-1]), "sources", cited_sources(text, memory))
        if new != text or path in created:
            files.write(deal, path, new)
        shelf = path[len(files.WIKI) + 1:].split("/")[0]
        title = front(text).get("title") or path
        words = len(own_text(text).split())
        contents.setdefault(shelf, []).append(f"- [{title}]({path[len(files.WIKI) + 1:]}): {lead(text)} ({words} words)")
    index = [f"# {memory['deal']['name']}: contents", ""]
    for shelf, lines in contents.items():
        index += [f"## {shelf.capitalize()}", "", *(lines or ["*no pages*"]), ""]
    files.write(deal, f"{files.WIKI}/index.md", "\n".join(index))
    return created


def numbers(text):
    found = set()
    for token in NUMBER.findall(text):
        try:
            found.add(float(token.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return found


def problems(deal, memory):
    """What looks wrong on the pages: citations that lead nowhere, replaced facts, and numbers no cited record holds."""
    found = []
    for path, text in sorted(all_pages(deal).items()):
        body = own_text(text)
        cited = list(dict.fromkeys(ID.findall(body)))
        known = [rid for rid in cited if any(rid in memory[table] for table in TABLES)]
        found += [f"{path}: cites {rid}, which does not exist" for rid in cited if rid not in known]
        for rid in known:
            entry = memory["facts"].get(rid) or memory["sources"].get(rid) or {}
            if entry.get("state") in ("outdated", "disputed", "replaced"):
                found.append(f"{path}: cites {rid}, which is {entry['state']}"
                             + (f" (replaced by {entry['replaced_by']})" if entry.get("replaced_by") else ""))
        written = " ".join(ID.sub("", body).split())
        if len(written.split()) > 40 and not known:
            found.append(f"{path}: has text and cites nothing")
        held = ""
        for rid in known:
            entry = memory["facts"].get(rid) or memory["sources"].get(rid) or {}
            held += " " + " ".join(str(value) for value in entry.values())
        loose = sorted(n for n in numbers(written) - numbers(held) if n >= 10 or n != int(n))
        if loose:
            shown = ", ".join(f"{n:g}" for n in loose[:8])
            found.append(f"{path}: {len(loose)} numbers are in no cited fact or source: {shown}")
    return found
