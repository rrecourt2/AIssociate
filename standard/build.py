"""Build the standard: check it, write the file the tool reads, write pages for a website.

    python3 standard/build.py                 check, and write bankability2/standard.json
    python3 standard/build.py --site DIR      also write one Markdown page per indicator and folder

Needs PyYAML. The tool itself does not: it reads the JSON file.
"""
import glob
import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from bankability2.standard import problems  # noqa: E402  the tool's own check of a standard

JSON_PATH = os.path.join(HERE, "..", "bankability2", "standard.json")
TIERS = ("best", "supporting", "stated")


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return yaml.safe_load(f)


def load():
    std = read("standard.yaml")
    for name in ("stages", "pillars", "subject-kinds", "link-types", "source-kinds"):
        std.update(read(f"lists/{name}.yaml"))
    std["dataroom"] = read("dataroom.yaml")
    paths = sorted(glob.glob(os.path.join(HERE, "indicators", "*", "*.yaml")))
    order = [pillar["id"] for pillar in std["pillars"]]
    std["indicators"] = sorted((read(os.path.relpath(p, HERE)) for p in paths), key=lambda ind: order.index(ind["pillar"]) if ind.get("pillar") in order else len(order))
    return std


# ---------------------------------------------------------------- pages for a website

def page(path, title, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{title}\"\n---\n\n# {title}\n\n" + "\n".join(lines).rstrip() + "\n")


def said(cond):
    if cond.get("answered"):
        return "is answered"
    if cond.get("against"):
        return "goes against its assumption"
    if "is" not in cond:
        return "is given"
    value = cond["is"]
    return "is " + ("yes" if value is True else "no" if value is False else f"`{value}`")


def check_lines(check, std_names):
    title, slot_page = std_names
    job = "Mitigant" if check.get("mitigant") else "Test" if "assumption" in check else "Question"
    lines = [f"### {check['id']}", "", check["question"], "", f"- **Job:** {job}"]
    if "assumption" in check:
        by = f" A {check['disproved_by']} disproves it." if "disproved_by" in check else ""
        lines.append(f"- **Assumption:** {check['assumption']}.{by}")
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
    for call in check.get("calls_for", []):
        wanted = f"a {call['kind']}" if "kind" in call else "a link of kind " + " or ".join(f"`{name}`" for name in call["link"])
        wanted += f", with the subject asked about at its `{call['end']}` end" if "end" in call else ""
        lines.append(f"- **Calls for:** {wanted} in the structure, when the answer {said(call)}")
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
    title = {x["id"]: x["title"] for key in ("stages", "pillars", "source_kinds", "link_types", "subject_kinds")
             for x in std[key]}

    def slot_page(slot, up="../"):
        return f"{up}dataroom/{slot[:2]}.md#{slot.replace('.', '')}"

    for ind in std["indicators"]:
        lines = [f"**The claim:** {ind['claim']}", "", f"- **Pillar:** {title[ind['pillar']]}",
                 f"- **Ideally done by:** {title[ind['due_by']]}", "- **Asked about:** " + ", ".join(ind["applies_to"])]
        if "applies_when" in ind:
            lines.append("- **Only when:** " + " or ".join(f"{c['check']} {said(c)}" for c in ind["applies_when"]))
        for key, label in (("matters_more_when", "Matters more"), ("matters_less_when", "Matters less")):
            for item in ind.get(key, []):
                lines.append(f"- **{label}** when {item['check']} {said(item)}. {item['reason']}.")
        for item in ind.get("look_again_when", []):
            lines.append(f"- **Look again:** {item['reason'].rstrip('.')}.")
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
    for pillar in std["pillars"]:
        lines += [f"### {pillar['title']}", "", pillar["description"], ""]
        lines += [f"- [{i['title']}](indicators/{i['id']}.md): {i['claim']}" for i in std["indicators"] if i["pillar"] == pillar["id"]]
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
    lines += [f"| {l['title']} (`{l['id']}`) | {l['description']} | {l.get('role_from') or l.get('role_to') or ''} |"
              for l in std["link_types"]]
    lines += ["", "## Kinds of source", "", "| Kind | What it is | Data-room slot |", "|---|---|---|"]
    lines += [f"| {k['title']} | {k['description']} | {k.get('slot', 'internal folder')} |" for k in std["source_kinds"]]
    page(os.path.join(out, "lists.md"), "Lists", lines)


def main():
    std = load()
    found = problems(std)
    if found:
        sys.exit("\n".join(found))
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(std, f, indent=1, ensure_ascii=False)
        f.write("\n")
    checks = sum(len(i["checks"]) for i in std["indicators"])
    print(f"{std['name']} {std['version']}: {len(std['indicators'])} indicators, {checks} checks")
    if "--site" in sys.argv:
        write_site(std, sys.argv[sys.argv.index("--site") + 1])


if __name__ == "__main__":
    main()
