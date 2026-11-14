"""What the memory means: who holds which role, where each check stands, and what to do next.

Everything here is worked out from the memory and the standard on every run. None of it is stored.
"""
import datetime

from .standard import FLAG, TIERS, slots_of
from .store import DEAL, as_list

VERDICTS = ("challenged", "contested", "not tested", "stands")  # worst first


def roles(memory, std):
    """The roles each subject holds. A role is the end of a link that has not ended."""
    kinds = {kind["id"]: kind for kind in std["link_types"]}
    held = {}
    for link in memory["links"].values():
        if link["state"] != "ended":
            for end, role in (("from", "role_from"), ("to", "role_to")):
                if role in kinds[link["type"]]:
                    held.setdefault(link[end], set()).add(kinds[link["type"]][role])
    return held


def targets(names, memory, held):
    """Whom or what a check is asked about: the deal, holders of a role, subjects of a kind, or links of a kind."""
    found = []
    for name in names:
        found += [DEAL] if name == "deal" else []
        found += [sid for sid, subject in memory["subjects"].items() if subject["kind"] == name or name in held.get(sid, ())]
        found += [lid for lid, link in memory["links"].items() if link["type"] == name and link["state"] != "ended"]
    return list(dict.fromkeys(found))


def answers(memory, std):
    """The facts that answer each check, by check and by whom or what the answer is for.

    An answer is for the subject its fact is about, unless it says otherwise or the check is asked about the deal only.
    """
    found = {}
    for fid, fact in memory["facts"].items():
        if fact["state"] != "outdated":
            for answer in fact.get("answers", []):
                check = std["checks"].get(answer["check"], {})
                asked_about = check.get("applies_to") or std["by_id"].get(check.get("indicator"), {}).get("applies_to")
                whom = answer.get("for") or (DEAL if asked_about == ["deal"] else fact["about"])
                found.setdefault((answer["check"], whom), []).append((fid, answer["value"]))
    return found


def holds(condition, target, found, std):
    """Whether a condition on an answer holds. None while the answer is not there."""
    given = found.get((condition["check"], target)) or found.get((condition["check"], DEAL)) or []
    if not given:
        return None
    if condition.get("answered"):
        return True
    if condition.get("against"):
        return any(against(std["checks"][condition["check"]], value) for _, value in given)
    return any(value == condition["is"] or (isinstance(value, list) and condition["is"] in value) for _, value in given)


def against(check, value):
    """Whether an answer goes against the assumption a check tests."""
    if "disproved_by" in check:
        return isinstance(value, bool) and value == (check["disproved_by"] == "yes")
    return "flag_when" in check and bool(meets(check["flag_when"], value))


def meets(rule, value):
    """Whether an answer meets a reference point such as "above 20" or "is not none"."""
    limit = FLAG.match(rule)
    if limit.group(1):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        number = float(limit.group(2))
        return {"above": value > number, "below": value < number,
                "at most": value <= number, "at least": value >= number}[limit.group(1)]
    named = limit.group(4).split(" or ")
    same = any(option in named for option in (value if isinstance(value, list) else [value]))
    return not same if limit.group(3) else same


def months_since(date, today):
    """Whole months from a date written as 2026, 2026-06 or 2026-06-30. None if it cannot be read."""
    try:
        parts = [int(part) for part in str(date)[:10].split("-")]
    except ValueError:
        return None
    year, month = parts[0], parts[1] if len(parts) > 1 else 12
    return (today.year - year) * 12 + today.month - month


