"""The wiki: pages the assistant writes, with the parts the tool fills in, and the same pages as one file for a browser.

A page names what it is about at the top. The tool owns the text between its pairs of markers:
"At a glance", "Key values" and "Sources". It never touches the rest.
"""
import json
import re

from . import files
from .assess import MAIN, VERDICTS, central, claims, holds_still, next_list, tally, view
from .store import DEAL, TABLES, live, table_of

SHELVES = {"opportunity": "Opportunity", "assets": "Assets and projects", "parties": "Parties", "people": "People",
           "context": "Context", "topics": "Topics", "deal": "Deal", "work": "Work"}  # the folders of the wiki, and their headings
BRIEF = ("people", "context", "topics", "deal", "work")  # a page on one of these gets one line that names what it is about
START = "opportunity/opportunity.md"  # the page of the opportunity: the way in
ORDER = ("contested", "open", "answered", "waiting", "parked", "off", "not relevant")  # what is to answer comes first
DOOR = """<!DOCTYPE html>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=Internal/wiki/wiki.html">
<title>Wiki</title>
<p><a href="Internal/wiki/wiki.html">Open the wiki</a></p>
"""  # Wiki.html in the deal folder: the way in to the view for a browser
TIMELINE = "# Timeline\n\nWhat was recorded, when (UTC) and by whom, "  # how the tool's timeline starts
BEGIN, END = "<!-- tool:begin {} -->", "<!-- tool:end -->"
PART = BEGIN + "((?!<!-- tool:begin).)*?" + END  # a begin marker, its lines and its own end marker
ID = re.compile(r"\b[A-Z]-\d{3,}\b")
NUMBER = re.compile(r"(\d[\d,.]*\d|\d)((?:\s?(?:thousand|million|billion|trillion|mn|bn|tn)|k|m)\b)?", re.I)  # k and m only against it
SCALE = {"thousand": 1e3, "k": 1e3, "million": 1e6, "mn": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9, "trillion": 1e12, "tn": 1e12}
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


def decoded(link):
    """The target of a Markdown link as a path."""
    return re.sub(r"%([0-9A-Fa-f]{2})", lambda code: chr(int(code.group(1), 16)), link)


def name_of(rid, memory):
    if rid == DEAL:
        return "the opportunity"
    if rid in memory["subjects"]:  # the short name, where it has one
        subject = memory["subjects"][rid]
        return subject.get("short") or subject.get("name") or f"the {subject['kind']} not yet named ({rid})"
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


def shown_state(row):
    """The state of a check for one subject, with its marks: thin, old, and own word for a favourable answer that rests
    only on what a party says of itself."""
    return ", ".join([row["state"], *row["flags"], *["own word"] * bool(row.get("own_word"))])


def by_stage(rows, std):
    """The open checks, counted by the stage each is ideally answered by: most are work for a later stage."""
    due = [row["due_by"] for row in rows if row["state"] == "open"]
    return ", ".join(f"{std['stage_titles'][stage]} {due.count(stage)}" for stage in std["stage_ids"] if stage in due)


def check_lines(rows, memory, std):
    """A table of checks with their state, their answer or what is missing, the assumption they test and what they rest on."""
    lines = ["| Check | For | State | Answer | Assumption | Rests on |", "|---|---|---|---|---|---|"]
    for row in rows:
        check = std["checks"][row["check"]]
        state = shown_state(row) + (f", decision {row['action']}" if "action" in row else "")
        tested = ("Mitigant: " if check.get("mitigant") else "") + check.get("assumption", "")
        if "against" in row:
            tested += " (**the answer goes against it**)" if row["against"] else " (**holds on this answer**)"
        rests = ", ".join(row.get("facts", [])) + (f" ({row['evidence']})" if "evidence" in row else "")
        lines.append(f"| {row['check']} {check['question']} | {name_of(row['for'], memory)} | {state} | "
                     f"{shown(row.get('value', ''))}{'missing: ' + row['missing'] if 'missing' in row else ''} | {tested} | {rests} |")
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
            lines += [f"- **Open question** {qid} to {q['asked_of']}: {q['text']}" + f" Note: {q.get('note')}" * bool(q.get("note"))
                      for qid, q in memory["questions"].items() if q["state"] == "open" and q.get("about") == rid]
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
                       if source.get(key) and source["state"] == "current")  # what was replaced is listed, not linked
        lines.append(f"- {sid} {source['title']}: {', '.join(filter(None, notes))}.{held}")
    return lines + [""]


