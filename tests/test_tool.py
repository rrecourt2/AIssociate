"""The tool, run on the made-up deal in examples/cedar-foods."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from bankability2 import assess, files, pages, standard, store  # noqa: E402
from bankability2.__main__ import main  # noqa: E402

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
        shutil.copy(os.path.join(EXAMPLE, "wiki", "cedar-foods-ltd.md"), cls.page)
        run("pages", cls.deal)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.deal)

    def memory(self):
        return files.read_json(self.deal, files.MEMORY)

    def rows(self, memory=None):
        found = assess.assess(memory or self.memory(), standard.effective(self.deal))
        return {(row["check"], row["for"]): row for row in found}

    def handed(self, data):
        """A JSON file to hand to a command."""
        path = os.path.join(self.deal, "handed.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_documents_are_filed_and_listed(self):
        manifest = files.read_json(self.deal, files.MANIFEST)
        self.assertEqual([doc["slot"] for doc in manifest["documents"]], ["01.01.a", "03.01.a"])
        self.assertIsNotNone(files.fingerprint(self.deal, "Internal/sources/2026-11-12 CFO call.md"))
        self.assertEqual(self.memory()["sources"]["S-002"]["fingerprint"], manifest["documents"][1]["fingerprint"])

    def test_roles_come_from_links(self):
        held = assess.roles(self.memory(), standard.effective(self.deal))
        self.assertEqual(held, {"P-001": {"borrower"}, "P-002": {"guarantor"}, "P-003": {"customer"}})

    def test_a_replaced_fact_stays(self):
        fact = self.memory()["facts"]["F-005"]
        self.assertEqual((fact["state"], fact["replaced_by"]), ("outdated", "F-008"))

    def test_where_checks_stand(self):
        rows = self.rows()
        major = rows["OBS_BUYER_CONC_001", "P-001"]
        self.assertEqual((major["state"], major["assumption"], major["evidence"]), ("answered", "disproved", "best"))
        self.assertEqual(rows["OBS_INPUT_001", "P-001"]["flags"], ["thin"])  # said on a call, and the stage is past screening
        self.assertEqual(rows["OBS_FX_002", "P-001"]["state"], "not relevant")  # asked only when there is foreign revenue
        self.assertEqual(rows["OBS_REV_002", "P-001"]["state"], "open")
        self.assertEqual(rows["OBS_REV_001", "P-002"]["state"], "waiting")  # the guarantor is not named yet
        self.assertEqual(rows["OBS_OFFTAKER_004", "R-003"]["state"], "answered")  # a check on a link
        self.assertEqual(rows["DEAL_MILK_PRICE_001", "P-001"]["state"], "open")  # the check this deal added
        self.assertNotIn(("OBS_FIC_001", "P-001"), rows)  # checks for banks do not apply

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
        self.assertEqual(run("check", self.deal)[1].strip(), "No problems found.")
        invented = os.path.join(os.path.dirname(self.page), "invented.md")
        with open(invented, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Invented\nabout: P-001\n---\n\n## What we know\n\nRevenue was KES 5,555m [F-008].\n")
        self.assertIn("5555", " ".join(pages.problems(self.deal, self.memory())))
        os.remove(invented)

    def test_the_entry_sheet_shows_values_and_gaps(self):
        sheet = "\n".join(assess.sheet(self.memory(), standard.effective(self.deal)))
        self.assertIn("| Revenue, last financial year | CIP | 4060 KES m | 2025-12-31 | F-008 | S-002 |", sheet)
        self.assertIn("| Sector code | CIP | **missing** |", sheet)


if __name__ == "__main__":
    unittest.main()
