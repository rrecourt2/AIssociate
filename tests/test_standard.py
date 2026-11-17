"""The standard is sound, and the file the tool reads is built from it."""
import json
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "standard"))

try:
    import build
except ImportError:  # PyYAML is not installed
    build = None


@unittest.skipIf(build is None, "needs PyYAML")
class Standard(unittest.TestCase):
    def test_every_reference_points_at_something(self):
        self.assertEqual(build.problems(build.load()), [])

    def test_every_check_says_what_settles_it(self):
        self.assertEqual([check["id"] for ind in build.load()["indicators"] for check in ind["checks"] if "settled_by" not in check], [])

    def test_the_built_file_is_current(self):
        with open(build.JSON_PATH, encoding="utf-8") as f:
            self.assertEqual(json.load(f), build.load(), "run: python3 standard/build.py")


if __name__ == "__main__":
    unittest.main()