def check_page(memory, std, rows, todo, where):
    """Every check of the standard as it stands for this deal: first what matters most, then each claim with its checks,
    what is to answer first. The view for a browser lets a reader choose which states to see."""
    def name(rid):
        return linked(rid, memory, where, "checks.md")

    def codes(ids):
        return " or ".join(f"`{cid}`" for cid in dict.fromkeys(ids))

    def cells(row):
        check, waits = std["checks"][row["check"]], row.get("waits_for", [])
        if row["state"] in ("answered", "contested"):
            note = f"{shown(row.get('value', ''))}{' (**against the claim**)' * bool(row.get('against'))} [{', '.join(row['facts'])}]"
        elif row["state"] == "not relevant":
            note = "given the answer to " + codes([cond["check"] for cond in check.get("when", [])] or check.get("after", []))
        elif row["state"] != "waiting":  # open, parked or off: the decision or the reason, where there is one
            agreed = "agreed action" if row["state"] == "open" else "decision"
            note = f"{agreed} {row['action']}" if "action" in row else row.get("reason", "")
            note += f"{'. ' * bool(note)}Missing: {row.get('missing')}" * ("missing" in row)
        elif row["for"] in memory["subjects"] and not memory["subjects"][row["for"]].get("name"):
            note = "until it is named"
        elif check.get("mitigant") or not waits:
            note = f"only if {codes(waits) or 'a test'} goes against the claim"
        else:
            note = f"until `{waits[0]}` is answered: {std['checks'][waits[0]]['question'][:80].rsplit(' ', 1)[0]} ..."
        found = [shown_state(row),
                 f"{'Mitigant: ' * bool(check.get('mitigant'))}{check['question']} `{row['check']}`"
                 + f" *{check.get('matters')}*" * bool(check.get("matters")), name(row["for"]), note, std["stage_titles"][row["due_by"]]]
        return [" ".join(str(cell).replace("|", "/").split()) for cell in found]  # so that no cell ends early

    def table(mine):
        """One line for a check, its state and its answer: the subjects that share them stand together in one cell."""
        merged = {}
        for state, check, whom, *rest in map(cells, mine):
            merged.setdefault((state, check, *rest), []).append(whom)
        return ["| " + " | ".join([state, check, "; ".join(whom), *rest]) + " |" for (state, check, *rest), whom in merged.items()]

    counts, found, stage_of, due = tally(rows), claims(rows, memory, std), std["stage_ids"].index, by_stage(rows, std)
    head = ["| State | Check | For | Answer, or what it waits for | Ideally by |", "|---|---|---|---|---|"]
    lines = [f"# {memory['deal']['name']}: checks", "", "Every check of the standard as it stands for this opportunity, at the stage "
             f"{std['stage_titles'][memory['deal']['stage']]}. Open: it can be answered now. Waiting: an earlier answer or a name "
             "comes first. Not relevant: an earlier answer made it so. Contested: two facts answer it differently. Off: a decision "
             "or an adjustment set it aside. Thin or old: the evidence is weaker or older than this stage asks for. Own word: the "
             "favourable answer to a test rests only on what a party says of itself, or only on evidence the check counts as "
             "stated.", "",
             "**" + ", ".join(f"{counts[state]} {state}" for state in ORDER if state in counts) + ".** Answers that go against "
             f"their claim: {sum(bool(row.get('against')) for row in rows)}."
             + f" Open, by the stage each is ideally answered by: {due}." * bool(due)]
    marked = {}  # what was marked for this deal: one row for a check, with its reason, and each subject with its state
    for row in sorted(rows, key=lambda row: ORDER.index(row["state"])):  # what is to answer first
        if std["checks"][row["check"]].get("matters"):
            marked.setdefault(row["check"], []).append((row["state"], cells(row)))
    key = []
    for mine in marked.values():
        states = ", ".join(dict.fromkeys(state for state, _ in mine))
        whom = "; ".join(f"{c[2]}: {c[0]}" + (f", {c[3].replace('; ', ', ')}" if state in ("answered", "contested") else "") for state, c in mine)
        key.append(f"| {states} | {mine[0][1][1]} | {whom} | {mine[0][1][4]} |")
    lines += ["", "## What matters most", "", "| State | Check | For | Ideally by |", "|---|---|---|---|", *key] * bool(key)
    screened = [sid for sid, subject in live(memory).items() if subject["kind"] in ("party", "person") and subject.get("name")]
    lines += ["", "## Names in the record", "", "The parties and people that the record names, for instance for a screening: "
              + ", ".join(map(name, screened)) + "; and the directors and managers that the facts about them name."] * bool(screened)
    for pillar in std["pillars"]:
        within = tally(row for row in rows if std["by_id"][row["indicator"]]["pillar"] == pillar["id"])
        lines += ["", f"## {pillar['title']}", "",
                  ", ".join(f"{within[state]} {state}" for state in ORDER if state in within) + "."] * bool(within)
        for ind in std["indicators"]:
            mine = sorted((row for row in rows if row["indicator"] == ind["id"]),
                          key=lambda row: (ORDER.index(row["state"]), stage_of(row["due_by"])))
            if ind["pillar"] == pillar["id"] and mine:
                stands = "; ".join(f"{claim['stands']} for {name(claim['for'])}" for claim in found if claim["indicator"] == ind["id"])
                lines += ["", f"### {ind['title']}", "", f"*{ind['claim']}*" + f" Where it stands: {stands}." * bool(stands), "",
                          *head, *table(mine)]
    lines += ["", "## Documents that are not in the folder", "",
              *(f"- {doc['title']} ({doc['slot']}): {doc['why']}" for doc in todo["documents"])] * bool(todo["documents"])
    return "\n".join([*lines, ""])


