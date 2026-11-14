"""The memory of a deal: sources, facts, subjects, links, decisions and questions, with a log.

Nothing is deleted. A record that is replaced stays, marked as replaced.
"""
import datetime
import hashlib
import json

from .files import Refused

# For each table: the ID prefix, the fields a new record must have, and the other fields it may have.
TABLES = {
    "sources": ("S", ("title", "kind"),
                ("where", "fingerprint", "date", "about", "read", "map", "sent_by", "state", "replaced_by", "note")),
    "facts": ("F", ("about", "statement", "source"),
              ("label", "value", "unit", "as_of", "place", "said_by", "nothing_found", "answers", "fills",
               "state", "replaced_by", "note")),
    "subjects": (None, ("kind",), ("name", "note")),  # the prefix comes from the kind of subject
    "links": ("R", ("from", "type", "to"), ("state", "why", "source", "note")),
    "decisions": ("D", ("decision", "reason"), ("about", "rests_on", "by")),
    "questions": ("Q", ("asked_of", "text"), ("about", "checks", "asked", "via", "state", "answered_by")),
}
# Fields that hold IDs, and the tables those IDs may come from.
REFERS = {"source": ("sources",), "via": ("sources",), "about": ("subjects", "links"), "from": ("subjects",),
          "to": ("subjects",), "rests_on": ("facts",), "answered_by": ("facts", "sources")}
STATES = {"sources": ("current", "replaced"), "facts": ("current", "outdated", "disputed"),
          "links": ("proposed", "confirmed", "ended"), "questions": ("open", "answered", "withdrawn")}
SAID_BY = ("document", "client", "officer", "third_party", "inference")
DEAL = "DEAL"  # stands for the deal as a whole wherever a subject is expected


def new(name, stage, standard_version):
    memory = {"format": 1, "deal": {"name": name, "stage": stage, "standard": standard_version}}
    memory.update({table: {} for table in TABLES})
    memory["log"] = []
    record(memory, "tool", "Deal folder created")
    return memory


def revision(memory):
    return memory["log"][-1]["n"]


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def state_of(memory):
    return digest({key: memory[key] for key in ("deal", *TABLES)})


def record(memory, by, note, op=None, added=(), changed=None):
    """Add a log entry. It carries the fingerprint of the entry before it and of the memory after the change."""
    log = memory["log"]
    entry = {"n": len(log) + 1, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
             "by": by, "note": note, "op": op, "added": list(added), "changed": changed or {},
             "state": state_of(memory), "prev": log[-1]["hash"] if log else None}
    entry["hash"] = digest(entry)
    log.append(entry)
    return entry


def verify(memory):
    """Problems with the log: a broken chain, or a memory that was changed without a log entry."""
    problems, prev = [], None
    for entry in memory["log"]:
        body = {key: value for key, value in entry.items() if key != "hash"}
        if entry["prev"] != prev or entry["hash"] != digest(body):
            problems.append(f"the log is broken at entry {entry['n']}")
            break
        prev = entry["hash"]
    if memory["log"] and memory["log"][-1]["state"] != state_of(memory):
        problems.append("the memory was changed outside the tool since the last log entry")
    return problems


def table_of(memory, rid):
    """The table an ID belongs to, or None."""
    return next((table for table in TABLES if rid in memory[table]), None)


def next_id(prefix, taken):
    numbers = [int(i[len(prefix) + 1:]) for i in taken if i.startswith(prefix + "-")]
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def as_list(value):
    return value if isinstance(value, list) else [] if value is None else [value]


EXPECTS = {"yes_no": "true or false", "number": "a number", "choice": "one of the check's options", "text": "text"}


def fits(check, value):
    """Whether a value is the kind of answer the check asks for."""
    if check["answer"] == "yes_no":
        return isinstance(value, bool)
    if check["answer"] == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if check["answer"] == "choice":
        return bool(as_list(value)) and all(option in check["options"] for option in as_list(value))
    return isinstance(value, str)


def place(memory, change, std, errors):
    """Give every new record its ID, and replace each "@name" with the ID it stands for."""
    prefixes = {kind["id"]: kind["prefix"] for kind in std["subject_kinds"]}
    names, placed = {}, []
    taken = {rid for table in TABLES for rid in memory[table]}
    for table in TABLES:
        for item in change.get(table, []):
            if not isinstance(item, dict):
                errors.append(f"{table}: each entry must be an object")
                continue
            fields = {key: value for key, value in item.items() if key not in ("id", "ref")}
            rid = item.get("id")
            if rid is None:
                prefix = TABLES[table][0] or prefixes.get(item.get("kind"))
                if prefix is None:
                    errors.append(f"subjects: unknown kind {item.get('kind')!r}. Known: {', '.join(prefixes)}")
                    continue
                rid = next_id(prefix, taken)
                taken.add(rid)
                if item.get("ref"):
                    names["@" + item["ref"]] = rid
            placed.append([table, rid, fields, "id" not in item])

    def swap(value):
        if isinstance(value, list):
            return [swap(v) for v in value]
        if isinstance(value, str) and value.startswith("@"):
            if value not in names:
                errors.append(f"{value} names nothing in this set of changes")
            return names.get(value, value)
        return value

    for _, _, fields, _ in placed:
        for key in (*REFERS, "replaces"):
            if key in fields:
                fields[key] = swap(fields[key])
        for answer in as_list(fields.get("answers")):
            if isinstance(answer, dict) and "for" in answer:
                answer["for"] = swap(answer["for"])
    return placed


