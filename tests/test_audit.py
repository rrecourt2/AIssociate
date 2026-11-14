"""The rules that keep the tool simple to audit. This test fails if the code breaks one."""
import ast
import glob
import os
import unittest

PACKAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bankability2")
ALLOWED_IMPORTS = {"argparse", "datetime", "hashlib", "json", "os", "re", "sys"}
FORBIDDEN_NAMES = {"eval", "exec", "compile", "__import__", "input", "breakpoint"}
FORBIDDEN_OS = {"environ", "getenv", "system", "popen", "remove", "unlink", "rmdir", "removedirs", "rename", "chmod"}
WRITERS = {"write", "move", "make_folder"}  # the only functions that change the disk
MAX_FILES, MAX_LINES, MAX_FUNCTION = 7, 2000, 100


def sources():
    for path in sorted(glob.glob(os.path.join(PACKAGE, "*.py"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        yield os.path.basename(path), text, ast.parse(text)


class Audit(unittest.TestCase):
    def test_size(self):
        files = list(sources())
        self.assertLessEqual(len(files), MAX_FILES)
        self.assertLessEqual(sum(len(text.splitlines()) for _, text, _ in files), MAX_LINES)
        for name, _, tree in files:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.assertLessEqual(node.end_lineno - node.lineno + 1, MAX_FUNCTION, f"{name}: {node.name}")

    def test_only_the_standard_library(self):
        for name, _, tree in sources():
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name, ALLOWED_IMPORTS, name)
                if isinstance(node, ast.ImportFrom):
                    self.assertTrue(node.level == 1 or node.module in ALLOWED_IMPORTS, f"{name}: {node.module}")

    def test_nothing_forbidden(self):
        for name, _, tree in sources():
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, FORBIDDEN_NAMES, name)
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "os":
                    self.assertNotIn(node.attr, FORBIDDEN_OS, name)

    def test_only_one_module_touches_the_disk(self):
        for name, _, tree in sources():
            if name == "files.py":
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, {"open", "os"}, f"{name} touches the disk")

    def test_writes_stay_in_the_deal_folder(self):
        tree = next(tree for name, _, tree in sources() if name == "files.py")
        for function in [node for node in tree.body if isinstance(node, ast.FunctionDef)]:
            text = ast.unparse(function)
            changes_disk = any(sign in text for sign in ("os.replace", "os.makedirs", "'w'", "'a'", "'wb'", "'x'"))
            self.assertEqual(changes_disk, function.name in WRITERS, function.name)
            if function.name in WRITERS:
                self.assertIn("inside(deal", text, f"{function.name} must check its path")


if __name__ == "__main__":
    unittest.main()
