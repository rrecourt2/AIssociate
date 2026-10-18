#!/usr/bin/env python3
"""The AIssociate deal register: one JSON file of record plus a generated Markdown view.

  register.py init FOLDER --deal KEY
  register.py summary FOLDER
  register.py show FOLDER [ID ...]
  register.py show FOLDER --section SECTION
  register.py apply FOLDER CHANGES.json
  register.py lists FOLDER
  register.py ddq FOLDER
  register.py migrate FOLDER
  register.py refresh FOLDER
  register.py check FOLDER

FOLDER is a local copy of the AIssociate case folder. register.json is the record.
Analysis.md is rewritten from it after every change; it is a read-only view.
Standard library only.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

TABLES = {  # name: (id prefix, columns)
    "sources": ("S", ["id", "title", "link", "type", "entity", "period", "event_date", "tier",
                      "coverage", "impact", "notes", "version", "sha256", "extract_path", "reviewed_scope", "supersedes"]),
    "risks": ("R", ["id", "title", "topic", "raised_by", "rating", "residual", "destination",
                    "reason", "status", "officer_decision"]),
    "mitigants": ("M", ["id", "risk", "text", "type", "verified", "source", "raised_by", "status"]),
    "open_items": ("O", ["id", "kind", "text", "link", "addressee", "raised_by", "owner",
                         "criticality", "status", "answer", "answer_source", "due", "officer_ok",
                         "audience", "purpose", "assessment", "assessed_by", "officer_decision"]),
    "findings": ("", ["id", "by", "version", "section", "issue", "priority", "status", "resolution"]),
    "analysis": ("", ["id", "title", "text", "sources", "updated", "claims", "recheck"]),
    "fp_map": ("", ["id", "version", "section", "owner", "ids", "recheck"]),
    "claims": ("C", ["id", "assertion", "kind", "entity", "period", "sources", "support",
                     "qualifications", "sections", "value", "unit", "definition", "inputs", "method",
                     "attributed_to", "adoption", "recheck"]),
}
CONTROL = ["deal", "officer", "decision_sought", "recommendation", "audience", "annexes", "deadline",
           "template", "word", "status", "ready_for", "ready_by", "updated"]  # word: current document link and version
ALLOWED = {
    ("sources", "tier"): {"A", "B", "C"},
    ("sources", "coverage"): {"unread", "partial", "read", "unreadable"},
    ("sources", "impact"): {"pending", "assessed", "no-impact"},
    ("risks", "rating"): {"high", "medium", "low"},
    ("risks", "residual"): {"high", "medium", "low", "unclear"},
    ("risks", "destination"): {"main", "annex", "background", "unresolved"},
    ("risks", "status"): {"open", "assessed", "recheck", "closed"},
    ("mitigants", "type"): {"existing", "proposed-condition", "assumption"},
    ("mitigants", "verified"): {"yes", "no"},
    ("open_items", "kind"): {"question", "action", "credit-question", "prior-issue"},
    ("open_items", "criticality"): {"blocker", "material", "later"},
    ("open_items", "status"): {"open", "promised", "answered", "recheck", "closed"},  # only closed is finished
    ("open_items", "officer_ok"): {"yes", "no"},
    ("open_items", "audience"): {"unknown", "client", "internal", "restricted"},
    ("claims", "recheck"): {"yes", "no", "unknown"},
    ("analysis", "recheck"): {"yes", "no", "unknown"},
    ("fp_map", "recheck"): {"yes", "no", "unknown"},
    ("findings", "by"): {"grill", "style"},
    ("findings", "priority"): {"blocker", "material", "minor"},
    ("findings", "status"): {"open", "resolved", "officer-judgment"},
    ("control", "status"): {"draft", "ready", "submitted"},
}
ID_RE = re.compile(r"\b[SRMOGTC]-\d+\b")
SOURCE_RE = re.compile(r"\bS-\d+\b")
DEFAULTS = {"open_items": {"status": "open", "audience": "unknown"},
            "sources": {"impact": "pending", "coverage": "unread"},
            "risks": {"status": "open"}, "findings": {"status": "open"},
            "claims": {"support": "unknown", "adoption": "unknown", "recheck": "no"},
            "analysis": {"recheck": "no"}, "fp_map": {"recheck": "no"}}


class ChangeError(Exception):
    """A change set was rejected; the register is unchanged."""


class ViewsIncompleteError(OSError):
    """The JSON record is saved, but its generated views need a retry."""


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- storage ----------

def new_register(deal):
    reg = {"schema_version": 1, "revision": 0, "control": {k: "" for k in CONTROL}, "log": []}
    reg["control"].update(deal=deal, status="draft", updated=now())
    reg.update({name: [] for name in TABLES})
    return reg


def load(folder):
    path = Path(folder) / "register.json"
    if not path.exists():
        raise ChangeError(f"no register.json in {folder}; run init first")
    reg = json.loads(path.read_text(encoding="utf-8"))
    if reg.get("schema_version") != 1:
        raise ChangeError("unsupported register schema; run register.py migrate FOLDER explicitly")
    return reg


def migrate(folder):
    """Upgrade once, retaining the exact legacy bytes and all IDs/history."""
    path = Path(folder) / "register.json"
    raw = path.read_bytes()
    reg = json.loads(raw)
    if reg.get("schema_version") == 1:
        refresh_views(folder, reg)
        return {"status": "already-migrated", "revision": reg["revision"]}
    if reg.get("schema_version", 0) != 0:
        raise ChangeError("cannot migrate an unknown schema version")
    backup = path.with_name("register.schema-0.backup.json")
    if backup.exists() and backup.read_bytes() != raw:
        raise ChangeError(f"refusing to replace a different migration backup: {backup}")
    if not backup.exists():
        with backup.open("xb") as f:
            f.write(raw)
    for name, (_, cols) in TABLES.items():
        for row in reg.setdefault(name, []):
            for col in cols:
                row.setdefault(col, "unknown" if col in {"audience", "recheck"} else "")
    reg["schema_version"] = 1
    if reg["control"]["status"] == "ready" and open_checks(reg):
        reg["control"]["status"] = "draft"  # Keep the historical decision fields and log intact.
    save(folder, reg)
    return {"status": "migrated", "revision": reg["revision"], "backup": str(backup)}


def refresh(folder):
    reg = load(folder)
    refresh_views(folder, reg)
    return {"status": "refreshed", "revision": reg["revision"]}


def save(folder, reg):
    """Write register.json atomically, then regenerate the views."""
    folder = Path(folder)
    data = json.dumps(reg, indent=1, ensure_ascii=False)
    json.loads(data)
    atomic_text(folder / "register.json", data)
    refresh_views(folder, reg)


def atomic_text(path, text):
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def refresh_views(folder, reg):
    try:
        write_views(folder, reg)
    except OSError as e:
        raise ViewsIncompleteError(f"register revision {reg['revision']} saved; views incomplete: {e}. "
                                   "Retry the same change set to regenerate the views.") from e


def write_views(folder, reg):
    atomic_text(Path(folder) / "Analysis.md", analysis_md(reg))


def linked(reg, text):
    """Turn source IDs into links to the original documents."""
    links = {s["id"]: s["link"] for s in reg["sources"] if s["link"]}
    return SOURCE_RE.sub(lambda m: f"[{m[0]}](<{links[m[0]]}>)" if m[0] in links else m[0], text)


def analysis_md(reg):
    first = ["strategy", "timeline", "key-figures"]
    rows = sorted(reg["analysis"], key=lambda r: (first.index(r["id"]) if r["id"] in first else len(first), r["id"]))
    out = [f"# {reg['control']['deal']} — analysis", "",
           f"_Generated from register revision {reg['revision']}. Do not edit this file; changes go through the register._", ""]
    for r in rows:
        out += [f"## {r['title'] or r['id']} ({r['id']})", "", r["text"].strip(), ""]
        out += [f"{label}: {linked(reg, r[key])}" for key, label in (("sources", "Sources"), ("claims", "Claims"),
                ("updated", "Updated"), ("recheck", "Recheck")) if r.get(key) not in ("", None, "no")]
        out.append("")
    if reg["claims"]:
        out += ["## Evidence index", ""]
        for c in reg["claims"]:
            context = "; ".join(v for v in (c["kind"], c["entity"], c["period"], c["attributed_to"]) if v)
            evidence = "; ".join(v for v in (c["sources"], c["inputs"]) if v) or "no located evidence"
            status = (c["support"] or "unknown") + ("; recheck" if c["recheck"] != "no" else "")
            out.append(f"- {c['id']} ({context}): {c['assertion']} — {linked(reg, evidence)} [{status}]")
        out.append("")
    rank = {"blocker": 0, "material": 1}
    opened = sorted((o for o in reg["open_items"] if o["status"] != "closed"),
                    key=lambda o: (rank.get(o["criticality"], 2), o["due"] or "9999"))
    if opened:
        out += ["## Open items", ""]
        for row in opened:
            out.append(f"- {row['id']} [{row['status']}; {row['criticality'] or 'unrated'}]: {row['text']}"
                       + (f" — {row['purpose']}" if row["purpose"] else ""))
        out.append("")
    if reg["sources"]:
        out += ["## Sources", ""] + original_sources(reg, {s["id"] for s in reg["sources"]}) + [""]
    return "\n".join(out)


# ---------- changes ----------

def next_id(rows, prefix):
    nums = [int(r["id"].split("-")[1]) for r in rows if re.fullmatch(rf"{prefix}-\d+", r["id"])]
    return f"{prefix}-{max(nums, default=0) + 1:03d}"


def apply_change(reg, ch):
    if not isinstance(ch, dict):
        raise ChangeError("each change must be an object")
    sheet = ch.get("sheet")
    fields = ch.get("add", ch.get("set", {}))
    if not isinstance(fields, dict) or any(not isinstance(v, str) for v in fields.values()):
        raise ChangeError("add/set fields must be an object of strings; omit unavailable fields")
    if sheet == "control":
        for k, v in fields.items():
            if k not in CONTROL:
                raise ChangeError(f"control has no field {k!r}")
            if k == "ready_for":
                raise ChangeError("ready_for is assigned when recording readiness")
            if k == "status" and not str(v).strip():
                raise ChangeError("control status cannot be blank")
            reg["control"][k] = str(v)
        return None
    if sheet not in TABLES:
        raise ChangeError(f"unknown sheet {sheet!r}; use one of {['control'] + list(TABLES)}")
    prefix, cols = TABLES[sheet]
    rows = reg[sheet]
    unknown = set(fields) - set(cols)
    if unknown:
        raise ChangeError(f"{sheet} has no field(s) {sorted(unknown)}")
    if "add" in ch:
        row = {c: "" for c in cols}
        row.update(DEFAULTS.get(sheet, {}))
        row.update({k: str(v) for k, v in fields.items() if str(v) != ""})
        if sheet == "findings":
            row["id"] = next_id(rows, "T" if row["by"] == "style" else "G")
        elif sheet == "fp_map":
            row["id"] = f"{row['version']}/{row['section']}"
        elif sheet == "analysis":
            if not row["id"]:
                raise ChangeError("analysis rows need an id such as timeline, key-figures, strategy or R-001")
        elif row["id"]:
            raise ChangeError("ids are assigned by the register; leave id empty when adding")
        else:
            row["id"] = next_id(rows, prefix)
        if sheet == "analysis":
            row["updated"] = now()
        rows[:] = [r for r in rows if r["id"] != row["id"]] + [row]
        return row["id"]
    if "update" in ch:
        target = ch["update"]
        for r in rows:
            if r["id"] == target:
                if sheet == "sources" and any(k in fields and r[k] and fields[k] != r[k]
                                              for k in ("sha256", "version", "supersedes")):
                    raise ChangeError(f"{target}: changed source content/version needs a new source ID")
                for k, v in fields.items():
                    if (sheet, k) in ALLOWED and r.get(k) and not str(v).strip():
                        raise ChangeError(f"{target}: {k} cannot be blank; choose an explicit state")
                r.update({k: str(v) for k, v in fields.items() if k != "id"})
                if sheet == "analysis":
                    r["updated"] = now()
                return target
        if sheet == "analysis":
            row = {c: "" for c in cols}
            row.update(DEFAULTS.get(sheet, {}))
            row.update({k: str(v) for k, v in fields.items()}, id=target)
            row["updated"] = now()
            rows.append(row)
            return target
        raise ChangeError(f"{target} not found in {sheet}")
    raise ChangeError("each change needs 'add', 'update' (with 'set') or, for control, 'set'")


def request_sha256(changes):
    try:
        raw = json.dumps(changes, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as e:
        raise ChangeError(f"request must contain JSON values: {e}") from e
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def invalidate_links(reg, old):
    """Follow only explicit register links; whole-case source impact remains separate."""
    old_sources = {r["id"]: r for r in old["sources"]}
    # A new version needs a new source ID; a corrected title, link or note changes no evidence.
    changed_sources = {r["id"] for r in reg["sources"] if r["id"] in old_sources
                       and any(r[k] != old_sources[r["id"]][k] for k in ("entity", "period", "event_date"))}
    changed_sources.update(r["supersedes"] for r in reg["sources"] if r["supersedes"]
                           and r["supersedes"] != old_sources.get(r["id"], {}).get("supersedes"))
    old_claims = {r["id"]: r for r in old["claims"]}
    changed_claims = {r["id"] for r in reg["claims"] if r["id"] in old_claims
                     and any(r[k] != old_claims[r["id"]][k] for k in r if k != "recheck")}
    for row in reg["claims"]:
        if changed_sources.intersection(SOURCE_RE.findall(row["sources"] + " " + row["inputs"])):
            row["recheck"] = "yes"
            changed_claims.add(row["id"])
    for _ in reg["claims"]:  # At most one pass per claim, including forward references and cycles.
        affected = {r["id"] for r in reg["claims"] if changed_claims.intersection(ID_RE.findall(r["inputs"]))}
        if affected <= changed_claims:
            break
        changed_claims.update(affected)
        for row in reg["claims"]:
            if row["id"] in affected:
                row["recheck"] = "yes"
    reopened = []
    old_answers = {r["id"]: r for r in old["open_items"]}
    for row in reg["open_items"]:
        prior = old_answers.get(row["id"])
        # An assessment written in this change set already reflects the changed evidence.
        if (prior and {prior["status"], row["status"]} <= {"closed", "answered"}
                and row["assessment"] == prior["assessment"]
                and (changed_sources | changed_claims).intersection(ID_RE.findall(row["answer_source"]))):
            reopened.append(copy.deepcopy(prior))
            row.update(status="recheck", assessment="", assessed_by="", officer_decision="")
    old_analysis = {r["id"]: r for r in old["analysis"]}
    changed_analysis = {r["id"] for r in reg["analysis"] if r["id"] in old_analysis
                        and any(r[k] != old_analysis[r["id"]][k] for k in r if k not in {"updated", "recheck"})}
    for row in reg["analysis"]:
        if (changed_sources.intersection(SOURCE_RE.findall(row["sources"]))
                or changed_claims.intersection(ID_RE.findall(row["claims"]))):
            row.update(recheck="yes", updated=now())
            changed_analysis.add(row["id"])
    sections = {s.strip() for row in reg["claims"] if row["id"] in changed_claims
                for s in re.split(r"[,;\n]", row["sections"]) if s.strip()}
    affected = changed_sources | changed_claims | changed_analysis
    for row in reg["fp_map"]:
        if affected.intersection(link_ids(row["ids"])) or row["section"] in sections:
            row["recheck"] = "yes"
    return reopened


def apply(folder, changes):
    if not isinstance(changes, dict) or not isinstance(changes.get("changes", []), list):
        raise ChangeError("a change set must be an object with a changes list")
    reg = load(folder)
    if not isinstance(changes.get("op_id"), str) or not changes["op_id"].strip():
        raise ChangeError("op_id is required so that a retry cannot apply the same change twice")
    digest = request_sha256(changes)
    for entry in reg["log"]:
        if entry.get("op_id") == changes["op_id"]:
            if not entry.get("request_sha256"):
                raise ChangeError("legacy operation has no digest; use refresh to repair views without replay")
            if entry["request_sha256"] != digest:
                raise ChangeError("op_id already used with a different payload; use a new operation ID")
            refresh_views(folder, reg)
            return {"status": "already-applied", "revision": reg["revision"]}
    if changes.get("base_revision") != reg["revision"]:
        raise ChangeError(f"stale: change set is based on revision {changes.get('base_revision')}, "
                          f"the register is at {reg['revision']}; re-read with summary and retry")
    before = {(p[1], p[2]) for p in problems(reg) if p[0] == "error"}
    new = copy.deepcopy(reg)
    touched = [apply_change(new, ch) for ch in changes.get("changes", [])]
    reopened = invalidate_links(new, reg)
    introduced = [p for p in problems(new) if p[0] == "error" and (p[1], p[2]) not in before]
    rank = {"low": 0, "medium": 1, "high": 2}
    old = {r["id"]: r for r in reg["risks"]}
    for r in new["risks"]:
        o = old.get(r["id"])
        if (o and rank.get(r["rating"], -1) < rank.get(o["rating"], -1)
                and (not r["officer_decision"].strip()
                     or r["officer_decision"] == o["officer_decision"])):
            introduced.append(("error", "officer-decision", r["id"],
                               f"downgrading {o['rating']} to {r['rating'] or 'unrated'} needs the Investment Officer's "
                               "decision in officer_decision"))
    if introduced:
        raise ChangeError("rejected, nothing saved:\n" + "\n".join(f"  {p[2]}: {p[3]}" for p in introduced))
    notes = []
    c = new["control"]
    control_changes = {k: v for ch in changes.get("changes", []) if ch.get("sheet") == "control"
                       for k, v in ch.get("set", {}).items()}
    requested_ready = control_changes.get("status") == "ready"
    if requested_ready:
        reasons = open_checks(new)
        if not str(control_changes.get("ready_by", "")).strip():
            reasons.append("explicit Investment Officer attribution in ready_by is required")
        if not c["word"].strip():
            reasons.append("the current document link and version are required in word")
        if reasons:
            raise ChangeError("cannot record ready, nothing saved: " + "; ".join(reasons))
        c["ready_for"] = f"{c['word']} at register revision {new['revision'] + 1}"
    elif reg["control"]["status"] == "ready":
        reasons = open_checks(new)
        if any(new[name] != reg[name] for name in TABLES):
            reasons.append("evidence or analysis changed since readiness was recorded")
        if any(c[k] != reg["control"][k] for k in CONTROL if k != "updated"):
            reasons.append("the document or control details changed since readiness was recorded")
        if reasons:
            if c["status"] == "ready":
                c["status"] = "draft"
            c.update(ready_for="", ready_by="")
            notes.append("readiness withdrawn: " + "; ".join(reasons))
    new["revision"] += 1
    new["control"]["updated"] = now()
    new["log"].append({"at": now(), "revision": new["revision"], "actor": changes.get("actor", ""),
                       "op_id": changes["op_id"], "summary": changes.get("summary", ""),
                       "next_step": changes.get("next_step", ""), "request_sha256": digest})
    if reopened:
        new["log"][-1]["reopened_answers"] = reopened
    save(folder, new)
    return {"status": "applied", "revision": new["revision"], "ids": [t for t in touched if t],
            "warnings": notes + [f"{p[2]}: {p[3]}" for p in problems(new) if p[0] == "warning"]}


# ---------- rules ----------

def gates(reg):
    """Reasons the current document cannot be called Ready, apart from rule errors and the Word check."""
    out = []
    blockers = [o["id"] for o in reg["open_items"] if o["criticality"] == "blocker" and o["status"] != "closed"]
    blockers += [f["id"] for f in reg["findings"] if f["priority"] == "blocker" and f["status"] != "resolved"]
    if blockers:
        out.append("open blockers: " + ", ".join(blockers))
    answers = [o["id"] for o in reg["open_items"] if o["status"] == "recheck"]
    if answers:
        out.append("answers to reassess: " + ", ".join(answers))
    pending = [s["id"] for s in reg["sources"] if s["impact"] == "pending"]
    if pending:
        out.append("source impact not assessed: " + ", ".join(pending))
    unread = [s["id"] for s in reg["sources"] if s["tier"] == "A" and s["coverage"] != "read"]
    if unread:
        out.append("critical sources not fully read: " + ", ".join(unread))
    recheck = [r["id"] for r in reg["risks"] if r["status"] == "recheck"]
    if recheck:
        out.append("risks to recheck: " + ", ".join(recheck))
    for name in ("claims", "analysis", "fp_map"):
        pending = [r["id"] for r in reg[name] if r.get("recheck") in {"yes", "unknown"}]
        if pending:
            out.append(f"{name} to recheck: " + ", ".join(pending))
    return out


def link_ids(text):
    return set(ID_RE.findall(text)) | {s.strip() for s in re.split(r"[,;\s]+", text) if s.strip()}


def source_errors(text, sources):
    matches = list(SOURCE_RE.finditer(text))
    if not matches:
        return ["needs an existing source ID and locator"]
    errors = []
    for i, match in enumerate(matches):
        if match.group() not in sources:
            errors.append(f"unknown source {match.group()}")
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if not re.search(r"\w", text[match.end():end]):
            errors.append(f"{match.group()} needs a locator")
    return errors


def evidence_ids(reg, row):
    """Resolve only cited claims and their inputs, never the whole case archive."""
    ids = set(ID_RE.findall(" ".join(row.get(k, "") for k in
              ("sources", "inputs", "claims", "answer_source", "source"))))
    for _ in reg["claims"]:
        linked = {i for claim in reg["claims"] if claim["id"] in ids
                  for i in ID_RE.findall(claim["sources"] + " " + claim["inputs"])}
        if linked <= ids:
            break
        ids.update(linked)
    return ids


def original_sources(reg, ids):
    lines = []
    newer = {s["supersedes"]: s["id"] for s in reg["sources"] if s["supersedes"]}
    for source in reg["sources"]:
        if source["id"] not in ids:
            continue
        title = source["title"].replace("[", "\\[").replace("]", "\\]") or source["id"]
        reference = f"[{title}](<{source['link']}>)" if source["link"] else title + " (original link unavailable)"
        details = [f"version {source['version'] or source['sha256'] or 'not recorded'}",
                   ", ".join(v for v in (source["entity"], source["period"]) if v),
                   f"coverage {source['coverage'] or 'unread'}",
                   f"superseded by {newer[source['id']]}" if source["id"] in newer else ""]
        lines.append(f"- {source['id']}: {reference} · " + " · ".join(d for d in details if d))
    for claim in reg["claims"]:
        evidence = "; ".join(claim[k] for k in ("sources", "inputs") if claim[k])
        if claim["id"] in ids and evidence:
            lines.append(f"- {claim['id']} evidence: {evidence}")
    return lines


def problems(reg, today=None):
    """(severity, rule, item, detail) tuples; errors block a change, warnings do not."""
    out = []
    err = lambda rule, item, detail: out.append(("error", rule, item, detail))  # noqa: E731
    warn = lambda rule, item, detail: out.append(("warning", rule, item, detail))  # noqa: E731
    for name in TABLES:
        seen = set()
        for r in reg[name]:
            if r["id"] in seen:
                err("unique-id", r["id"], f"duplicate id in {name}")
            seen.add(r["id"])
            for (table, column), allowed in ALLOWED.items():
                required = column in DEFAULTS.get(name, {})
                if table == name and (r.get(column) or required) and r.get(column) not in allowed:
                    err("allowed-value", r["id"], f"{column}={r[column]!r}; use one of {sorted(allowed)}")
    status = reg["control"].get("status")
    if status not in ALLOWED[("control", "status")]:
        err("allowed-value", "control", f"status={status!r}")
    risks = {r["id"]: r for r in reg["risks"]}
    sources = {s["id"]: s for s in reg["sources"]}
    claims = {c["id"]: c for c in reg["claims"]}
    superseded = {s["supersedes"] for s in reg["sources"] if s["supersedes"]}
    verified = {m["risk"] for m in reg["mitigants"] if m["verified"] == "yes" and m["type"] == "existing"}
    for r in reg["risks"]:
        if not r["raised_by"].strip():
            err("raised-by", r["id"], "record who raised this risk")
        if r["rating"] == "high" and r["destination"] == "background" and not r["officer_decision"].strip():
            err("officer-decision", r["id"], "a high-rated risk moves to background only with the Investment Officer's decision")
        if r["destination"] and not r["reason"].strip():
            warn("destination-reason", r["id"], "give a reason for the destination")
    for m in reg["mitigants"]:
        if m["risk"] not in risks:
            err("link", m["id"], f"mitigant points to unknown risk {m['risk']!r}")
        if not m["raised_by"].strip():
            err("raised-by", m["id"], "record who raised this mitigant")
        if m["verified"] == "yes" and not m["source"].strip():
            err("evidence", m["id"], "a verified mitigant needs a source")
        elif m["source"].strip():
            for message in source_errors(m["source"], sources):
                err("evidence", m["id"], message)
    for o in reg["open_items"]:
        if o["link"].startswith("R-") and o["link"] not in risks:
            err("link", o["id"], f"open item points to unknown risk {o['link']!r}")
        if not o["raised_by"].strip():
            err("raised-by", o["id"], "record who raised this item")
        decision = o.get("officer_decision", "").strip()
        if o["status"] in {"answered", "recheck"} or (o["status"] == "closed" and not decision):
            if not o["answer_source"].strip():
                err("evidence", o["id"], "an answered or closed item needs an answer source")
        if o["answer_source"].strip():
            for message in source_errors(o["answer_source"], sources):
                err("evidence", o["id"], message)
        if o["status"] == "closed":
            previous = next((answer for entry in reversed(reg["log"])
                             for answer in entry.get("reopened_answers", []) if answer["id"] == o["id"]), {})
            if not decision or decision == previous.get("officer_decision"):
                if previous and all(o[k] == previous[k] for k in
                                    ("answer", "answer_source", "assessment", "assessed_by")):
                    err("assessment", o["id"], "changed evidence needs a new assessment, not the previous answer replayed")
                cited = evidence_ids(reg, o)
                covered = set()
                for source_id in cited - superseded:
                    while (source_id in sources and sources[source_id]["supersedes"]
                           and sources[source_id]["supersedes"] not in covered):
                        source_id = sources[source_id]["supersedes"]
                        covered.add(source_id)
                if (cited & superseded) - covered:
                    err("answer-currentness", o["id"], "superseded answer evidence needs its current replacement "
                        "in answer_source or a new attributed Investment Officer exception")
                if any(claims[i]["recheck"] != "no" for i in cited if i in claims):
                    err("answer-currentness", o["id"], "cited claims need reassessment before answer closure")
            if not o.get("assessment", "").strip():
                err("assessment", o["id"], "closure needs an assessment of the answer or remaining gap")
            if not o.get("assessed_by", "").strip():
                err("assessor", o["id"], "closure needs an assessor in assessed_by")
            if decision and (":" not in decision or not decision.split(":", 1)[0].strip()
                             or not decision.split(":", 1)[1].strip()):
                err("officer-decision", o["id"], "attribute officer_decision as 'Investment Officer name, date: decision'")
        r = risks.get(o["link"])
        if (o["criticality"] == "later" and r and r["destination"] == "main" and r["id"] not in verified
                and o["officer_ok"] != "yes"):
            err("later-diligence", o["id"], f"{r['id']} is in the main document without an existing verified mitigant; "
                                            "'later' needs officer_ok=yes")
    for s in reg["sources"]:
        if s["sha256"] and not re.fullmatch(r"[0-9a-f]{64}", s["sha256"]):
            err("source-hash", s["id"], "sha256 must be a SHA-256 digest")
        if s["supersedes"] and (s["supersedes"] not in sources
                or int(s["supersedes"].split("-")[1]) >= int(s["id"].split("-")[1])):
            err("source-version", s["id"], "supersedes must identify an earlier source ID")
        if s["tier"] == "A" and s["coverage"] != "read":
            warn("tier-a-read", s["id"], f"tier A source is {s['coverage'] or 'unread'}")
        if s["impact"] == "pending":
            warn("impact-pending", s["id"], "assess what this source changes")
    for r in reg["risks"]:
        if r["status"] == "recheck":
            warn("recheck", r["id"], "recheck this risk against the latest evidence")
    known = {r["id"] for name in TABLES for r in reg[name]}
    for name in ("claims", "analysis"):
        for row in reg[name]:
            if row["sources"].strip():
                for message in source_errors(row["sources"], sources):
                    err("evidence", row["id"], message)
            if name == "claims":
                if not row["assertion"].strip() or not row["kind"].strip():
                    err("claim", row["id"], "a material claim needs an assertion and kind")
                if row["value"].strip() or row["kind"] == "calculation":
                    required = ["value", "unit", "entity", "period", "definition"]
                    if row["kind"] == "calculation":
                        required += ["inputs", "method"]
                    missing = [k for k in required if not row[k].strip()]
                    if missing:
                        err("numeric-claim", row["id"], "numeric/calculation claim needs " + ", ".join(missing))
                linked = ID_RE.findall(row["inputs"])
                if any(i not in known for i in linked):
                    err("claim-link", row["id"], "inputs cite unknown IDs")
                if SOURCE_RE.search(row["inputs"]):
                    for message in source_errors(row["inputs"], sources):
                        err("evidence", row["id"], message)
            elif any(i not in claims for i in link_ids(row["claims"])):
                err("claim-link", row["id"], "analysis cites unknown claims")
    dates = {s["id"]: s["event_date"] for s in reg["sources"] if s["event_date"]}
    cutoff = ((today or datetime.date.today()) - datetime.timedelta(days=365)).isoformat()
    for f in reg["fp_map"]:
        cited = link_ids(f["ids"])
        unknown = [i for i in cited if i not in known]
        if unknown:
            err("fp-map-link", f["id"], "cites unknown ids " + ", ".join(unknown))
        src = [dates[i] for i in cited if i in dates]
        if src and max(src) < cutoff:
            warn("stale-sources", f["id"], "every cited source is more than 12 months old")
    return out


def open_checks(reg):
    return [f"{n} rule errors" for n in [sum(p[0] == "error" for p in problems(reg))] if n] + gates(reg)


# ---------- views for the assistant ----------

def short(text, n=90):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + "…"


def tally(*counters):
    parts = [", ".join(f"{k} {v}" for k, v in sorted(c.items())) for c in counters if c]
    return f" ({'; '.join(parts)})" if parts else ""


def checks_line(reasons):
    return "Open checks: " + ("; ".join(reasons) if reasons else "none")


def summary(reg):
    c = reg["control"]
    lines = [f"{c['deal']} · register revision {reg['revision']}"]
    if c["status"] == "ready":
        lines.append(f"Status: ready ({c['ready_for']}, recorded by {c['ready_by'] or 'unknown'})")
    else:
        lines.append(f"Status: {c['status'] or 'draft'}")
    if c["word"]:
        lines.append(f"Document: {c['word']}")
    if reg["log"] and reg["log"][-1]["next_step"]:
        lines.append(f"Next: {reg['log'][-1]['next_step']}")
    src = reg["sources"]
    tier_a = [s for s in src if s["tier"] == "A"]
    lines.append(f"Sources: {len(src)} · tier A read {sum(s['coverage'] == 'read' for s in tier_a)}/{len(tier_a)}"
                 f" · impact pending {sum(s['impact'] == 'pending' for s in src)}")
    dest = Counter(r["destination"] or "unplaced" for r in reg["risks"] if r["status"] != "closed")
    lines.append(f"Risks: {sum(dest.values())} open{tally(dest)}"
                 f" · recheck {sum(r['status'] == 'recheck' for r in reg['risks'])}")
    opened = [o for o in reg["open_items"] if o["status"] != "closed"]
    state = Counter(o["status"] or "open" for o in opened)
    crit = Counter(o["criticality"] or "unrated" for o in opened)
    lines.append(f"Open items: {len(opened)} not closed{tally(state, crit)}")
    lines.append(f"Findings: {sum(f['status'] != 'resolved' for f in reg['findings'])} unresolved")
    lines.append(checks_line(open_checks(reg)))
    rank = {"blocker": 0, "material": 1}
    top = sorted(opened, key=lambda o: (rank.get(o["criticality"], 2), o["due"] or "9999"))[:5]
    if top:
        lines.append("Top open items:")
        lines += [f"  {o['id']} [{o['criticality'] or '-'}] {o['addressee'] or '-'}: {short(o['text'])}"
                  + (f" ({o['link']})" if o["link"] else "") + (f" due {o['due']}" if o["due"] else "")
                  + (f" — {o['status']}" if o["status"] != "open" else "") for o in top]
    probs = problems(reg)
    lines.append(f"Rule problems: {sum(p[0] == 'error' for p in probs)} errors, "
                 f"{sum(p[0] == 'warning' for p in probs)} warnings")
    lines += [f"  {p[0].upper()} {p[2]}: {short(p[3])}" for p in probs[:5]]
    if reg["log"]:
        lines.append("Recent:")
        lines += [f"  r{e['revision']} {e['at'][:10]} {e['actor']}: {short(e['summary'])}" for e in reg["log"][-3:]]
    return "\n".join(lines)


def show(reg, ids, section=None):
    if section:
        mapped = [r for r in reg["fp_map"] if r["section"] == section]
        selected = set(ids) | {i for row in mapped for i in link_ids(row["ids"])}
        selected.update(i for row in reg["analysis"] if row["id"] in selected
                        for i in ID_RE.findall(row["claims"]))
        selected.update(r["id"] for r in reg["claims"]
                        if section in {s.strip() for s in re.split(r"[,;\n]", r["sections"])})
        for _ in reg["claims"]:
            linked = {i for r in reg["claims"] if r["id"] in selected
                      for i in ID_RE.findall(r["inputs"] + " " + r["qualifications"])}
            linked.update(r["id"] for r in reg["claims"]
                          if selected.intersection(ID_RE.findall(r["qualifications"])))
            if linked <= selected:
                break
            selected.update(linked)
        claims = [r for r in reg["claims"] if r["id"] in selected]
        analyses = [r for r in reg["analysis"] if r["id"] in selected
                    or selected.intersection(ID_RE.findall(r["claims"]))]
        selected.update(r["id"] for r in analyses + mapped)
        selected.update(i for r in claims + analyses for i in SOURCE_RE.findall(r["sources"] + " " + r.get("inputs", "")))
        selected.update(r["id"] for r in reg["sources"] if r["supersedes"] in selected)
        selected.update(r["supersedes"] for r in reg["sources"] if r["id"] in selected and r["supersedes"])
        strategy = next((r["text"] for r in reg["analysis"] if r["id"] == "strategy"), "not recorded")
        return (f"Section: {section}\nThis selection is not a complete substantive review.\n"
                f"Strategy: {short(strategy, 800)}\n\n" + (show(reg, sorted(selected)) if selected else ""))
    if not ids:
        out = [f"{reg['control']['deal']} · evidence index · register revision {reg['revision']}"]
        strategy = next((r["text"] for r in reg["analysis"] if r["id"] == "strategy"), "not recorded")
        out.append(f"Strategy: {short(strategy, 800)}")
        for name, title in (("sources", "title"), ("claims", "assertion")):
            entries = reg[name]
            out.append(f"{name.capitalize()}: {len(entries)}"
                       + (" (first 20 shown; full index in register.json)" if len(entries) > 20 else ""))
            for row in entries[:20]:
                context = f"{short(row['entity'] or '-', 32)} / {short(row['period'] or '-', 24)}"
                if name == "sources":
                    state = f"coverage {row['coverage']}; impact {row['impact']}"
                    reference = row["link"] or row["extract_path"]
                else:
                    state = f"support {short(row['support'] or 'unknown', 32)}; recheck {row['recheck']}"
                    reference = row["sources"] or row["inputs"]
                out.append(f"  {row['id']}: {short(row[title], 72)} | {context} | {state}"
                           f" | {short(reference or 'no located reference', 120)}")
        out.append("Use show FOLDER ID [ID ...] for full records; this index is not a substantive review.")
        return "\n".join(out)
    rows = {r["id"]: (name, r) for name in TABLES if name != "analysis" for r in reg[name]}
    for r in reg["analysis"]:
        rows.setdefault(r["id"], ("analysis", r))
    out = []
    cited = set()
    for i in ids:
        if i not in rows:
            out.append(f"{i}: not found")
            continue
        name, r = rows[i]
        cited.update(evidence_ids(reg, r))
        out.append(f"{i} ({name})")
        out += [f"  {k}: {v}" for k, v in r.items() if v and k != "id"]
        if name == "risks":
            out += [f"  mitigant {m['id']}: {m['text']} [{m['type']}, verified {m['verified'] or '-'}]"
                    for m in reg["mitigants"] if m["risk"] == i]
            out += [f"  open item {o['id']}: {o['text']} [{o['status']}]" for o in reg["open_items"] if o["link"] == i]
        for analysis in reg["analysis"]:
            if analysis["id"] == i and name != "analysis":
                cited.update(evidence_ids(reg, analysis))
                out.append(f"{i} (analysis)")
                out += [f"  {k}: {v}" for k, v in analysis.items() if v and k != "id"]
    links = original_sources(reg, cited - set(ids))
    if links:
        out += ["Original sources:"] + links
    return "\n".join(out)


def client_requests(reg):
    return [o for o in reg["open_items"] if o.get("audience") == "client" and o["status"] in {"open", "promised"}]


def ddq(reg):
    """Only explicitly client-facing requests; no internal assessments or risk links."""
    lines = [f"# {reg['control']['deal']} — client requests", "",
             f"Register revision {reg['revision']}", ""]
    for row in client_requests(reg):
        lines += [f"## {row['id']}", "", row["text"], ""]
        lines += [f"{label}: {row[key]}" for key, label in (("purpose", "Purpose"), ("due", "Due")) if row[key]]
        if row["status"] == "promised":
            lines.append("Promised; awaiting evidence.")
        lines.append("")
    return "\n".join(lines if client_requests(reg) else lines + ["No open client requests."])


def lists(reg):
    opened = [o for o in reg["open_items"] if o["status"] != "closed"]
    client = client_requests(reg)
    internal = [o for o in opened if o not in client]
    state = {"promised": " — promised, awaiting evidence", "answered": " — answered, awaiting assessment",
             "recheck": " — answer evidence changed, reassess before closure or a new client request"}
    item = lambda o: (f"- {o['id']} [{o['criticality'] or '-'}] {o['text']}"  # noqa: E731
                      + (f" ({o['link']})" if o["link"] else "") + state.get(o["status"], "")
                      + (f" — due {o['due']}" if o["due"] else ""))
    conditions = [m for m in reg["mitigants"] if m["type"] == "proposed-condition" and m["status"] != "closed"]
    out = ["## Client requests", ""] + ([item(o) for o in client] or ["- none"])
    out += ["", "## Internal open points", ""] + ([item(o) for o in internal] or ["- none"])
    out += ["", "## Proposed conditions", ""] + ([f"- {m['id']} ({m['risk']}) {m['text']}" for m in conditions]
                                                  or ["- none"])
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("folder")
    p.add_argument("--deal", required=True)
    p = sub.add_parser("show")
    p.add_argument("folder")
    p.add_argument("ids", nargs="*")
    p.add_argument("--section")
    p = sub.add_parser("apply")
    p.add_argument("folder")
    p.add_argument("changes")
    for name in ("summary", "check", "lists", "ddq", "migrate", "refresh"):
        p = sub.add_parser(name)
        p.add_argument("folder")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "init":
            if (Path(args.folder) / "register.json").exists():
                raise ChangeError("register.json already exists here")
            Path(args.folder).mkdir(parents=True, exist_ok=True)
            save(args.folder, new_register(args.deal))
            print(f"created register for {args.deal} at revision 0")
        elif args.cmd == "summary":
            print(summary(load(args.folder)))
        elif args.cmd == "show":
            print(show(load(args.folder), args.ids, args.section))
        elif args.cmd == "apply":
            result = apply(args.folder, json.loads(Path(args.changes).read_text(encoding="utf-8")))
            print(json.dumps(result, indent=1))
        elif args.cmd == "lists":
            print(lists(load(args.folder)))
        elif args.cmd == "ddq":
            print(ddq(load(args.folder)))
        elif args.cmd == "migrate":
            print(json.dumps(migrate(args.folder), indent=1))
        elif args.cmd == "refresh":
            print(json.dumps(refresh(args.folder), indent=1))
        elif args.cmd == "check":
            reg = load(args.folder)
            probs = problems(reg)
            print("\n".join(f"{p[0].upper()} {p[1]} {p[2]}: {p[3]}" for p in probs) or "no problems")
            reasons = open_checks(reg)
            print(checks_line(reasons))
            return 1 if reasons else 0
    except ViewsIncompleteError as e:
        print(f"SAVED: {e}", file=sys.stderr)
        return 4
    except (ChangeError, json.JSONDecodeError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
