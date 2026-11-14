"""Build the standard: check it, write the file the tool reads, write pages for a website.

    python3 standard/build.py                 check, and write bankability2/standard.json
    python3 standard/build.py --site DIR      also write one Markdown page per indicator and folder

Needs PyYAML. The tool itself does not: it reads the JSON file.
"""
import glob
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "..", "bankability2", "standard.json")
ANSWERS = {"yes_no", "number", "choice", "text"}
TIERS = ("best", "supporting", "stated")
FLAG = re.compile(r"^(above|below|at most|at least) -?\d+(\.\d+)?$|^is (not )?\w+$")


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return yaml.safe_load(f)


def load():
    std = read("standard.yaml")
    for name in ("stages", "workstreams", "subject-kinds", "link-types", "source-kinds"):
        std.update(read(f"lists/{name}.yaml"))
    std["dataroom"] = read("dataroom.yaml")
    paths = sorted(glob.glob(os.path.join(HERE, "indicators", "*", "*.yaml")))
    std["indicators"] = [read(os.path.relpath(p, HERE)) for p in paths]
    return std


def slots_of(std):
    return [slot for f in std["dataroom"]["folders"] for sf in f["sub_folders"] for slot in sf["slots"]]


def validate(std):
    """Return a list of problems. An empty list means the standard is sound."""
    problems = []
    stages = {s["id"] for s in std["stages"]}
    workstreams = {w["id"] for w in std["workstreams"]}
    kinds = {k["id"] for k in std["source_kinds"]}
    slots = {s["id"] for s in slots_of(std)}
    roles = {l[r] for l in std["link_types"] for r in ("role_from", "role_to") if r in l}
    targets = [{"deal"}, roles, {k["id"] for k in std["subject_kinds"]}, {l["id"] for l in std["link_types"]}]
    applicable = set().union(*targets)
    if sum(len(t) for t in targets) != len(applicable):
        problems.append("a role, a subject kind and a link type share a name")
    indicators = {i["id"] for i in std["indicators"]}
    checks = [c["id"] for i in std["indicators"] for c in i["checks"]]
    for name, ids in (("indicator", [i["id"] for i in std["indicators"]]), ("check", checks),
                      ("slot", [s["id"] for s in slots_of(std)]), ("kind of source", [k["id"] for k in std["source_kinds"]])):
        problems += [f"{name} {i} appears twice" for i in sorted(set(ids)) if ids.count(i) > 1]
    checks = set(checks)

    def need(where, ok, message):
        if not ok:
            problems.append(f"{where}: {message}")

    def conditions(where, items):
        for item in items or []:
            need(where, item.get("check") in checks, f"unknown check {item.get('check')}")

    for kind in std["source_kinds"]:
        need(kind["id"], kind.get("slot") is None or kind["slot"] in slots, f"unknown slot {kind.get('slot')}")
    for ind in std["indicators"]:
        iid = ind["id"]
        own = {c["id"] for c in ind["checks"]}
        need(iid, ind["workstream"] in workstreams, f"unknown workstream {ind['workstream']}")
        need(iid, ind["due_by"] in stages, f"unknown stage {ind['due_by']}")
        need(iid, set(ind["applies_to"]) <= applicable, f"applies_to names something unknown: {ind['applies_to']}")
        for key in ("applies_when", "matters_more_when", "matters_less_when"):
            conditions(iid, ind.get(key))
        conditions(iid, [i for i in ind.get("look_again_when", []) if "check" in i])
        for side in ("risk", "mitigant"):
            need(iid, set(ind.get(side, {}).get("checks", [])) <= own, f"{side} names a check of another indicator")
        for item in ind.get("look_again_when", []):
            need(iid, item.get("new_source") is None or item["new_source"] in kinds, "unknown kind of source")
            need(iid, set(item.get("checks", [])) <= checks, "look_again_when names an unknown check")
        for check in ind["checks"]:
            cid = check["id"]
            need(cid, check["answer"] in ANSWERS, f"unknown answer type {check['answer']}")
            need(cid, check["answer"] != "choice" or check.get("options"), "a choice needs options")
            need(cid, check.get("due_by", ind["due_by"]) in stages, f"unknown stage {check.get('due_by')}")
            need(cid, set(check.get("applies_to", [])) <= applicable, "applies_to names something unknown")
            need(cid, set(check.get("after", [])) <= checks, f"after names an unknown check: {check.get('after')}")
            conditions(cid, check.get("when"))
            need(cid, set(check.get("look_in", [])) <= slots, f"unknown slot in {check.get('look_in')}")
            for tier, names in check.get("evidence", {}).items():
                need(cid, tier in TIERS and set(names) <= kinds, f"evidence '{tier}' has an unknown name")
            if "disproved_by" in check:
                ok = check["answer"] == "yes_no" and "assumption" in check and check["disproved_by"] in ("yes", "no")
                need(cid, ok, "disproved_by needs a yes/no check with an assumption")
            need(cid, "flag_when" not in check or FLAG.match(check["flag_when"]), "flag_when is not understood")
            need(cid, check.get("ask_whom", "client") in ("client", "lender"), "ask_whom must be client or lender")
            for lead in check.get("leads_to", []):
                need(cid, lead["indicator"] in indicators, f"leads to unknown indicator {lead['indicator']}")
    return problems