def answered_row(row, check, given, memory, std, today):
    """Fill in what an answer rests on: its value, the strength of the evidence, its age and what it means."""
    facts = [memory["facts"][fid] for fid, _ in given]
    values = [value for _, value in given]
    row.update(facts=[fid for fid, _ in given], value=values[0])
    if any(fact["state"] == "disputed" for fact in facts) or any(value != values[0] for value in values):
        row["state"] = "contested"
        return
    row["state"] = "answered"
    stage = next(stage for stage in std["stages"] if stage["id"] == memory["deal"]["stage"])
    kinds = {memory["sources"][fact["source"]]["kind"] for fact in facts}
    tiers = [tier for tier in TIERS if kinds & set(check.get("evidence", {}).get(tier, []))]
    row["evidence"] = tiers[-1] if tiers else "unlisted"
    if "assumption" in check:
        row["against"] = against(check, values[0])
        said = tiers[-1:] == ["stated"] or all(fact.get("said_by") == "client" for fact in facts)
        if said and not row["against"]:
            row["own_word"] = True  # a favourable answer that rests only on what someone said
    weak = "evidence" in check and TIERS.index(tiers[-1] if tiers else TIERS[0]) < TIERS.index(stage["ideal_evidence"])
    if weak and not row.get("against"):  # an answer against the claim is believed whatever it rests on
        row["flags"].append("thin")
    ages = [months_since(fact.get("as_of") or memory["sources"][fact["source"]].get("date"), today) for fact in facts]
    ages = [age for age in ages if age is not None]
    if ages and min(ages) > stage["ideal_max_age_months"]:
        row["flags"].append("old")


def assess(memory, std, today=None):
    """One row per check and per subject it is asked about, with its state."""
    today = today or datetime.date.today()
    held, found = roles(memory, std), answers(memory, std)
    rows, states = [], {}
    actions = {(cid, decision.get("about", DEAL)): did for did, decision in memory["decisions"].items()
               for cid in decision.get("covers", [])}

    def parked(off, check, target):
        """A "not now" lasts until the stage changes or a check it follows gets a new answer."""
        if off["strength"] == "not_for_this_deal":
            return True
        if off.get("stage") != memory["deal"]["stage"]:
            return False
        earlier = check.get("after", []) + [cond["check"] for cond in check.get("when", [])]
        return not any(memory["facts"][fid]["rev"] > (off.get("rev") or 0)
                       for cid in earlier for fid, _ in found.get((cid, target), []))

    def decided(cond, check, target):
        """Whether a condition is met. A condition on a check that is itself not relevant is not met."""
        result = holds(cond, target, found, std)
        same_topic = std["checks"][cond["check"]]["indicator"] == check["indicator"]
        if result is None and same_topic and state(cond["check"], target) == "not relevant":
            return False
        return result

    def state(cid, target):
        if (cid, target) in states:
            return states[cid, target]["state"]
        check = std["checks"][cid]
        ind = std["by_id"][check["indicator"]]
        row = {"check": cid, "indicator": ind["id"], "for": target, "state": "open", "flags": [],
               "due_by": check.get("due_by", ind["due_by"])}
        states[cid, target] = row
        off = check.get("off") or ind.get("off")
        given = found.get((cid, target))
        unnamed = target in memory["subjects"] and not memory["subjects"][target].get("name")  # a seat nobody holds yet
        after = check.get("after", [])
        conds = [decided(cond, check, target) for cond in check.get("when", [])]
        applies = [holds(cond, target, found, std) for cond in ind.get("applies_when", [])]
        action = actions.get((cid, target)) or actions.get((cid, DEAL))
        if action:
            row["action"] = action  # a decision that covers this check: a gap with an agreed action
        follows_dead_end = any(state(dep, target) == "not relevant" for dep in after
                               if std["checks"][dep]["indicator"] == ind["id"])
        if off and parked(off, check, target):
            row.update(state="off" if off["strength"] == "not_for_this_deal" else "parked", reason=off["reason"])
        elif given:
            answered_row(row, check, given, memory, std, today)
        elif (conds and all(cond is False for cond in conds)) or follows_dead_end:
            row["state"] = "not relevant"  # none of its conditions can hold any more
        elif (any(not (found.get((dep, target)) or found.get((dep, DEAL))) for dep in after) or unnamed
              or (conds and True not in conds) or (applies and True not in applies)):
            row["state"] = "waiting"  # for an earlier answer, for a condition, or for the seat to be filled
        return row["state"]

    for ind in std["indicators"]:
        for check in ind["checks"]:
            for target in targets(check.get("applies_to", ind["applies_to"]), memory, held):
                applies = [holds(cond, target, found, std) for cond in ind.get("applies_when", [])]
                if applies and all(cond is False for cond in applies):
                    continue  # discovery has shown that the indicator does not apply here
                state(check["id"], target)
                rows.append(states[check["id"], target])
    return rows