def problems_of(table, rid, fields, is_new, memory, known, std):
    """What makes one record malformed. `known` maps every ID, old and new, to its table."""
    _, need, other = TABLES[table]
    found = [f"unknown field {key!r}" for key in fields if key not in (*need, *other, "replaces")]
    if is_new:
        found += [f"{key!r} is missing" for key in need if fields.get(key) in (None, "", [])]
    elif rid not in memory[table]:
        found.append("no such record")
    for key, tables in REFERS.items():
        for value in as_list(fields.get(key)):
            if not (known.get(value) in tables or (key == "about" and value == DEAL)):
                found.append(f"{key} {value!r} is not a known ID of the right kind")
    if "replaces" in fields and (table not in ("sources", "facts") or known.get(fields["replaces"]) != table):
        found.append(f"replaces {fields['replaces']!r}: no such record in {table}")
    for key, allowed in (("kind", std["kinds_by_table"].get(table)), ("type", std["link_ids"] if table == "links" else None),
                         ("state", STATES.get(table)), ("said_by", SAID_BY)):
        if allowed and fields.get(key) is not None and fields[key] not in allowed:
            found.append(f"{key} {fields[key]!r} is not known. Known: {', '.join(sorted(allowed))}")
    for answer in as_list(fields.get("answers")):
        if not isinstance(answer, dict) or answer.get("check") not in std["checks"] or "value" not in answer:
            found.append(f"answer {answer!r} needs a known check and a value")
        elif "for" in answer and answer["for"] != DEAL and known.get(answer["for"]) not in ("subjects", "links"):
            found.append(f"answer for {answer['for']!r}: not a known subject or link")
        elif not fits(std["checks"][answer["check"]], answer["value"]):
            found.append(f"the answer to {answer['check']} must be {EXPECTS[std['checks'][answer['check']]['answer']]}")
    return [f"{table} {rid}: {problem}" for problem in found]


def apply(memory, change, std):
    """Check a set of changes and apply all of it, or refuse all of it. Returns the log entry."""
    errors = [f"unknown key {key!r}" for key in change if key not in ("by", "note", "base", "op", "deal", *TABLES)]
    if change.get("op") and any(entry["op"] == change["op"] for entry in memory["log"]):
        return None  # this set of changes was applied before
    if "base" in change and change["base"] != revision(memory):
        errors.append(f"the memory is at revision {revision(memory)}, not {change['base']}. Look at it again and resend.")
    deal = change.get("deal", {})
    errors += [f"deal: unknown field {key!r}" for key in deal if key not in ("name", "stage")]
    if "stage" in deal and deal["stage"] not in std["stage_ids"]:
        errors.append(f"deal: unknown stage {deal['stage']!r}. Known: {', '.join(std['stage_ids'])}")
    placed = place(memory, change, std, errors)
    known = {rid: table for table in TABLES for rid in memory[table]}
    known.update({rid: table for table, rid, _, _ in placed})
    for table, rid, fields, is_new in placed:
        errors += problems_of(table, rid, fields, is_new, memory, known, std)
    if errors:
        raise Refused("Nothing was recorded.\n" + "\n".join(errors))

    number = revision(memory) + 1
    added, changed = [], {}
    before = {key: memory["deal"].get(key) for key in deal if memory["deal"].get(key) != deal[key]}
    if before:
        changed[DEAL] = before
        memory["deal"].update(deal)
    for table, rid, fields, is_new in placed:
        replaces = fields.pop("replaces", None)
        if is_new:
            start = {"state": STATES[table][0]} if table in STATES else {}
            memory[table][rid] = {**start, **fields, "rev": number}
            added.append(rid)
        else:
            old = memory[table][rid]
            before = {key: old.get(key) for key in fields if old.get(key) != fields[key]}
            old.update(fields)
            if before:
                changed[rid] = before
        if replaces:
            old = memory[table][replaces]
            changed[replaces] = {"state": old.get("state"), "replaced_by": old.get("replaced_by")}
            old.update(state=STATES[table][1], replaced_by=rid)
    return record(memory, change.get("by", "unknown"), change.get("note", ""), change.get("op"), added, changed)
