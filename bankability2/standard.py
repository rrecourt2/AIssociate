"""The standard a deal uses: the base, adjusted by the institution's layer and then by the deal's layer."""
import re

from . import files
from .files import Refused

ANSWERS = ("yes_no", "number", "choice", "text")
TIERS = ("stated", "supporting", "best")  # weakest first
STRENGTHS = ("not_now", "not_for_this_deal")
FLAG = re.compile(r"^(above|below|at most|at least) (-?\d+(?:\.\d+)?)$|^is (not )?(\w+)$")


def slots_of(std):
    return [slot for folder in std["dataroom"]["folders"] for sub in folder["sub_folders"] for slot in sub["slots"]]


def find(std, target):
    """The indicator, the check or the list entry that an ID names, or None. A list entry is named as "stage:concept"."""
    if ":" in target:
        name, _, rid = target.partition(":")
        entries = {"stage": std["stages"], "slot": slots_of(std), "kind": std["source_kinds"],
                   "link": std["link_types"]}.get(name, [])
        return next((entry for entry in entries if entry["id"] == rid), None)
    for ind in std["indicators"]:
        if ind["id"] == target:
            return ind
        for check in ind["checks"]:
            if check["id"] == target:
                return check
    return None


def adjust(std, item, layer):
    """Apply one adjustment to the standard. Returns a problem, or None."""
    do, target = item.get("do"), item.get("target", "")
    if layer == "deal" and not item.get("reason"):
        return f"{do!r} needs a 'reason'"
    if do == "add":
        home = find(std, item.get("to", "")) if "check" in item else std
        new = item.get("check") or item.get("indicator")
        fits = isinstance(new, dict) and "id" in new and isinstance((home or {}).get("checks", new.get("checks")), list)
        if not fits or find(std, new["id"]):
            return "add needs a check with a new ID and the indicator it goes 'to', or a whole indicator with its checks"
        (home["checks"] if "check" in item else std["indicators"]).append(dict(new))
        return None
    found = find(std, target)
    if found is None:
        return f"{target!r} names nothing in the standard"
    if layer == "deal" and found.get("locked") and do in ("change", "switch_off"):
        return f"{target} is locked by the institution: {found['locked']}"
    if do == "change" and isinstance(item.get("set"), dict):
        found.update(item["set"])
    elif do == "switch_off" and item.get("strength") in STRENGTHS and item.get("reason"):
        found["off"] = {key: item.get(key) for key in ("strength", "reason", "by", "date", "rev", "stage")}
    elif do == "switch_on":
        found.pop("off", None)
    elif do == "lock" and layer == "institution" and item.get("reason"):
        found["locked"] = item["reason"]
    else:
        return (f"{do!r} on {target}: use add, change (with 'set'), switch_off (with 'strength' {' or '.join(STRENGTHS)} "
                "and a 'reason'), switch_on, or lock (institution layer only, with a 'reason')")
    return None


def effective(deal, extra=()):
    """The standard as this deal uses it. `extra` holds adjustments that are being tried out."""
    std = files.read_json(deal, files.BASE)
    if std is None:
        raise Refused(f"{deal} is not a deal folder: it holds no {files.BASE}")
    notes, std["systems"] = [], []
    for layer, path in (("institution", files.INSTITUTION), ("deal", files.DEAL_LAYER)):
        stored = files.read_json(deal, path, {})
        std["systems"] += stored.get("systems", [])
        for item in stored.get("adjustments", []) + (list(extra) if layer == "deal" else []):
            problem = adjust(std, item, layer)
            if problem:
                notes.append(f"{layer} layer: {problem}")
    std["notes"] = notes + problems(std)
    return index(std)


def index(std):
    """Add the lookups the tool uses. They are computed on every run and never stored."""
    std["stage_ids"] = [stage["id"] for stage in std["stages"]]
    std["stage_titles"] = {stage["id"]: stage["title"] for stage in std["stages"]}
    std["link_ids"] = {link["id"] for link in std["link_types"]}
    std["kinds_by_table"] = {"sources": {kind["id"] for kind in std["source_kinds"]},
                             "subjects": {kind["id"] for kind in std["subject_kinds"]}}
    std["by_id"] = {ind["id"]: ind for ind in std["indicators"]}
    std["checks"] = {}
    for ind in std["indicators"]:
        for check in ind["checks"]:
            check["indicator"] = ind["id"]
            std["checks"][check["id"]] = check
    return std