# ---------------------------------------------------------------- pages for a website

def page(path, title, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{title}\"\n---\n\n# {title}\n\n" + "\n".join(lines).rstrip() + "\n")


def said(cond):
    if cond.get("answered"):
        return "is answered"
    value = cond["is"]
    return "is " + ("yes" if value is True else "no" if value is False else f"`{value}`")


def check_lines(check, std_names):
    title, slot_page = std_names
    lines = [f"### {check['id']}", "", check["question"], ""]
    if "assumption" in check:
        by = f" A {check['disproved_by']} disproves it." if "disproved_by" in check else ""
        lines.append(f"- **Assumption tested:** {check['assumption']}.{by}")
    for key, label in (("why", "Why it is asked"), ("flag_when", "Reference point"), ("unit", "Unit"),
                       ("due_by", "Ideally answered by")):
        if key in check:
            lines.append(f"- **{label}:** {title.get(check[key], check[key])}")
    if "options" in check:
        lines.append("- **Options:** " + ", ".join(f"`{o}`" for o in check["options"]))
    if "after" in check:
        lines.append("- **Asked after:** " + ", ".join(check["after"]))
    if "when" in check:
        lines.append("- **Asked when:** " + " or ".join(f"{c['check']} {said(c)}" for c in check["when"]))
    if "look_in" in check:
        lines.append("- **Where to look:** " + ", ".join(f"[{s}]({slot_page(s)})" for s in check["look_in"]))
    for tier in TIERS:
        if tier in check.get("evidence", {}):
            lines.append(f"- **Evidence, {tier}:** " + ", ".join(title[k] for k in check["evidence"][tier]))
    for key, label in (("ask", "How to ask"), ("if_unknown", "If unknown"), ("note", "Note")):
        if key in check:
            lines.append(f"- **{label}:** {check[key]}")
    if check.get("ask_whom") == "lender":
        lines.append("- **Asked of:** the lender, not the client")
    for lead in check.get("leads_to", []):
        lines.append(f"- **Leads to:** [{lead['indicator']}]({lead['indicator']}.md) when the answer {said(lead)}. {lead['reason']}.")
    return lines + [""]


