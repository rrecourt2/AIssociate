"""The standard a deal uses: the base, adjusted by the institution's layer and then by the deal's layer."""
import re

from . import files
from .files import Refused

ANSWERS = ("yes_no", "number", "choice", "text")
TIERS = ("stated", "supporting", "best")  # weakest first
ROUTES = {"company": "the company", "screening": "a screening", "terms": "the terms of the loan", "lender": "the lender",
          "expert": "an expert", "public": "public sources"}  # what settles a check, and how a reader is told
STRENGTHS = ("not_now", "not_for_this_deal")
FLAG = re.compile(r"^(above|below|at most|at least) (-?\d+(?:\.\d+)?)$|^is (not )?(\w+(?: or \w+)*)$")


EXPECTS = {"yes_no": "true or false", "number": "a number", "choice": "one of the check's options", "text": "text"}


def route(check):
    """What settles a check. A check that does not say, or that names something else, is taken to the company."""
    return check["settled_by"] if check.get("settled_by") in ROUTES else "company"


def takes(check):
    """The answer a check takes, as a person reads it: yes/no, a number with its unit, the options, or text."""
    if check["answer"] == "choice":
        return ("any of " if check.get("many") else "one of ") + " | ".join(check.get("options", []))
    if check["answer"] == "number":
        return "number" + (f", {check['unit']}" if check.get("unit") else "")
    return "yes/no" if check["answer"] == "yes_no" else "text"


def fits(check, value):
    """Whether a value is the kind of answer the check asks for."""
    if check["answer"] == "yes_no":
        return isinstance(value, bool)
    if check["answer"] == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if check["answer"] == "choice":
        values = value if isinstance(value, list) else [value]
        return bool(values) and all(option in check.get("options", []) for option in values)
    return isinstance(value, str)


def flag_fits(check):
    """Whether a reference point can be met by the kind of answer the check asks for."""
    rule = FLAG.match(str(check.get("flag_when")))
    if not rule:
        return False
    if rule.group(1):
        return check["answer"] == "number"
    return check["answer"] == "choice" and set(rule.group(4).split(" or ")) <= set(check.get("options", []))


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
    home = next((ind for ind in std["indicators"] if any(found is check for check in ind["checks"])), {})
    locked = next((one["locked"] for one in (found, home, *found.get("checks", [])) if one.get("locked")), None)
    if layer == "deal" and locked and do in ("change", "switch_off"):  # a lock covers an indicator and its checks
        return f"{target} is locked by the institution: {locked}"
    if do == "change" and isinstance(item.get("set"), dict):
        found.update(item["set"])
        for key in [key for key, value in item["set"].items() if value is None]:
            del found[key]  # setting a field to null takes it off
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
    links = {link["id"] for link in std["link_types"]}
    subject_kinds = {kind["id"] for kind in std["subject_kinds"]}
    groups = [{"deal"}, roles, subject_kinds, links]
    applicable = set().union(*groups)
    if sum(len(group) for group in groups) != len(applicable):
        found.append("a role, a kind of subject and a kind of link share a name")
    indicators = [ind["id"] for ind in std["indicators"]]
    checks = [check["id"] for ind in std["indicators"] for check in ind["checks"]]
    by_id = {check["id"]: check for ind in std["indicators"] for check in ind["checks"]}
    for name, ids in (("indicator", indicators), ("check", checks), ("slot", slots),
                      ("kind of source", [kind["id"] for kind in std["source_kinds"]])):
        found += [f"{name} {rid} appears twice" for rid in sorted(set(ids)) if ids.count(rid) > 1]

    def need(where, ok, message):
        if not ok:
            found.append(f"{where}: {message}")

    def known_checks(where, items):
        for item in items or []:
            named = by_id.get(item.get("check"))
            need(where, named, f"unknown check {item.get('check')!r}")
            need(where, not named or "is" not in item or fits(named, item["is"]),
                 f"{item.get('check')} cannot have the answer {item.get('is')!r}")
            need(where, not named or not item.get("against") or "assumption" in named,
                 f"{item.get('check')} tests no assumption, so no answer can go against it")

    for kind in std["source_kinds"]:
        need(kind["id"], kind.get("slot") is None or kind["slot"] in slots, f"unknown slot {kind.get('slot')!r}")
    for link in std["link_types"]:
        need(link["id"], set(link.get("counts_for", [])) <= subject_kinds, "counts_for names an unknown kind of subject")
    for kind in std["subject_kinds"]:
        need(kind["id"], set(kind.get("asked_only", [])) <= set(indicators), "asked_only names an unknown indicator")
    for pillar in std["pillars"]:
        need(pillar["id"], pillar.get("asked_of") in (None, "perimeter", "entity"), "asked_of is perimeter or entity")
    for ind in std["indicators"]:
        iid, own = ind["id"], {check["id"] for check in ind["checks"]}
        need(iid, ind.get("title") and ind.get("claim"), "needs a title and a claim")
        need(iid, ind.get("pillar") in {pillar["id"] for pillar in std["pillars"]}, "unknown pillar")
        need(iid, ind.get("due_by") in stages, f"unknown stage {ind.get('due_by')!r}")
        need(iid, set(ind.get("applies_to", ["?"])) <= applicable, "applies_to names something unknown")
        for key in ("applies_when", "matters_more_when", "matters_less_when"):
            known_checks(iid, ind.get(key))
        for item in ind.get("look_again_when", []):
            known_checks(iid, [item] if "check" in item else [])
            need(iid, item.get("new_source") in kinds or "check" in item, "look_again_when needs a kind of source or a check")
            need(iid, item.get("reason"), "look_again_when needs a reason")
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
            decides = ("disproved_by" in check) != ("flag_when" in check)  # exactly one of the two
            need(cid, decides == ("assumption" in check), "an assumption needs disproved_by or flag_when, and they need it")
            if "disproved_by" in check:
                need(cid, check["answer"] == "yes_no" and check["disproved_by"] in ("yes", "no"),
                     "disproved_by is yes or no, on a yes/no check")
            if "flag_when" in check:
                need(cid, flag_fits(check), "flag_when does not fit the answer the check asks for")
                need(cid, check.get("why"), "a reference point needs its reason in 'why'")
            need(cid, check.get("settled_by", "company") in ROUTES, f"settled_by is one of: {', '.join(ROUTES)}")
            need(cid, not check.get("mitigant") or ("assumption" in check and check.get("when")),
                 "a mitigant needs an assumption, and a 'when' that says which test it answers")
            for call in check.get("calls_for", []):
                need(cid, call.get("answered") is True or ("is" in call and fits(check, call["is"])),
                     "calls_for names an answer the check cannot have")
                need(cid, (set(call.get("link", ["?"])) <= links) != (call.get("kind") in subject_kinds),
                     "calls_for needs known kinds of link, or one kind of subject")
                need(cid, call.get("end", "to") in ("from", "to"), "calls_for: 'end' is from or to")
            for lead in check.get("leads_to", []):
                need(cid, lead.get("indicator") in indicators, f"leads to unknown indicator {lead.get('indicator')!r}")
                need(cid, "is" not in lead or fits(check, lead["is"]), f"leads_to names an answer the check cannot have")
    return found
