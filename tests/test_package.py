import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

import package

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def root(tmp_path):
    for part in (".claude-plugin", "shared", "tools", "skills"):
        if (REPO / part).exists():
            shutil.copytree(REPO / part, tmp_path / part)
    (tmp_path / "INSTALL.md").write_text("install")
    return tmp_path


def skill_md(root, name="fp-lead"):
    return root / "skills" / name / "SKILL.md"


def test_real_repository_passes_and_builds_identical_zips(root, tmp_path):
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    package.build(root, check_only=True)
    first = package.build(root, tmp_path / "a")
    second = package.build(root, tmp_path / "b")
    assert first == second
    assert before == {p: p.read_bytes() for p in root.rglob("*")
                      if p.is_file() and p.relative_to(root).parts[0] not in {"a", "b"}}
    for name in first:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
        with ZipFile(tmp_path / "a" / name) as archive:
            assert all(info.date_time == package.STAMP for info in archive.infolist())


@pytest.mark.parametrize("layout", ["plugin", "individual"])
def test_extracted_evidence_workflow_without_repository_imports(root, tmp_path, layout):
    packages = tmp_path / "packages"
    package.build(root, packages)
    version = json.loads((root / ".claude-plugin/plugin.json").read_text())["version"]
    extracted = tmp_path / "extracted"
    if layout == "plugin":
        with ZipFile(packages / f"aissociate-{version}.zip") as archive:
            archive.extractall(extracted)
        lead = extracted / "skills/fp-lead"
    else:
        with ZipFile(packages / f"aissociate-individual-skills-{version}.zip") as archive:
            archive.extract("fp-lead.zip", extracted)
        with ZipFile(extracted / "fp-lead.zip") as archive:
            archive.extractall(extracted / "fp-lead")
        lead = extracted / "fp-lead"
    for skill in (root / "skills").iterdir():
        assert sorted(p.name for p in skill.iterdir()) == ["SKILL.md"]
    skill_text = (lead / "SKILL.md").read_text()
    assert "../../" not in skill_text and "](scripts/register.py)" in skill_text
    assert "](references/workflow-contract.md)" in skill_text
    assert (lead / "references/workflow-contract.md").read_bytes() == (root / "shared/workflow-contract.md").read_bytes()
    work = tmp_path / "outside-repository"
    work.mkdir()
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    def run(script, *args):
        result = subprocess.run([sys.executable, "-S", str(lead / "scripts" / script), *map(str, args)],
                                cwd=work, env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    for processor in ("register.py", "fin_table.py"):
        assert "usage:" in run(processor, "--help")
    folder = work / "deal"
    run("register.py", "init", folder, "--deal", "synthetic")
    evidence = work / "company-account.txt"
    evidence.write_text("Synthetic company account: the business provides maintenance services.")
    purpose = "Explore a possible loan; no structure selected. Next: assess cash conversion."
    request = work / "request.json"
    request.write_text(json.dumps(dict(op_id="evidence-1", base_revision=0, actor="Synthetic officer", changes=[
        {"sheet": "sources", "add": {"title": "Company account", "link": str(evidence),
                                        "coverage": "read", "impact": "assessed"}},
        {"sheet": "claims", "add": {"assertion": "The business provides maintenance services.", "kind": "fact",
                                       "sources": "S-001 paragraph 1"}},
        {"sheet": "analysis", "add": {"id": "strategy", "text": purpose}},
        {"sheet": "open_items", "add": {"text": "Send updated forecast.", "audience": "client",
                                           "raised_by": "Synthetic officer"}},
        {"sheet": "open_items", "add": {"text": "Discuss internal concern.", "audience": "internal",
                                           "raised_by": "Synthetic officer"}}])))
    run("register.py", "apply", folder, request)
    assert sorted(p.name for p in folder.iterdir()) == ["Analysis.md", "register.json"]

    # The canonical record and its readable view are all a later task needs.
    saved = work / "saved-investigation"
    shutil.copytree(folder, saved)
    assert purpose in run("register.py", "show", saved)
    assert str(evidence) in run("register.py", "show", saved, "C-001")
    analysis = (saved / "Analysis.md").read_text()
    assert purpose in analysis and "maintenance services" in analysis
    assert f"[S-001](<{evidence}>) paragraph 1" in analysis
    ddq = run("register.py", "ddq", saved)
    assert "Send updated forecast." in ddq and "Discuss internal concern." not in ddq


def test_name_must_match_folder(root):
    p = skill_md(root)
    p.write_text(p.read_text().replace("name: fp-lead", "name: FP-Lead", 1))
    with pytest.raises(package.PackageError, match="must equal the folder"):
        package.build(root, check_only=True)


def test_description_length_is_enforced(root):
    p = skill_md(root)
    text = p.read_text()
    start = text.index("description:")
    end = text.index("\n", start)
    p.write_text(text[:start] + "description: " + "x" * 1025 + text[end:])
    with pytest.raises(package.PackageError, match="1-1024"):
        package.build(root, check_only=True)


@pytest.mark.parametrize("target", ["../../shared/nowhere.md", "../../README.md", "references/old-copy.md"])
def test_unknown_local_link_is_refused(root, target):
    p = skill_md(root)
    p.write_text(p.read_text() + f"\nSee [missing]({target}).\n")
    with pytest.raises(package.PackageError, match="unknown.*link"):
        package.build(root, check_only=True)


@pytest.mark.parametrize("name", [".DS_Store", "private-notes.md"])
def test_unexpected_skill_files_are_never_packaged(root, name):
    (root / "skills" / "fp-lead" / name).write_bytes(b"private synthetic content")
    with pytest.raises(package.PackageError, match="only SKILL.md"):
        package.build(root, check_only=True)


@pytest.mark.parametrize("relative", ["skills/fp-lead/SKILL.md", "skills/fp-lead", "shared/operating-rules.md",
                                      "tools", ".claude-plugin/plugin.json", "INSTALL.md"])
def test_symlinked_package_inputs_are_refused_without_source_writes(root, relative):
    target = root / relative
    backing = root / "linked-content"
    target.rename(backing)
    target.symlink_to(backing, target_is_directory=backing.is_dir())
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
    with pytest.raises(package.PackageError, match="symlinks are not allowed"):
        package.build(root)
    assert all(p.read_bytes() == data for p, data in before.items())
    assert not (root / "dist").exists()


def test_manifest_version_is_checked(root):
    path = root / ".claude-plugin" / "plugin.json"
    data = json.loads(path.read_text())
    data["version"] = "latest"
    path.write_text(json.dumps(data))
    with pytest.raises(package.PackageError, match="version"):
        package.build(root, check_only=True)


def test_link_with_anchor_cannot_hide_a_missing_companion(root):
    p = skill_md(root)
    p.write_text(p.read_text() + "\n[missing](../../shared/absent.md#section)\n")
    with pytest.raises(package.PackageError, match="unknown.*link"):
        package.build(root, check_only=True)


def test_folded_description_is_not_silently_treated_as_one_character(root):
    p = skill_md(root)
    text = p.read_text()
    start, end = text.index("description:"), text.index("\n", text.index("description:"))
    p.write_text(text[:start] + "description: >\n  " + "x" * 1025 + text[end:])
    with pytest.raises(package.PackageError, match="single-line"):
        package.build(root, check_only=True)


def test_unknown_cli_argument_does_not_build(monkeypatch, capsys):
    monkeypatch.setattr(package, "build", lambda **kw: pytest.fail("must not build"))
    assert package.main(["--chek"]) == 1
    assert "usage" in capsys.readouterr().err.lower()