def problems(std):
    """What is unsound in a standard: an ID used twice, or a reference to something that does not exist."""
    found = []
    stages = {stage["id"] for stage in std["stages"]}
    kinds = {kind["id"] for kind in std["source_kinds"]}
    slots = [slot["id"] for slot in slots_of(std)]
    roles = {link[end] for link in std["link_types"] for end in ("role_from", "role_to") if end in link}
    groups = [{"deal"}, roles, {kind["id"] for kind in std["subject_kinds"]}, {link["id"] for link in std["link_types"]}]
    applicable = set().union(*groups)
    if sum(len(group) for group in groups) != len(applicable):
        found.append("a role, a kind of subject and a kind of link share a name")
    indicators = [ind["id"] for ind in std["indicators"]]
    checks = [check["id"] for ind in std["indicators"] for check in ind["checks"]]
    for name, ids in (("indicator", indicators), ("check", checks), ("slot", slots),
                      ("kind of source", [kind["id"] for kind in std["source_kinds"]])):
        found += [f"{name} {rid} appears twice" for rid in sorted(set(ids)) if ids.count(rid) > 1]

    def need(where, ok, message):
        if not ok:
            found.append(f"{where}: {message}")

    def known_checks(where, items):
        for item in items or []:
            need(where, item.get("check") in checks, f"unknown check {item.get('check')!r}")

    for kind in std["source_kinds"]:
        need(kind["id"], kind.get("slot") is None or kind["slot"] in slots, f"unknown slot {kind.get('slot')!r}")
    for ind in std["indicators"]:
        iid, own = ind["id"], {check["id"] for check in ind["checks"]}
        need(iid, ind.get("workstream") in {ws["id"] for ws in std["workstreams"]}, "unknown workstream")
        need(iid, ind.get("due_by") in stages, f"unknown stage {ind.get('due_by')!r}")
        need(iid, set(ind.get("applies_to", ["?"])) <= applicable, "applies_to names something unknown")
        for key in ("applies_when", "matters_more_when", "matters_less_when"):
            known_checks(iid, ind.get(key))
        for side in ("risk", "mitigant"):
            need(iid, set(ind.get(side, {}).get("checks", [])) <= own, f"{side} names a check of another indicator")
        for item in ind.get("look_again_when", []):
            known_checks(iid, [item] if "check" in item else [])
            need(iid, item.get("new_source") is None or item["new_source"] in kinds, "unknown kind of source")
            need(iid, set(item.get("checks", [])) <= set(checks), "look_again_when names an unknown check")
        for check in ind["checks"]:
            cid = check["id"]
            need(cid, check.get("question") and check.get("answer") in ANSWERS, "needs a question and a known answer type")
            need(cid, check.get("answer") != "choice" or check.get("options"), "a choice needs options")
            need(cid, check.get("due_by", ind.get("due_by")) in stages, f"unknown stage {check.get('due_by')!r}")
            need(cid, set(check.get("applies_to", [])) <= applicable, "applies_to names something unknown")
            need(cid, set(check.get("after", [])) <= set(checks), f"after names an unknown check: {check.get('after')}")
            known_checks(cid, check.get("when"))
            need(cid, set(check.get("look_in", [])) <= set(slots), f"unknown slot in {check.get('look_in')}")
            for tier, names in check.get("evidence", {}).items():
                need(cid, tier in TIERS and set(names) <= kinds, f"evidence {tier!r} has an unknown name")
            if "disproved_by" in check:
                sound = check["answer"] == "yes_no" and "assumption" in check and check["disproved_by"] in ("yes", "no")
                need(cid, sound, "disproved_by needs a yes/no check with an assumption")
            need(cid, "flag_when" not in check or FLAG.match(str(check["flag_when"])), "flag_when is not understood")
            need(cid, check.get("ask_whom", "client") in ("client", "lender"), "ask_whom must be client or lender")
            for lead in check.get("leads_to", []):
                need(cid, lead.get("indicator") in indicators, f"leads to unknown indicator {lead.get('indicator')!r}")
    return found