def claims(rows, memory, std):
    """Where each claim stands, for each subject or link it is made about. Questions do not count: tests do."""
    found, given = {}, answers(memory, std)
    for row in rows:
        check = std["checks"][row["check"]]
        if "assumption" not in check or row["state"] in ("off", "not relevant"):
            continue
        claim = found.setdefault((row["indicator"], row["for"]), {
            "indicator": row["indicator"], "for": row["for"], "tests": 0, "own_word": 0, "thin": 0, "against": [],
            "contested": [], "mitigants": {}, "actions": [], "look_again": [], "seen": 0})
        answered = row["state"] == "answered"
        claim["seen"] = max([claim["seen"], *(memory["facts"][fid]["rev"] for fid in row.get("facts", []))])
        if row.get("action") and row["action"] not in claim["actions"]:
            claim["actions"].append(row["action"])
        if check.get("mitigant"):
            if answered or row["state"] == "open":
                claim["mitigants"][row["check"]] = ("fails" if row["against"] else "holds") if answered else "not known"
        elif row["state"] == "contested":
            claim["contested"].append(row["check"])
        elif answered and row["against"]:
            claim["against"].append(row["check"])
        elif answered:
            claim["tests"] += 1
            claim["own_word"] += bool(row.get("own_word"))
            claim["thin"] += "thin" in row["flags"]
    for claim in found.values():
        claim["stands"] = ("challenged" if claim["against"] else "contested" if claim["contested"]
                           else "stands" if claim["tests"] > claim["own_word"] else "not tested")
        for item in std["by_id"][claim["indicator"]].get("look_again_when", []) if claim["seen"] else []:
            if "new_source" in item:
                later = any(source["kind"] == item["new_source"] and source["rev"] > claim["seen"]
                            and (not source.get("about") or {claim["for"], DEAL} & set(as_list(source["about"])))
                            for source in memory["sources"].values())
            else:
                facts = given.get((item["check"], claim["for"])) or given.get((item["check"], DEAL)) or []
                later = any(memory["facts"][fid]["rev"] > claim["seen"] and value == item.get("is", value)
                            for fid, value in facts)
            if later:
                claim["look_again"].append(item["reason"])
    return list(found.values())


def view(found, std):
    """For each pillar: how many claims stand where. A claim made about several subjects counts once, at its worst."""
    worst = {}
    for claim in found:
        worst[claim["indicator"]] = min(worst.get(claim["indicator"], len(VERDICTS)), VERDICTS.index(claim["stands"]))
    counts = {pillar["id"]: [0] * len(VERDICTS) for pillar in std["pillars"]}
    for indicator, place in worst.items():
        counts[std["by_id"][indicator]["pillar"]][place] += 1
    return counts


def called_for(rows, memory, std):
    """Answers that call for a link or a subject which the structure does not hold yet."""
    found = []
    for row in rows:
        asked = row["state"] == "answered" and "action" not in row  # a decision can say why nothing is needed
        for call in std["checks"][row["check"]].get("calls_for", []) if asked else []:
            value = row["value"]
            if not (call.get("answered") or value == call.get("is") or (isinstance(value, list) and call.get("is") in value)):
                continue
            link = memory["links"].get(row["for"])
            ends = {link["from"], link["to"]} if link else {row["for"]}
            sides = [call["end"]] if "end" in call and not link else ["from", "to"]  # the end the subject must be
            kinds = {sid: subject["kind"] for sid, subject in memory["subjects"].items()}
            there = (call["kind"] in kinds.values() if "kind" in call
                     else any(other["type"] in call["link"] and other["state"] != "ended"
                              and (row["for"] == DEAL or ends & {other[side] for side in sides}
                                   or ("end" not in call and kinds.get(other["to"]) == "facility"))  # support for the loan
                              for other in memory["links"].values()))
            if not there:
                wanted = f"a {call['kind']}" if "kind" in call else "a link of kind " + " or ".join(call["link"])
                found.append({"check": row["check"], "for": row["for"], "wanted": wanted})
    return found


