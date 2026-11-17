"""The rules that keep the tool simple to audit. This test fails if the code breaks one."""
import ast
import glob
import os
import unittest

PACKAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bankability2")
ALLOWED_IMPORTS = {"argparse", "datetime", "hashlib", "json", "os", "re", "sys", "unicodedata"}
FORBIDDEN_NAMES = {"eval", "exec", "compile", "__import__", "input", "breakpoint",
                   "getattr", "setattr", "delattr", "globals", "locals", "vars", "__builtins__"}
ALLOWED_OS = {"path", "replace", "makedirs", "walk", "sep"}  # all that files.py may use of os
WRITERS = {"write", "move", "make_folder"}  # the only functions that change the disk
MAX_FILES, MAX_LINES, MAX_FUNCTION = 7, 2250, 100


def sources():
    for path in sorted(glob.glob(os.path.join(PACKAGE, "*.py"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        yield os.path.basename(path), text, ast.parse(text)


def opens_for_writing(function):
    """Whether a function opens a file for anything but reading."""
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            modes = node.args[1:2] + [keyword.value for keyword in node.keywords if keyword.arg == "mode"]
            if any(not isinstance(mode, ast.Constant) or mode.value not in ("r", "rb") for mode in modes):
                return True
    return False


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
                        self.assertIsNone(alias.asname, f"{name}: a module imported under another name")
                if isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 1, f"{name}: 'from' may only import the tool's own modules")

    def test_nothing_forbidden(self):
        for name, _, tree in sources():
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, FORBIDDEN_NAMES, name)
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "os":
                    self.assertIn(node.attr, ALLOWED_OS, name)

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
            changes_disk = "os.replace" in text or "os.makedirs" in text or opens_for_writing(function)
            self.assertEqual(changes_disk, function.name in WRITERS, function.name)
            if function.name in WRITERS:
                self.assertIn("inside(deal", text, f"{function.name} must check its path")


if __name__ == "__main__":
    unittest.main()
