"""The tool, run on the made-up deal in examples/cedar-foods."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from bankability2 import assess, files, pages, standard, store  # noqa: E402
from bankability2.__main__ import fact_lines, main, plain  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "cedar-foods")


def run(*args):
    """Run a command. Returns its exit code and what it printed."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main([str(arg) for arg in args])
    files.WRITTEN.clear()
    return code, out.getvalue()


class Deal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deal = tempfile.mkdtemp()
        run("start", cls.deal, "--name", "Cedar Foods", "--institution", os.path.join(ROOT, "examples", "institution.example.json"))
        shutil.copytree(os.path.join(EXAMPLE, "documents"), os.path.join(cls.deal, "Inbox"))
        run("file", cls.deal, os.path.join(EXAMPLE, "changes", "0-filing.json"))
        for name in ("1-teaser", "2-annual-report", "3-call"):
            run("add", cls.deal, os.path.join(EXAMPLE, "changes", name + ".json"))
        run("adjust", cls.deal, os.path.join(EXAMPLE, "changes", "4-adjust.json"))
        run("pages", cls.deal)
        cls.page = os.path.join(cls.deal, "Internal", "wiki", "parties", "cedar-foods-ltd.md")
        shutil.copytree(os.path.join(EXAMPLE, "wiki"), os.path.join(cls.deal, "Internal", "wiki"), dirs_exist_ok=True)
        run("pages", cls.deal)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.deal)

    def memory(self):
        return files.read_json(self.deal, files.MEMORY)

    def rows(self, memory=None):
        found = assess.assess(memory or self.memory(), standard.effective(self.deal))
        return {(row["check"], row["for"]): row for row in found}

    def copy(self):
        """A copy of the deal folder, for a test that records something."""
        path = os.path.join(tempfile.mkdtemp(), "deal")
        shutil.copytree(self.deal, path)
        self.addCleanup(shutil.rmtree, os.path.dirname(path))
        return path

    def handed(self, data):
        """A JSON file to hand to a command."""
        path = os.path.join(self.deal, "handed.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_documents_are_filed_flat_and_indexed(self):
        manifest = files.read_json(self.deal, files.MANIFEST)
        self.assertEqual([doc["slot"] for doc in manifest["documents"]], ["01.01.a", "03.01.a"])
        self.assertEqual(sorted(os.listdir(os.path.join(self.deal, "Client folder"))), [  # no data-room folders on disk
            "Cedar Foods annual report 2025 extract.md", "Cedar Foods teaser.md", "index.md", "manifest.json"])
        self.assertIsNotNone(files.fingerprint(self.deal, "Internal/sources/2026-11-12 CFO call.md"))
        self.assertEqual(self.memory()["sources"]["S-002"]["fingerprint"], manifest["documents"][1]["fingerprint"])
        index = files.read(self.deal, "Client folder/index.md")
        self.assertIn("### 03.01 Historical Financials\n\n- [Annual report 2025](Cedar%20Foods%20annual%20report%202025%20extract.md): "
                      "Audited financial statements, Cedar Foods Ltd, 2025. Slot 03.01.a", index)
        self.assertIn("## Always expected and not here yet\n\n- 01.01.b Company / Project Description", index)

    def test_a_document_is_never_overwritten_and_an_extract_goes_with_its_original(self):
        deal = self.copy()
        for name in ("Cedar Foods teaser.md", "Scan.pdf", "Scan.txt"):
            with open(os.path.join(deal, "Inbox", name), "w", encoding="utf-8") as f:
                f.write("another document")
        code, said = run("file", deal, self.handed([
            {"file": "Inbox/Cedar Foods teaser.md", "kind": "executive_summary"},
            {"file": "Inbox/Scan.pdf", "kind": "business_plan", "extract": "Inbox/Scan.txt"}]))
        self.assertEqual(code, 1)
        self.assertIn("Not filed. The tool never overwrites a file", said)
        self.assertIn("Inbox/Cedar Foods teaser.md: Client folder/Cedar Foods teaser.md already exists", said)
        filed = files.read_json(deal, files.MANIFEST)["documents"][-1]
        self.assertEqual((filed["path"], filed["extract"]), ("Client folder/Scan.pdf", "Internal/sources/extracts/Scan.txt"))
        self.assertIsNotNone(files.fingerprint(deal, "Internal/sources/extracts/Scan.txt"))
        self.assertIn("[Scan.pdf](Scan.pdf): Business plan. Slot 01.01.b", files.read(deal, "Client folder/index.md"))
        self.assertEqual(run("add", deal, self.handed({"sources": [  # a source keeps the place of its extract
            {"title": "Scan", "kind": "business_plan", "where": filed["path"], "extract": filed["extract"]}]}))[0], 0)
        run("add", deal, self.handed({"sources": [{"id": "S-001", "where": filed["path"]}]}))  # the original came later
        self.assertEqual(files.read_json(deal, files.MEMORY)["sources"]["S-001"]["fingerprint"], files.fingerprint(deal, filed["path"]))

    def test_an_older_folder_is_moved_by_upgrade(self):
        deal = self.copy()
        os.makedirs(os.path.join(deal, "Internal", "memory"))
        os.replace(os.path.join(deal, files.MEMORY), os.path.join(deal, files.OLD_MEMORY))
        self.assertIn("Move it with: upgrade", run("status", deal)[1])
        wiki = os.path.join(deal, "Internal", "wiki")  # and its pages are on the shelves of an earlier version
        os.makedirs(os.path.join(wiki, "deal"))
        os.replace(os.path.join(wiki, "assets", "second-uht-line.md"), os.path.join(wiki, "deal", "second-uht-line.md"))
        os.replace(os.path.join(wiki, "opportunity", "opportunity.md"), os.path.join(wiki, "deal", "deal.md"))
        with open(os.path.join(wiki, "deal", "deal.md"), "a", encoding="utf-8") as f:
            f.write("\nSee [the line](second-uht-line.md) [F-008].\n")
        said = run("upgrade", deal)[1]
        self.assertIn("Moved the record to Internal/record/record.json", said)
        self.assertIn("Moved the pages of the wiki to the shelves this version uses", said)
        self.assertIn("See [the line](../assets/second-uht-line.md) [F-008].", files.read(deal, "Internal/wiki/opportunity/opportunity.md"))
        self.assertIn("(opportunity/opportunity.md)", files.read(deal, "Internal/wiki/index.md"))  # the contents page is written again
        self.assertEqual(run("check", deal)[1].strip(), "No problems found.")

    def test_roles_come_from_links(self):
        held = assess.roles(self.memory(), standard.effective(self.deal))
        self.assertEqual(held, {"P-001": {"borrower"}, "P-002": {"guarantor"}, "P-003": {"customer"}, "J-001": {"financed_project"}})

    def test_who_is_asked(self):
        memory, std = self.memory(), standard.effective(self.deal)
        memory["subjects"].update({"G-001": {"kind": "group", "name": "Cedar Group"}, "N-001": {"kind": "person", "name": "A. Owner"}})
        links = (("P-001", "member_of", "G-001"), ("L-001", "relies_on", "G-001"), ("N-001", "owns", "P-001"),
                 ("N-001", "guarantees", "P-001"))  # the last is a guarantee of existing debt, not of the loan under review
        for n, (start, kind, end) in enumerate(links):
            memory["links"][f"R-10{n}"] = {"from": start, "type": kind, "to": end, "state": "confirmed"}
        self.assertEqual(assess.roles(memory, std)["N-001"], {"shareholder"})
        rows = self.rows(memory)
        asked = {name: {target for check, target in rows if check == name} for name in
                 ("OBS_REV_004", "OBS_BOARD_001", "OBS_SANC_001", "OBS_BO_002", "OBS_GUARANTEE_KIND_001")}
        self.assertEqual(asked["OBS_REV_004"], {"G-001"})  # the business is examined once, on the group
        self.assertEqual(asked["OBS_BOARD_001"], {"P-001"})  # the board is that of the company, not of the group
        memory["links"]["R-001"]["state"] = "ended"  # a member of the group is asked as a legal entity, borrower or not
        self.assertIn(("OBS_BOARD_001", "P-001"), self.rows(memory))
        memory["links"]["R-001"]["state"] = "confirmed"
        self.assertIn("N-001", asked["OBS_SANC_001"])  # a person is asked what fits a person
        self.assertNotIn("N-001", asked["OBS_BO_002"])  # and not who owns it
        self.assertEqual(asked["OBS_GUARANTEE_KIND_001"], {"R-002"})  # only the guarantee of the loan is examined
        self.assertIn("F-008 answers OBS_REV_001 for P-001, which is not asked that check", assess.stray(memory, std, rows.values()))
        memory["subjects"]["A-001"] = {"kind": "asset", "name": "Nakuru plant"}
        memory["links"]["R-200"] = {"from": "P-001", "type": "owns", "to": "A-001", "state": "confirmed"}
        self.assertNotIn("shareholder", assess.roles(memory, std)["P-001"])  # owning a plant makes nobody a shareholder
        memory["subjects"]["A-002"] = {"kind": "asset", "name": "Filling line 1"}
        memory["links"]["R-201"] = {"from": "A-002", "type": "part_of", "to": "A-001", "state": "confirmed"}
        self.assertEqual({target for check, target in self.rows(memory) if check == "OBS_ASSET_007"}, {"A-001"})  # not its part
        memory["subjects"]["N-001"]["state"] = "ended"  # a subject that has ended holds no role and is asked nothing
        self.assertNotIn("N-001", assess.roles(memory, std))
        self.assertNotIn("N-001", {target for _, target in self.rows(memory)})
        std["link_types"][0]["counts_for"], std["subject_kinds"][0]["asked_only"] = ["loan"], ["CAS_NOTHING_001"]
        self.assertEqual(len(standard.problems(std)), 2)  # the build refuses a kind or an indicator that does not exist

    def test_add_says_what_it_made_and_an_answer_can_be_withdrawn(self):
        deal = self.copy()
        answer = {"check": "OBS_FX_002", "value": 40}  # asked only when there is revenue in a foreign currency
        fact = {"ref": "hedge", "about": "P-001", "statement": "A fact with an answer nobody asked for.", "source": "S-003"}
        worked = {"about": "P-001", "statement": "A figure worked out from (@hedge) and F-005.", "source": "S-003"}
        _, said = run("add", deal, self.handed({"facts": [dict(fact, answers=[answer]), worked]}))
        self.assertIn("@hedge -> F-020", said)
        self.assertEqual(files.read_json(deal, files.MEMORY)["facts"]["F-021"]["statement"], "A figure worked out from (F-020) and F-005.")
        self.assertIn("- F-021: names F-005, which is outdated (replaced by F-008)", run("check", deal)[1])
        self.assertIn("Note: F-020 answers OBS_FX_002 for P-001, where that check is not relevant.", said)
        run("add", deal, self.handed({"facts": [{"id": "F-020", "answers": []}]}))
        memory = files.read_json(deal, files.MEMORY)
        self.assertEqual((memory["facts"]["F-020"]["answers"], memory["log"][-1]["changed"]), ([], {"F-020": {"answers": [answer]}}))
        self.assertIn("Pages that cite a record this set changed, to read again: Internal/wiki/opportunity/opportunity.md",
                      run("add", deal, self.handed({"facts": [{"id": "F-008", "place": "page 12"}]}))[1])
        said = run("add", deal, self.handed({"facts": [{"id": "F-014", "answers": [], "quote": "Bluegate pays within 54 days."}]}))[1]
        self.assertTrue("-1 answered" in said and "+1 open" in said)  # what the set did to the checks
        self.assertIn("- F-014: its quotation is not in the text of S-003", run("check", deal)[1])
        self.assertEqual(plain("| **Revenue** | 4,060 |"), "revenue 4,060")  # compared without marks, bars or capitals
        run("add", deal, self.handed({"decisions": [{"decision": "Kept.", "reason": "Small.", "about": "P-003", "rests_on": ["F-014"]}]}))
        run("pages", deal)  # a record that no page cites is in the view all the same, unless it is history
        self.assertIn('"D-003"', files.read(deal, "Internal/wiki/wiki.html"))

    def test_upgrade_brings_the_standard_of_the_tool(self):
        deal, newer = self.copy(), files.packaged_standard()
        before, newer["version"] = newer["version"], "9.9.9"
        newer["indicators"] = [ind for ind in newer["indicators"] if ind["id"] != "CAS_COST_001"]
        with mock.patch.object(files, "packaged_standard", return_value=newer):
            _, said = run("upgrade", deal)
        self.assertIn("- F-012: OBS_COST_004", said)  # the answer stays in the fact and no longer counts
        self.assertIn("Checks that are gone: OBS_COST_001 (CAS_COST_001)", said)  # and what the new standard changed is listed
        memory = files.read_json(deal, files.MEMORY)
        self.assertEqual((memory["deal"]["standard"], memory["log"][-1]["changed"]), ("9.9.9", {"DEAL": {"standard": before}}))
        self.assertEqual(store.verify(memory), [])

    def test_the_views(self):
        _, said = run("status", self.deal, "--for", "L-001", "--all")
        self.assertIn("- L-001 EUR 12m senior loan: facility, the loan under review", said)
        self.assertIn("- R-002 the party not yet named (P-002) guarantees EUR 12m senior loan (proposed)", said)
        self.assertNotIn("Bluegate", said)  # only the loan and the links that touch it
        self.assertIn("[DEAL_MILK_PRICE_001: yes/no]", run("status", self.deal, "--for", "P-001", "--all")[1])
        claims = run("show", self.deal, "claims")[1]
        self.assertIn("- Key customer (Cedar Foods Ltd sells_to Bluegate Supermarkets): not tested; tests answered 1 of", claims)
        self.assertIn("answers on someone's own word 1 [CAS_OFFTAKER_CREDIT_001]", claims)
        self.assertEqual(run("show", self.deal, "facts", "R-003")[1].strip(), "- F-014 about R-003: The CFO said Bluegate pays "
                         "within 45 days. (S-003; as of 2026-11-12; client; answers OBS_OFFTAKER_004: yes)")
        self.assertIn("- F-005 (outdated) about", run("show", self.deal, "facts", "F-005", "S-002")[1])  # named, so it shows
        self.assertNotIn("F-005", run("show", self.deal, "facts")[1])
        long = {"facts": {"F-1": {"state": "current", "about": "P-001", "statement": "x" * 400, "source": "S-001"}}}
        self.assertIn("x" * 300 + " ...", fact_lines(long, ["P-001"])[0])  # a long statement is cut in a list
        self.assertIn("x" * 400, fact_lines(long, ["F-1"])[0])  # and given in full when the fact is named
        self.assertIn('quote: "Revenue was KES 4,060m (2024: KES 3,720m)."', run("show", self.deal, "facts", "F-008")[1])
        self.assertIn("- OBS_REV_001: ", run("show", self.deal, "CAS_REVENUE_001")[1])  # an indicator lists its checks
        self.assertIn("- OBS_GROUP_011:", run("show", self.deal, "own account")[1])  # a search also finds a check
        self.assertIn("- D-002: Cedar is to propose", run("show", self.deal, "decisions")[1])  # every record of one kind
        self.assertEqual(len(run("show", self.deal, "sample")[1].splitlines()), 10)  # ten facts to compare with their pages
        self.assertIn("The deal folder comes right after the command", run("show", "facts", self.deal)[1])
        kinds = run("show", self.deal, "kinds")[1]
        self.assertIn("- call: Call or meeting. Folder: Internal/sources", kinds)
        self.assertIn("Gives the role guarantor to its 'from' end. It counts only when it points at a facility.", kinds)

    def test_a_closed_pipe_is_not_a_refusal(self):
        class Closed(io.StringIO):
            def write(self, text):
                raise BrokenPipeError

        with contextlib.redirect_stdout(Closed()):
            self.assertEqual(main(["show", self.deal, "log"]), 0)

    def test_a_replaced_fact_stays(self):
        fact = self.memory()["facts"]["F-005"]
        self.assertEqual((fact["state"], fact["replaced_by"]), ("outdated", "F-008"))

    def test_where_checks_stand(self):
        rows = self.rows()
        major = rows["OBS_BUYER_CONC_001", "P-001"]  # a question: it opens the topic and tests nothing
        self.assertEqual((major["state"], major["evidence"], "against" in major), ("answered", "best", False))
        margin = rows["OBS_COST_004", "P-001"]  # a test: the CFO said on a call that the margin fell
        self.assertEqual((margin["against"], margin["evidence"]), (True, "stated"))
        self.assertEqual(margin["flags"], [])  # an answer against the claim is believed whatever it rests on
        self.assertEqual(rows["OBS_INPUT_001", "P-001"]["flags"], ["thin"])  # said on a call, and the stage is past screening
        self.assertEqual(rows["OBS_FX_002", "P-001"]["state"], "not relevant")  # asked only when there is foreign revenue
        self.assertEqual(rows["OBS_REV_004", "P-001"]["state"], "open")
        self.assertEqual(rows["OBS_DEBT_001", "P-002"]["state"], "waiting")  # the guarantor is not named yet
        paid = rows["OBS_OFFTAKER_004", "R-003"]  # a check on a link, answered in the customer's favour by the seller
        self.assertEqual((paid["state"], paid["against"], paid.get("own_word")), ("answered", False, True))
        self.assertEqual(rows["DEAL_MILK_PRICE_001", "P-001"]["state"], "open")  # the check this deal added
        self.assertNotIn(("OBS_FIC_001", "P-001"), rows)  # checks for banks do not apply
        self.assertIn(("OBS_AGRI_001", "P-001"), rows)  # checks for agribusiness do, because discovery said so
        self.assertEqual(rows["OBS_HEDGE_003", "P-001"]["action"], "D-002")  # a gap with an agreed action
        memory = self.memory()  # a decision without an owner or a date settles a check, only for the subject it is about
        memory["decisions"]["D-900"] = {"decision": "Not examined.", "reason": "It carries little.", "covers": ["OBS_REV_004"]}
        self.assertEqual(self.rows(memory)["OBS_REV_004", "P-001"], rows["OBS_REV_004", "P-001"])  # about the deal: no effect here
        self.assertIn("D-900 covers OBS_REV_004 for DEAL, which is not asked that check: it is asked of P-001",  # and the tool says so
                      assess.stray(memory, standard.effective(self.deal), self.rows(memory).values()))
        memory["decisions"]["D-900"]["about"] = "P-001"
        self.assertEqual(self.rows(memory)["OBS_REV_004", "P-001"]["state"], "off")
        memory["decisions"]["D-900"]["covers"] = ["OBS_SANC_001"]  # a check the institution has locked is not settled this way
        self.assertEqual(self.rows(memory)["OBS_SANC_001", "P-001"], rows["OBS_SANC_001", "P-001"])
        memory = self.memory()  # a fact of a later date answers, and does not contest the earlier one
        memory["facts"]["F-900"] = dict(memory["facts"]["F-012"], as_of="2027-01-01", answers=[{"check": "OBS_COST_004", "value": False}])
        later = self.rows(memory)["OBS_COST_004", "P-001"]
        self.assertEqual((margin["value"], later["state"], later["value"]), (True, "answered", False))
        memory = self.memory()
        memory["facts"]["F-007"]["state"] = "outdated"  # without it no currency test goes against the claim
        self.assertEqual(self.rows(memory)["OBS_HEDGE_003", "P-001"]["state"], "waiting")
        memory["facts"]["F-003"]["state"] = "outdated"  # without the kind of business, its checks wait for discovery
        self.assertEqual(self.rows(memory)["OBS_REV_004", "P-001"]["state"], "waiting")

    def test_where_claims_stand(self):
        memory, std = self.memory(), standard.effective(self.deal)
        rows = assess.assess(memory, std)
        found = {(claim["indicator"], claim["for"]): claim for claim in assess.claims(rows, memory, std)}
        currency = found["CAS_FX_001", "P-001"]
        self.assertEqual((currency["stands"], currency["against"], currency["actions"]), ("challenged", ["OBS_FX_008"], ["D-002"]))
        self.assertEqual(currency["mitigants"]["OBS_HEDGE_003"], "not known")
        self.assertEqual(found["CAS_OFFTAKER_CREDIT_001", "R-003"]["stands"], "not tested")  # it rests on the seller's word
        self.assertEqual(assess.view(found.values(), std)["liquidity"][0], 1)  # one challenged claim in that pillar
        memory["facts"]["F-014"].update(source="S-002", said_by="document")  # borne out by a document, with other tests open
        later = {(claim["indicator"], claim["for"]): claim for claim in assess.claims(assess.assess(memory, std), memory, std)}
        self.assertEqual(later["CAS_OFFTAKER_CREDIT_001", "R-003"]["stands"], "stands so far")
        memory["facts"]["F-009"]["state"] = "disputed"  # two documents disagree on a question behind the claim
        later = {(claim["indicator"], claim["for"]): claim for claim in assess.claims(assess.assess(memory, std), memory, std)}
        self.assertEqual(later["CAS_OFFTAKER_CREDIT_001", "R-003"]["stands"], "contested")
        for flags, stands in (([], "stands"), (["thin"], "stands so far")):  # it stands when no test is left to strengthen
            every = [dict(row, state="answered", against=False, flags=flags, own_word=False, evidence="best")
                     for row in rows if row["for"] == "R-003"]
            self.assertEqual({c["indicator"]: c["stands"] for c in assess.claims(every, memory, std)}["CAS_OFFTAKER_CREDIT_001"], stands)
        wanted = {(call["check"], call["wanted"]) for call in assess.called_for(rows, memory, std)}
        self.assertEqual(wanted, {("OBS_INPUT_001", "a link of kind supplies_to"), ("OBS_DEBT_001", "a link of kind lends_to")})
        memory["subjects"]["J-001"]["kind"] = "asset"  # without a project, the spending plan calls for one
        self.assertIn(("OBS_CAPEX_PLAN_001", "a project"), {(c["check"], c["wanted"]) for c in assess.called_for(rows, memory, std)})

    def test_not_now_lasts_until_the_stage_changes(self):
        memory = self.memory()
        self.assertEqual(self.rows(memory)["OBS_INS_001", "P-001"]["state"], "parked")
        memory["deal"]["stage"] = "diligence"
        self.assertEqual(self.rows(memory)["OBS_INS_001", "P-001"]["state"], "open")

    def test_a_locked_check_cannot_be_switched_off(self):
        code, said = run("adjust", self.deal, self.handed(
            {"do": "switch_off", "target": "OBS_SANC_001", "strength": "not_for_this_deal", "reason": "Not needed."}))
        self.assertEqual(code, 1)
        self.assertIn("locked by the institution", said)
        code, said = run("adjust", self.deal, self.handed(  # nor through its indicator
            {"do": "switch_off", "target": "CAS_SANCTIONS_001", "strength": "not_now", "reason": "Not needed."}))
        self.assertIn("locked by the institution", said)

    def test_a_malformed_change_is_refused_whole(self):
        before = store.revision(self.memory())
        code, said = run("add", self.deal, self.handed({
            "sources": [{"title": "A good source", "kind": "call"}],
            "facts": [{"about": "P-001", "statement": "A fact without a real source.", "source": "S-999"}]}))
        self.assertEqual(code, 1)
        self.assertIn("Nothing was recorded", said)
        self.assertEqual(store.revision(self.memory()), before)

    def test_the_same_change_is_not_applied_twice(self):
        before = store.revision(self.memory())
        _, said = run("add", self.deal, os.path.join(EXAMPLE, "changes", "1-teaser.json"))
        self.assertIn("Already recorded", said)
        _, said = run("add", self.deal, self.handed({"subjects": [{"kind": "party", "name": "A trial"}]}), "--try")
        self.assertIn("A trial run: nothing was written. It would be recorded as revision", said)
        self.assertEqual(store.revision(self.memory()), before)

    def test_the_log_shows_a_change_made_outside_the_tool(self):
        memory = self.memory()
        self.assertEqual(store.verify(memory), [])
        memory["facts"]["F-008"]["value"] = 9999
        self.assertEqual(len(store.verify(memory)), 1)

    def test_the_tool_does_not_write_outside_the_deal_folder(self):
        with self.assertRaises(files.Refused):
            files.write(self.deal, "../outside.txt", "no")

    def test_the_page_is_filled_in_and_checked(self):
        with open(self.page, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("| Revenue | 4060 KES m | 2025-12-31 | F-008 |", text)
        self.assertIn("- S-002 Annual report 2025", text)
        damaged = text.replace("<!-- tool:end -->", "", 1)  # a page that lost the end marker of its first part
        self.assertIn("**Debt.** Borrowings were KES 1,300m", pages.fill(damaged, "glance", ["new"]))
        self.assertEqual(run("check", self.deal)[1].strip(), "No problems found.")

    def test_check_reads_paragraph_by_paragraph(self):
        deal = self.copy()

        def found(text, path="Internal/wiki/topics/revenue.md"):
            os.makedirs(os.path.dirname(os.path.join(deal, path)), exist_ok=True)
            with open(os.path.join(deal, path), "w", encoding="utf-8") as f:
                f.write("---\ntitle: Revenue\nabout: CAS_REVENUE_001\n---\n\n## What we know\n\n" + text)
            lone = "Internal/wiki/topics/revenue.md: no other page links to it"  # true of this page in every case below
            said = pages.problems(deal, files.read_json(deal, files.MEMORY))
            self.assertIn(lone, said)
            return [line for line in said if line != lone]

        # A number must be in a record cited in its own paragraph: here the second one cites the fact on borrowings.
        self.assertEqual(found("Revenue was KES 4,060m in 2025 [F-008].\n\n- Borrowings were KES 4,060m [F-011].\n"), [
            'Internal/wiki/topics/revenue.md: "Borrowings were KES 4,060m [F-011]. ..." has 4060, '
            'which no record cited in that paragraph holds'])
        # A fact that was replaced may be cited after the word that marks it. Without the word it is reported.
        self.assertEqual(found("Revenue was KES 4,060m in 2025 [F-008]. Outdated: the teaser gave about KES 4.1bn [F-005].\n"), [])
        self.assertIn("cites F-005, which is outdated (replaced by F-008)", found("Revenue was about KES 4.1bn in 2025 [F-005].\n")[0])
        self.assertEqual(len(found("Revenue was KES 4,060m in 2025 [F-008]. Disputed: the teaser gave KES 4.1bn [F-005].\n")), 1)  # the wrong word
        self.assertEqual(found("Revenue was KES 4,060m [F-008]. Disputed: another figure. Outdated: the teaser gave KES 4.1bn [F-005].\n"), [])
        self.assertEqual(found("**Earlier.** Outdated: the teaser gave about KES 4.1bn [F-005].\n"), [])  # after a lead-in in bold
        # The head row of a table names the columns and is not read. A figure cites in its own row.
        self.assertEqual(found("| | 2025 |\n|---|---|\n| Revenue | KES 4,060m [F-008] |\n"), [])
        # A link to a page that is not there is reported. Working notes say how to work, and need not cite.
        self.assertIn("links to ../assets/plant.md, which is not there", found("See [the plant](../assets/plant.md) [F-008].\n")[0])
        self.assertEqual(found("Revenue was KES 4,060m in 2025 [F-008].\n"), [])
        self.assertEqual(found("The analyst asked on 12/11/2026 for 150 words on the plant.\n", "Internal/wiki/work/working-notes.md"), [])
        run("add", deal, self.handed({"deal": {"avoid": ["cheap loan"]}}))  # a wording the analyst asked to keep out
        self.assertIn("holds a wording to avoid: cheap loan", found("The loan is cheap for a company with revenue of KES 4,060m [F-008].\n")[0])
        self.assertEqual(found("The loan is in euros [F-008]. Milk is cheap.\n"), [])  # the words are not in one sentence
        # The drafts are read the same way.
        self.assertIn("Internal/outputs/fp.md", found("Revenue was KES 5,555m [F-008].\n", "Internal/outputs/fp.md")[0])
        self.assertEqual(found("Revenue was KES 5,555m [F-008].\n", "Internal/outputs/fp.md"),  # a draft that went out is left alone
                         found("Revenue was KES 6,666m [F-008].\n", "Internal/outputs/sent/fp-v1.md"))

    def test_few_pages_and_a_view_for_a_browser(self):
        wiki = os.path.join(self.deal, "Internal", "wiki")  # a page for the deal, the borrower and the project only
        self.assertEqual([sorted(os.listdir(os.path.join(wiki, shelf))) for shelf in ("opportunity", "assets", "parties")],
                         [["opportunity.md"], ["second-uht-line.md"], ["cedar-foods-ltd.md"]])
        contents = files.read(self.deal, "Internal/wiki/index.md")
        self.assertIn("- [Cedar Foods Ltd](parties/cedar-foods-ltd.md): Cedar Foods Ltd is a dairy processor in Nakuru, Kenya, "
                      "and the borrower of the proposed EUR 12m loan.\n", contents)
        self.assertIn("- P-003 Bluegate Supermarkets: party, customer", contents)
        self.assertEqual(pages.lead("# Blue\n\nBlue Co. Ltd sells milk under Decree No. 12 in Thika Town [F-001]. It is small.\n"),
                         "Blue Co. Ltd sells milk under Decree No. 12 in Thika Town.")  # cut at the sentence, not at an abbreviation
        glance = files.read(self.deal, "Internal/wiki/opportunity/opportunity.md")
        self.assertIn("- P-001 [Cedar Foods Ltd](../parties/cedar-foods-ltd.md): party, borrower. Borrows EUR 12m senior loan "
                      "(R-001); sells to Bluegate Supermarkets (R-003).", glance)
        self.assertIn("**Challenged:** Currency risk ([Cedar Foods Ltd](../parties/cedar-foods-ltd.md)). The answers go against: "
                      "No more than a small part", glance)
        self.assertIn("(OBS_FX_008). Mitigants: 5 not known. Decision: D-002.", glance)
        self.assertTrue(contents.rstrip().endswith("what is answered, what is open and what settles it."))  # the checks come last
        checks = files.read(self.deal, "Internal/wiki/checks.md")
        self.assertIn("| answered | Does the party earn any of its revenue in a foreign currency, or at prices that are set in one? "
                      "`OBS_FX_001` | [Cedar Foods Ltd](parties/cedar-foods-ltd.md) | no [F-010] |  | Screening |", checks)
        self.assertIn("until `OBS_FX_007` is answered: Does the party pay any of its costs in a foreign currency", checks)
        template, view = files.packaged("wiki.html"), files.read(self.deal, "Internal/wiki/wiki.html")
        loads = [mark for mark in ("://", "<link", " src=", "@import", "url(") if mark in template]
        self.assertEqual(loads, [])  # it loads nothing: no script, style, font or picture from elsewhere
        with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as f:
            self.assertIn('"wiki.html"', f.read())  # an installed copy of the tool needs the template too
        data = json.loads(view.split('<script id="data" type="application/json">')[1].split("</script>")[0])
        self.assertEqual(sorted(data["pages"]),  # every page, the contents page, the sources and the index of the documents
                         ["../../Client folder/index.md", "assets/second-uht-line.md", "checks.md", "index.md", "opportunity/opportunity.md",
                          "parties/cedar-foods-ltd.md", "sources.md"])
        self.assertIn("- S-002 Annual report 2025: audited_annual_report, 2026-03-28, read: part, facts: 4. [Original](",
                      data["pages"]["sources.md"])
        self.assertEqual((data["facts"]["F-008"]["value"], data["sources"]["S-002"]["where"]),
                         (4060, "Client folder/Cedar Foods annual report 2025 extract.md"))
        self.assertNotIn("F-005", data["facts"])  # a fact that was replaced is in the view only where a page cites it

    def test_a_page_can_describe_several_subjects(self):
        deal = self.copy()
        os.makedirs(os.path.join(deal, "Internal", "wiki", "topics"))
        with open(os.path.join(deal, "Internal", "wiki", "topics", "customers.md"), "w", encoding="utf-8") as f:
            f.write("---\ntitle: Customers\nabout: CAS_REVENUE_001, P-003\n---\n\nBluegate buys 31% of revenue [F-009].\n")
        run("pages", deal)
        self.assertNotIn("- P-003 Bluegate", files.read(deal, "Internal/wiki/index.md"))  # no longer without a page
        self.assertIn("sells to [Bluegate Supermarkets](../topics/customers.md)",
                      files.read(deal, "Internal/wiki/parties/cedar-foods-ltd.md"))
        os.remove(os.path.join(deal, "Internal", "wiki", "parties", "cedar-foods-ltd.md"))
        with open(os.path.join(deal, "Internal", "wiki", "topics", "history.md"), "w", encoding="utf-8") as f:
            f.write("---\ntitle: History\nabout: P-001\n---\n\nCedar Foods was founded in Nakuru [F-001].\n")
        self.assertIn("parties/cedar-foods-ltd.md", run("pages", deal)[1])  # a page about a topic is nobody's own page:
        self.assertIn("[Cedar Foods Ltd](../parties/cedar-foods-ltd.md)", files.read(deal, "Internal/wiki/opportunity/opportunity.md"))  # made again
        os.remove(os.path.join(deal, "Internal", "wiki", "parties", "cedar-foods-ltd.md"))
        line = files.read(deal, "Internal/wiki/assets/second-uht-line.md").replace("about: J-001", "about: J-001, P-001")
        files.write(deal, "Internal/wiki/assets/second-uht-line.md", line)
        self.assertNotIn("Created", run("pages", deal)[1])  # a page about subjects that names it second is its page

    def test_the_entry_sheet_shows_values_and_gaps(self):
        sheet = "\n".join(assess.sheet(self.memory(), standard.effective(self.deal)))
        self.assertIn("| Revenue, last financial year | CIP | 4060 KES m | 2025-12-31 | F-008 | S-002 |", sheet)
        self.assertIn("| Sector code | CIP | **missing** |", sheet)


if __name__ == "__main__":
    unittest.main()