def next_list(memory, std, rows, in_folder=()):
    """Every candidate for what to do or collect next. The assistant chooses what to show.

    `in_folder` names the data-room slots that hold a document according to the manifest.
    """
    order = {stage: place for place, stage in enumerate(std["stage_ids"])}
    unlocks = {}
    for check in std["checks"].values():
        opens = [cond["check"] for cond in check.get("when", []) + std["by_id"][check["indicator"]].get("applies_when", [])]
        for earlier in set(check.get("after", []) + opens):
            unlocks[earlier] = unlocks.get(earlier, 0) + 1
    work = [dict(row, unlocks=unlocks.get(row["check"], 0) if row["state"] == "open" else 0) for row in rows
            if (row["state"] in ("open", "contested") and "action" not in row) or (row["state"] == "answered" and row["flags"])]
    work.sort(key=lambda row: (order[row["due_by"]], -row["unlocks"]))

    slot_of = {kind["id"]: kind.get("slot") for kind in std["source_kinds"]}
    filed = {slot_of[source["kind"]] for source in memory["sources"].values() if source["state"] == "current"} | set(in_folder)
    wanted = {}
    for row in work:
        for slot in std["checks"][row["check"]].get("look_in", []):
            wanted[slot] = wanted.get(slot, 0) + 1
    documents = []
    for slot in slots_of(std):
        if slot["id"] not in filed and (slot["expected"] == "always" or slot["id"] in wanted):
            why = "always expected" if slot["expected"] == "always" else ""
            if slot["id"] in wanted:
                why = (why + ", " if why else "") + f"open checks that look here: {wanted[slot['id']]}"
            documents.append({"slot": slot["id"], "title": slot["title"], "why": why})

    filled = {field for fact in memory["facts"].values() if fact["state"] == "current" for field in fact.get("fills", [])}
    return {
        "structure": [f"{sid}: {subject['kind']} not yet named. {subject.get('note', '')}".strip()
                      for sid, subject in memory["subjects"].items() if not subject.get("name")]
                     + [f"{lid}: {link['from']} {link['type']} {link['to']} is proposed, not confirmed"
                        for lid, link in memory["links"].items() if link["state"] == "proposed"]
                     + [f"{memory['subjects'].get(call['for'], {}).get('name') or call['for'].replace(DEAL, 'The deal')}: "
                        f"the answer to {call['check']} calls for {call['wanted']}, and there is none"
                        for call in called_for(rows, memory, std)],
        "actions": [f"{did}: {decision['decision']} (owner: {decision.get('owner', 'not named')}; due: "
                    f"{decision.get('due', 'no date')}; covers {', '.join(decision['covers'])})"
                    for did, decision in memory["decisions"].items() if decision.get("covers")],
        "documents": documents,
        "checks": work,
        "questions": [dict(question, id=qid) for qid, question in memory["questions"].items() if question["state"] == "open"],
        "replaced": [f"{fid} rests on {fact['source']}, which was replaced by {memory['sources'][fact['source']].get('replaced_by')}"
                     for fid, fact in memory["facts"].items()
                     if fact["state"] == "current" and memory["sources"][fact["source"]]["state"] == "replaced"],
        "fields": [f"{system['id']}: {field['id']} {field.get('label', '')} ({field.get('gate', 'no gate')})"
                   for system in std["systems"] for field in system.get("fields", []) if field["id"] not in filled],
    }


def sheet(memory, std):
    """For each of the institution's systems: every field with its value and where the value comes from."""
    lines = []
    for system in std["systems"]:
        lines.append(f"## {system.get('title', system['id'])}")
        lines += ["", "| Field | Gate | Value | As of | Fact | Source |", "|---|---|---|---|---|---|"]
        for field in system.get("fields", []):
            facts = [(fid, fact) for fid, fact in memory["facts"].items()
                     if fact["state"] == "current" and field["id"] in fact.get("fills", [])]
            if not facts:
                lines.append(f"| {field.get('label', field['id'])} | {field.get('gate', '')} | **missing** | | | |")
            for fid, fact in facts:
                value = f"{fact['value']} {fact.get('unit', '')}".strip() if "value" in fact else fact["statement"]
                lines.append(f"| {field.get('label', field['id'])} | {field.get('gate', '')} | {value} | "
                             f"{fact.get('as_of', '')} | {fid} | {fact['source']} |")
        lines.append("")
    return lines