def timeline(memory):
    """The log of the record as a page: each revision, the newest first and by day, with who made it, its note and what it touched."""
    lines, day = [TIMELINE + "the newest first: the tool writes this page from the log of the record."], None
    for entry in reversed(memory["log"]):
        if entry["at"][:10] != day:
            day = entry["at"][:10]
            lines += ["", f"## {day}", ""]
        ids = [*entry.get("added", []), *entry.get("changed", {})]
        kinds = [table_of(memory, rid) for rid in ids]
        touched = [f"{kinds.count(t)} {t if kinds.count(t) > 1 else t[:-1]}" for t in TABLES if t in kinds] + ["the opportunity"] * (DEAL in ids)
        lines.append(f"- **Revision {entry['n']}**, {entry['at'][11:16]}, {' '.join(entry['by'].split())}: {' '.join(entry['note'].split())}"
                     + f" ({', '.join(touched)})" * bool(touched))
    return "\n".join([*lines, ""])


def own_timeline(deal):
    """Whether the timeline is the tool's to write: there is no such page yet, or the tool wrote it. Before 0.9.0 it was an ordinary name."""
    text = files.read(deal, f"{files.WIKI}/timeline.md")
    return text is None or text.startswith(TIMELINE)


def all_pages(deal):
    paths = [path for path in files.listing(deal, files.WIKI)
             if path.endswith(".md") and path[len(files.WIKI) + 1:] not in ("index.md", "sources.md", "checks.md", "timeline.md")]
    return {path: files.read(deal, path) for path in paths}