def write_site(std, out):
    title = {x["id"]: x["title"] for key in ("stages", "workstreams", "source_kinds", "link_types", "subject_kinds")
             for x in std[key]}

    def slot_page(slot, up="../"):
        return f"{up}dataroom/{slot[:2]}.md#{slot.replace('.', '')}"

    for ind in std["indicators"]:
        lines = [f"- **Workstream:** {title[ind['workstream']]}", f"- **Ideally done by:** {title[ind['due_by']]}",
                 "- **Applies to:** " + ", ".join(ind["applies_to"])]
        if "applies_when" in ind:
            lines.append("- **Only when:** " + " or ".join(f"{c['check']} {said(c)}" for c in ind["applies_when"]))
        for side in ("risk", "mitigant"):
            if side in ind:
                lines.append(f"- **{side.capitalize()} statement:** {ind[side]['statement']}")
        for who, why in ind.get("why_it_matters", {}).items():
            lines.append(f"- **Why it matters, {who}:** {why}")
        for key, label in (("matters_more_when", "Matters more"), ("matters_less_when", "Matters less")):
            for item in ind.get(key, []):
                lines.append(f"- **{label}** when {item['check']} {said(item)}. {item['reason']}.")
        for item in ind.get("look_again_when", []):
            lines.append(f"- **Look again:** {item['reason']}.")
        lines += ["", "## Checks", ""]
        for check in ind["checks"]:
            lines += check_lines(check, (title, slot_page))
        page(os.path.join(out, "indicators", ind["id"] + ".md"), ind["title"], lines)

    looked_in = {}
    for ind in std["indicators"]:
        link = f"[{ind['title']}](../indicators/{ind['id']}.md)"
        for slot in {s for check in ind["checks"] for s in check.get("look_in", [])}:
            looked_in.setdefault(slot, []).append(link)
    for folder in std["dataroom"]["folders"]:
        lines = []
        for sub in folder["sub_folders"]:
            lines += [f"## {sub['id']} {sub['title']}", ""]
            for slot in sub["slots"]:
                belongs = [k["title"] for k in std["source_kinds"] if k.get("slot") == slot["id"]]
                lines += [f"### {slot['id']} {slot['title']} <a id=\"{slot['id'].replace('.', '')}\"></a>", "",
                          slot["holds"], "", f"- **Expected:** {slot['expected']}"]
                if belongs:
                    lines.append("- **Kinds of source filed here:** " + ", ".join(belongs))
                if slot["id"] in looked_in:
                    lines.append("- **Indicators that look here:** " + ", ".join(looked_in[slot["id"]]))
                lines.append("")
        page(os.path.join(out, "dataroom", folder["id"] + ".md"), f"{folder['id']} {folder['title']}", lines)

    lines = [std["description"], "", f"Version {std['version']}.", "", "## Indicators", ""]
    for ws in std["workstreams"]:
        lines += [f"### {ws['title']}", ""]
        lines += [f"- [{i['title']}](indicators/{i['id']}.md)" for i in std["indicators"] if i["workstream"] == ws["id"]]
        lines.append("")
    lines += ["## Data room", ""]
    lines += [f"- [{f['id']} {f['title']}](dataroom/{f['id']}.md)" for f in std["dataroom"]["folders"]]
    lines += ["", "## Lists", "", "- [Stages, kinds of subject, kinds of link and kinds of source](lists.md)"]
    page(os.path.join(out, "index.md"), std["name"], lines)

    lines = ["## Stages", "", "| Stage | Purpose | Ideal evidence | Ideal age, months |", "|---|---|---|---|"]
    lines += [f"| {s['title']} | {s['purpose']} | {s['ideal_evidence']} | {s['ideal_max_age_months']} |" for s in std["stages"]]
    lines += ["", "## Kinds of subject", "", "| Kind | What it is |", "|---|---|"]
    lines += [f"| {k['title']} | {k['description']} |" for k in std["subject_kinds"]]
    lines += ["", "## Kinds of link", "", "| Link | What it means | Role it gives |", "|---|---|---|"]
    lines += [f"| {l['title']} | {l['description']} | {l.get('role_from') or l.get('role_to') or ''} |" for l in std["link_types"]]
    lines += ["", "## Kinds of source", "", "| Kind | What it is | Data-room slot |", "|---|---|---|"]
    lines += [f"| {k['title']} | {k['description']} | {k.get('slot', 'internal folder')} |" for k in std["source_kinds"]]
    page(os.path.join(out, "lists.md"), "Lists", lines)


def main():
    std = load()
    problems = validate(std)
    if problems:
        sys.exit("\n".join(problems))
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(std, f, indent=1, ensure_ascii=False)
        f.write("\n")
    checks = sum(len(i["checks"]) for i in std["indicators"])
    print(f"{std['name']} {std['version']}: {len(std['indicators'])} indicators, {checks} checks")
    if "--site" in sys.argv:
        write_site(std, sys.argv[sys.argv.index("--site") + 1])


if __name__ == "__main__":
    main()
