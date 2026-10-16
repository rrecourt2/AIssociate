import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from word_fixtures import edit_text, make_template
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
def test_extracted_lead_workflow_without_repository_imports(root, tmp_path, layout):
    packages = tmp_path / "packages"
    package.build(root, packages)
    version = json.loads((root / ".claude-plugin/plugin.json").read_text())["version"]
    extracted = tmp_path / "extracted"
    if layout == "plugin":
        with ZipFile(packages / f"aissociate-{version}.zip") as archive:
            archive.extractall(extracted)
        scripts = extracted / "skills/fp-lead/scripts"
        evidence_tool = extracted / "skills/deal-analyst/scripts/register.py"
    else:
        with ZipFile(packages / f"aissociate-individual-skills-{version}.zip") as archive:
            archive.extract("fp-lead.zip", extracted)
            archive.extract("deal-analyst.zip", extracted)
        with ZipFile(extracted / "fp-lead.zip") as archive:
            archive.extractall(extracted / "fp-lead")
        with ZipFile(extracted / "deal-analyst.zip") as archive:
            archive.extractall(extracted / "deal-analyst")
        scripts = extracted / "fp-lead/scripts"
        evidence_tool = extracted / "deal-analyst/scripts/register.py"
    assert (scripts / "plugin.json").read_bytes() == (root / ".claude-plugin/plugin.json").read_bytes()
    for skill in (root / "skills").iterdir():
        assert sorted(p.name for p in skill.iterdir()) == ["SKILL.md"]
    skill_text = (scripts.parent / "SKILL.md").read_text()
    assert "../../" not in skill_text and "](scripts/fp.py)" in skill_text
    assert "](references/workflow-contract.md)" in skill_text
    assert (scripts.parent / "references/workflow-contract.md").read_bytes() == (root / "shared/workflow-contract.md").read_bytes()
    work = tmp_path / "outside-repository"
    work.mkdir()
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    def run(script, *args, code=0):
        result = subprocess.run([sys.executable, "-S", str(scripts / script), *map(str, args)],
                                cwd=work, env=env, text=True, capture_output=True)
        assert result.returncode == code, result.stdout + result.stderr
        return result.stdout

    def command(script, command, folder, payload, code=0):
        request = work / "request.json"
        request.write_text(json.dumps(payload))
        return json.loads(run(script, command, folder, request, code=code))

    info = json.loads(run("fp.py", "--version"))
    assert info["name"] == "aissociate" and info["version"] == version
    assert info["scripts"] == {name: hashlib.sha256((root / "tools" / name).read_bytes()).hexdigest()
                                for name in ("fp.py", "register.py", "fp_docx.py", "fin_table.py")}
    for processor in ("register.py", "fp_docx.py", "fin_table.py"):
        assert "usage:" in run(processor, "--help")

    template, base = work / "template.docx", work / "partial.docx"
    make_template(template)
    make_template(base)
    edit_text(base, "[Summarise the proposal]", "Existing company account.")
    original = base.read_bytes()
    example = work / "example.txt"
    example.write_text("Approved example: explain the business and the financing case.")
    folder = work / "deal"
    master = folder / "register.json"
    run(evidence_tool, "init", folder, "--deal", "synthetic")
    evidence = work / "company-account.txt"
    evidence.write_text("Synthetic company account: the business provides maintenance services. "
                        "FY2025 revenue: scheduled work EUR6m; emergency work EUR4m.")
    claim = dict(assertion="The business provides maintenance services.", kind="fact",
                 sources="S-001 paragraph 1", sections="summary")
    if layout == "plugin":
        claim = dict(assertion="Revenue from maintenance services totals EUR10m.", kind="calculation",
                     value="10", unit="EURm", entity="Synthetic company", period="FY2025",
                     definition="Scheduled and emergency maintenance revenue", method="6 + 4",
                     inputs="S-001 paragraph 1: scheduled 6, emergency 4", sections="summary")
    purpose = "Explore a possible loan; no structure selected. Next: assess cash conversion."
    command(evidence_tool, "apply", folder,
            dict(op_id="evidence-1", base_revision=0, actor="Synthetic officer", changes=[
                {"sheet": "sources", "add": {"title": "Company account", "link": str(evidence),
                                                "coverage": "read", "impact": "assessed"}},
                {"sheet": "claims", "add": claim},
                {"sheet": "analysis", "add": {"id": "strategy", "text": purpose}},
                {"sheet": "analysis", "add": {"id": "performance", "text": "Revenue reviewed; contracts not yet reviewed.",
                                                  "claims": "C-001"}}]))

    # Only the canonical record and readable view are needed to resume an investigation.
    saved = work / "saved-investigation"
    saved.mkdir()
    for name in ("register.json", "Analysis.md"):
        shutil.copyfile(folder / name, saved / name)
        assert (saved / name).read_bytes() == (folder / name).read_bytes()
    assert purpose in run(evidence_tool, "show", saved)
    assert str(evidence) in run(evidence_tool, "show", saved, "C-001")
    analysis = (saved / "Analysis.md").read_text()
    assert purpose in analysis and "contracts not yet reviewed" in analysis and str(evidence) in analysis
    assert "S-001 paragraph 1" in analysis

    def check_bundle(name, current=None):
        delivery = work / name
        result = json.loads(run("fp.py", "bundle", folder, "--out", delivery))
        assert result["status"] == "bundled"
        manifest = json.loads((delivery / "manifest.json").read_text())
        assert manifest["version"] == version
        assert manifest["register_revision"] == json.loads(master.read_text())["revision"]
        expected = {"register.json", "Analysis.md", "register.xlsx", "DDQ.md"}
        if current:
            assert manifest["build_id"] == current["build_id"]
            expected.add(Path(current["word"]).name)
        else:
            assert not manifest.get("build_id")
            assert not list(delivery.glob("*.docx"))
        assert expected <= {item["path"] for item in manifest["files"]}
        for item in manifest["files"]:
            assert hashlib.sha256((delivery / item["path"]).read_bytes()).hexdigest() == item["sha256"]
        before = {p.name: p.read_bytes() for p in delivery.iterdir()}
        run("fp.py", "bundle", folder, "--out", delivery)
        assert before == {p.name: p.read_bytes() for p in delivery.iterdir()}
        return delivery

    check_bundle("evidence-delivery")
    index = run("register.py", "show", folder)
    assert "evidence index" in index and "S-001" in index and "C-001" in index
    assert "maintenance services" in index
    prepare = dict(op_id="prepare-1", base_revision=json.loads(master.read_text())["revision"],
                   deal="synthetic", base=str(base),
                   template=str(template), examples=[str(example)], output_dir=str(folder / "output"),
                   mode="existing", provenance="Authorised synthetic officer draft")
    result = command("fp.py", "prepare", folder, prepare)
    assert result["status"] == "prepared"

    def preflight(op_id, *changes):
        reg = json.loads(master.read_text())
        run_state = dict(reg["run"], preflight=dict(reg["run"]["preflight"], editorial="complete"))
        notes = {"title": "Template and examples", "text": "Keep headings; explain the financing case."}
        analysis = ({"sheet": "analysis", "update": "preflight", "set": notes} if reg["analysis"] else
                    {"sheet": "analysis", "add": dict(notes, id="preflight")})
        return command("register.py", "apply", folder,
                       dict(op_id=op_id, base_revision=reg["revision"], actor="Synthetic officer",
                            changes=[analysis, {"sheet": "run", "set": run_state}, *changes]))

    preflight("preflight-1",
              {"sheet": "open_items", "add": {"text": "Send updated forecast.", "audience": "client",
                                                "raised_by": "Synthetic officer"}},
              {"sheet": "open_items", "add": {"text": "Discuss internal concern.", "audience": "internal",
                                                "addressee": "Client team", "raised_by": "Synthetic officer"}},
              {"sheet": "open_items", "add": {"text": "Unclassified request.", "raised_by": "Synthetic officer"}})
    draft = work / "draft.md"
    draft.write_text("## summary\nRevised company account.\n\n"
                     "## financial-analysis\nExplained financial movements.\n\n{{keep:1}}\n\n"
                     "## market-risk\nMarket context.\n\n## recommendation\nProvisional case.\n")
    build = dict(op_id="build-1", base_revision=json.loads(master.read_text())["revision"],
                 content=str(draft), out="FP-v01.docx")
    first = command("fp.py", "build", folder, build)
    assert first["status"] == "built" and base.read_bytes() == original
    word = Path(first["word"])
    word_bytes = word.read_bytes()
    assert command("fp.py", "build", folder, build)["build_id"] == first["build_id"]
    assert word.read_bytes() == word_bytes

    delivery = check_bundle("delivery-1", first)
    ddq = (delivery / "DDQ.md").read_text()
    assert "Send updated forecast." in ddq
    assert "Discuss internal concern." not in ddq and "Unclassified request." not in ddq

    edit_text(word, "Provisional case.", "Officer wording: condition still required.")
    prepare.update(op_id="prepare-2", base_revision=json.loads(master.read_text())["revision"],
                   base=str(word), mode="normal", provenance="Officer-edited identified output")
    command("fp.py", "prepare", folder, prepare)
    answer = work / "forecast-answer.txt"
    answer.write_text("Synthetic CFO email: updated forecast received, assumptions need assessment.")
    preflight("preflight-2",
              {"sheet": "sources", "add": {"title": "Forecast answer", "link": str(answer),
                                              "type": "email"}},
              {"sheet": "open_items", "update": "O-001", "set": {"status": "answered",
                  "answer": "Updated forecast received.", "answer_source": "S-002 paragraph 1"}})
    draft.write_text("## summary\nUpdated for the forecast answer.\n\n"
                     "## recommendation\nReplacement recommendation.\n")
    second = command("fp.py", "build", folder,
                     dict(op_id="build-2", base_revision=json.loads(master.read_text())["revision"],
                          content=str(draft), out="FP-v02.docx", support=[str(answer)]), code=2)
    assert second["status"] == "partial" and second["build_id"] != first["build_id"]
    text = run("fp_docx.py", "inspect", second["word"], "--markdown")
    assert "Officer wording: condition still required." in text
    assert "Updated for the forecast answer." in text and "Replacement recommendation." not in text
    delivery = check_bundle("delivery-2", second)
    assert "Replacement recommendation." in next(delivery.glob("*.proposals.md")).read_text()
    assert (delivery / answer.name).read_bytes() == answer.read_bytes()
    assert "Send updated forecast." not in (delivery / "DDQ.md").read_text()
    reg = json.loads(master.read_text())
    assert reg["open_items"][0]["status"] == "answered" and reg["sources"][1]["impact"] == "pending"
    before = master.read_bytes()
    status = json.loads(run("fp.py", "status", folder))
    assert all(item["matches"] for item in status["files"]) and master.read_bytes() == before


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