def drafts(deal):
    """The drafts directly in the outputs folder. One in a sub-folder was sent or replaced, and is left alone."""
    return {path: files.read(deal, path) for path in files.listing(deal, files.OUTPUTS)
            if path.endswith(".md") and "/" not in path[len(files.OUTPUTS) + 1:]}


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
    has_page = {rid for path, ids in named if path.split("/")[0] not in BRIEF for rid in ids}  # also one it shares
    wanted = [sid for sid, subject in memory["subjects"].items() if subject.get("name") and held.get(sid, set()) & MAIN]
    for rid in [DEAL, *wanted]:
        if rid not in has_page:
            subject = memory["subjects"].get(rid, {"kind": "", "name": memory["deal"]["name"]})  # the opportunity is no subject
            shelf = "parties" if subject["kind"] in ("party", "group", "person") else "assets"
            slug = re.sub(r"[^a-z0-9]+", "-", subject["name"].lower()).strip("-") or rid.lower()
            path = f"{files.WIKI}/" + (START if rid == DEAL else f"{shelf}/{slug}.md")
            if path in pages:  # another subject has the same name
                path = f"{files.WIKI}/{shelf}/{slug}-{rid.lower()}.md"
            pages[path], where[rid] = SKELETON.format(title=subject["name"], about=rid), path[cut:]
            created.append(path)
    for path, ids in sorted(named, key=lambda page: page[0].split("/")[0] in BRIEF):  # what has no page of its own
        for rid in ids:  # is found on the first page that names it: a page about subjects before one about a topic
            where.setdefault(rid, path)
    marks = " ".join(str(check.get("matters", "")) for check in std["checks"].values())  # the reason of a mark names facts too
    heavy = set(ID.findall(marks)) | {fid for row in rows if row.get("against") or std["checks"][row["check"]].get("matters")
                                      for fid in row.get("facts", [])}

    def weight(page):
        """Where a page stands on its shelf. First the page of a party or a project with a main role. Then the pages that
        cite the most of what matters: the facts behind a marked check or behind an answer that goes against a claim.
        Then the pages that cite the most of the record, then by name."""
        cited, own = set(ID.findall(own_text(page[1]))), page[0][cut:].split("/")[0] not in BRIEF
        main = own and any(rid == DEAL or held.get(rid, set()) & MAIN for rid in about(page[1]))
        return not main, -len(heavy & cited), -len(cited), page[0]

    contents, ordered = {shelf: [] for shelf in SHELVES}, sorted(pages.items(), key=weight)
    for path, text in ordered:
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
             f"[Documents](../../{encoded(files.CLIENT)}/index.md) lists what the client shared."
             + " [Timeline](timeline.md) lists what was recorded, when and by whom." * own_timeline(deal), ""]
    for shelf, lines in contents.items():
        if lines:
            index += [f"## {SHELVES.get(shelf, shelf.capitalize())}", "", *lines, ""]
    others = [f"- {sid} {subject.get('name') or 'not yet named'}: {described(sid, memory, std, held)}"
              + (f". {subject['note']}" if subject.get("note") else "")
              for sid, subject in live(memory).items() if sid not in where]
    if others:
        index += ["## Subjects without a page", "", *others, ""]
    index += ["## Checks", "", "- [The due diligence list](checks.md): every check of the standard for this opportunity, with what "
              "is answered, what is open and what it waits for.", ""]
    listed = files.read_json(deal, files.MANIFEST, {"documents": []})["documents"]
    todo = next_list(memory, std, rows, in_folder={doc["slot"] for doc in listed})
    sources, checks, log = "\n".join(source_lines(memory)), check_page(memory, std, rows, todo, where), {}
    if own_timeline(deal):  # never over a page of the analyst's of that name
        log = {"timeline.md": timeline(memory)}
        files.write(deal, f"{files.WIKI}/timeline.md", log["timeline.md"])
    files.write(deal, f"{files.WIKI}/index.md", "\n".join(index))
    files.write(deal, f"{files.WIKI}/sources.md", sources)
    files.write(deal, f"{files.WIKI}/checks.md", checks)
    client = f"../../{files.CLIENT}/index.md"  # the index of the client folder, as a path from the wiki folder
    texts = {"index.md": "\n".join(index), "sources.md": sources, **{path[cut:]: pages[path] for path, _ in ordered},
             client: documents(memory["deal"]["name"], listed, std), **log, "checks.md": checks}
    notes = [row.get("missing", "") for row in rows]  # a note on what is missing cites what it names
    cited = set(ID.findall(" ".join([*(text for path, text in texts.items() if path not in ("sources.md", "checks.md")), *notes])))
    past = {"facts": "outdated", "sources": "replaced", "links": "ended"}  # history goes in only where a page cites it
    kept = {table: {rid: record for rid, record in memory[table].items()
                    if rid in cited or record.get("state", "current") != past.get(table)} for table in TABLES}
    data = {"name": memory["deal"]["name"], "revision": memory["log"][-1]["n"], "shelves": SHELVES, "pages": texts,
            "documents": client, "where": where, **kept}
    filled = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")  # so that no text can end the script it sits in
    files.write(deal, f"{files.WIKI}/wiki.html", files.packaged("wiki.html").replace("{{DATA}}", filled))
    files.write(deal, "Wiki.html", DOOR)
    return created, changed, len(pages) - len(created) - len(changed)


def numbers(text):
    """The numbers in a text, leaving out those inside the ID of a record or a check, and inside a link's target. Each
    as written, then with its scale word applied, and the step it is written to: "2.5bn" is (2.5, 2.5e9, 1e8)."""
    found = set()
    for token, word in NUMBER.findall(re.sub(r"\]\([^)]*\)|\b[A-Z]+_\w+", " ", ID.sub("", text))):
        token, scale = token.replace(",", "").rstrip("."), SCALE.get(word.strip().lower(), 1)
        try:
            found.add((float(token), float(token) * scale, 10 ** -len(token.partition(".")[2]) * scale))
        except ValueError:
            pass
    return found


def supported(figure, held):
    """Whether the numbers that records hold bear out a figure: the same number, or one that rounds to it at the step it
    is written to, with a scale word on either side: 4,060m is 4.1bn, not 4.0bn. The same digits pass unless both sides
    carry a scale word and the two differ: 50bn is not 50 million."""
    n, value, step = figure
    bare = any(n == m and (value == n or scaled == m) for m, scaled, _ in held)  # the same digits, one side with no scale word
    rounds = any(-step * 0.500001 <= scaled - value < step * 0.499999 for _, scaled, _ in held)  # a half rounds up
    return bare or rounds  # the 0.000001 keeps an error of floating point, as in 4.06 * 1e9, from moving a figure over the edge


def where_held(loose, holders):
    """For numbers that no record cited beside them holds: up to three facts that hold each, or else a fact that holds
    the number with decimals."""
    hints = []
    for n in loose:
        ids, first = holders.get(n, [])[:3], f"{n:g}" if len(loose) > 1 else "It"
        near = [(m, fids[0]) for m, fids in holders.items() if n == int(n) == int(m)]
        if ids:
            hints.append(f"{first} is in " + " and ".join([", ".join(ids[:-1]), ids[-1]] if len(ids) > 1 else ids))
        elif near:
            hints.append(f"{near[0][1]} holds {near[0][0]:,}")
    return "".join(f". {hint}" for hint in hints)


def problems(deal, memory):
    """What looks wrong on the pages and in the drafts: citations and links that lead nowhere, citations of a record that
    was replaced and is not marked so, numbers that no record cited in the same paragraph holds, and a page that no
    other page links to."""
    found, pages, reached = [], all_pages(deal), set()
    there = set(files.listing(deal, files.WIKI) + files.listing(deal, files.OUTPUTS))
    holders = {}  # each number, and the facts that hold it
    for fid, fact in memory["facts"].items():
        if fact["state"] != "outdated":
            said = " ".join(str(fact.get(key, "")) for key in ("statement", "value", "unit", "as_of", "place", "quote"))
            for n in {n for n, _, _ in numbers(said)}:
                holders.setdefault(n, []).append(fid)
    for path, text in sorted({**pages, **drafts(deal)}.items()):
        body = own_text(text)
        notes = path == f"{files.WIKI}/work/working-notes.md"  # they say how to work, and need not cite the record
        cited = list(dict.fromkeys(ID.findall(body)))
        found += [f"{path}: cites {rid}, which does not exist" for rid in cited if not table_of(memory, rid)]
        if len(ID.sub("", body).split()) > 40 and not notes and not any(table_of(memory, rid) for rid in cited):
            found.append(f"{path}: has text and cites nothing")
        for link in re.findall(r"\]\((?![a-z]+:)([^)#\s]+\.md)", text):  # a link to another page, also in the tool's parts
            target = files.beside(path, decoded(link))
            if path in pages and target != path:
                reached.add(target)
            if target.startswith((files.WIKI + "/", files.OUTPUTS + "/")) and target not in there:
                found.append(f"{path}: links to {link}, which is not there")
        for words in [] if notes else memory["deal"].get("avoid", []):  # a wording to keep out: all its words in one sentence
            found += [f"{path}: \"{' '.join(sentence.split()[:6])} ...\" holds a wording to avoid: {words}"
                      for block in [front(text).get("title", ""), *re.findall(r"^#+\s*(.+)$", text, re.M), *blocks(body)]
                      for sentence in re.split(r"(?<=[.!?])\s+", block)
                      if all(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", sentence, re.I) for word in words.split())]
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
                                 if key not in ("fingerprint", "rev", "value", "answers") and (key != "map" or "map" in entry))
                unit = str(entry.get("unit", "")).split()[-1:]  # the scale word of a unit such as KES m goes with the value
                held += f" {entry.get('value', '')}{''.join(unit)}"
            held = numbers(held)  # a figure passes where a record cited beside it holds it, also rounded or with a scale word
            loose = sorted({n for n, value, step in numbers(block) if (value >= 10 or n != int(n)) and not supported((n, value, step), held)})
            if loose and not notes:  # where a cited record holds the same digits, it gives them another scale word
                digits = {m for m, _, _ in held}
                figures = [f"{n:g} with another scale word" if n in digits else f"{n:g}" for n in loose[:8]]
                found.append(f"{path}: \"{' '.join(block.split()[:6])} ...\" has {', '.join(figures)}, "
                             "which no record cited in that paragraph holds" + where_held(loose[:8], holders))
        found += [f"{path}: cites {rid}, which is {entry['state']}" + (f" (replaced by {entry['replaced_by']})" if entry.get(
            "replaced_by") else "") + f". Cite what took its place, or start the sentence with \"{entry['state'].capitalize()}:\""
            for rid, entry in stale.items()]
    return found + [f"{path}: no other page links to it" for path in sorted(pages)  # the page of the deal is the way in
                    if path not in reached and path != f"{files.WIKI}/{START}" and not path.startswith(f"{files.WIKI}/work/")]
