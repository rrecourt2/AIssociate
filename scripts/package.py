"""Check the skills and build the Cowork upload ZIPs (standard library only).

  python3 scripts/package.py          # check sources and build dist/
  python3 scripts/package.py --check  # check only

Source skills contain only SKILL.md. Canonical links become self-contained references/scripts
inside the archives; building never generates or updates companion files in the source tree.
"""
import json
import re
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
STAMP = (2026, 1, 1, 0, 0, 0)  # fixed timestamps: the same sources always give the same ZIP bytes
LINK = re.compile(r"\]\(([^)]+)\)")


class PackageError(Exception):
    pass


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise PackageError("SKILL.md must start with --- frontmatter ---")
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        value = value.strip()
        if not sep or line != line.lstrip() or value.startswith(("|", ">")):
            raise PackageError("use single-line frontmatter fields in this package")
        if key in fields:
            raise PackageError(f"duplicate frontmatter field {key}")
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError as exc:
                raise PackageError("use a valid single-line quoted field") from exc
        elif value.startswith("'"):
            if not value.endswith("'") or len(value) < 2:
                raise PackageError("unterminated quoted frontmatter field")
            value = value[1:-1].replace("''", "'")
        if not isinstance(value, str) or "\n" in value or "\r" in value:
            raise PackageError("frontmatter values must be single-line strings")
        fields[key.strip()] = value
    return fields


def originals(root):
    return {f"../../shared/{p.name}": (f"references/{p.name}", p) for p in (root / "shared").glob("*.md")} | \
           {f"../../tools/{p.name}": (f"scripts/{p.name}", p) for p in (root / "tools").glob("*.py")}


def check_skill(skill, canon):
    """Validate a source skill and resolve its canonical links into {zip path: bytes}."""
    if not skill.is_dir() or sorted(p.name for p in skill.iterdir()) != ["SKILL.md"]:
        raise PackageError(f"{skill.name}: source skills must contain only SKILL.md")
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    fm = frontmatter(text)
    name, desc = fm.get("name", ""), fm.get("description", "")
    if name != skill.name:
        raise PackageError(f"{skill.name}: frontmatter name {name!r} must equal the folder name")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        raise PackageError(f"{skill.name}: name must be kebab-case, at most 64 characters")
    if not 1 <= len(desc) <= 1024:
        raise PackageError(f"{skill.name}: description must be 1-1024 characters (has {len(desc)})")
    files = {}

    def resolve_link(match):
        target = match[1]
        if target.startswith(("https://", "http://", "#")):
            return match[0]
        path, separator, anchor = target.partition("#")
        if path not in canon:
            raise PackageError(f"{skill.name}: unknown canonical link {target}")
        local, source = canon[path]
        files[local] = source.read_bytes()
        return f"]({local}{separator}{anchor})"

    files["SKILL.md"] = LINK.sub(resolve_link, text).encode("utf-8")
    companions = {k: v for k, v in files.items() if k != "SKILL.md"}
    if len(companions) > 20:
        raise PackageError(f"{skill.name}: {len(companions)} companion files (maximum 20)")
    if any(len(v) > 5 * 1024 ** 2 for v in companions.values()) or sum(map(len, companions.values())) > 10 * 1024 ** 2:
        raise PackageError(f"{skill.name}: companion files exceed 5 MB each or 10 MB in total")
    return files


def archive(files):
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = ZipInfo(name, STAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])
    data = buffer.getvalue()
    with ZipFile(BytesIO(data)) as z:
        if z.testzip() is not None or {n: z.read(n) for n in z.namelist()} != files:
            raise PackageError("archive read-back failed")
    return data


def build(root=ROOT, dest=None, check_only=False):
    for name in ("skills", "shared", "tools", ".claude-plugin", "INSTALL.md"):
        source = root / name
        for path in [source, *source.rglob("*")]:
            if path.is_symlink():
                raise PackageError(f"{path}: symlinks are not allowed")
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    if manifest.get("name") != "aissociate" or not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        raise PackageError("plugin.json needs name 'aissociate' and a version like 0.5.0")
    canon = originals(root)
    skills = {s.name: check_skill(s, canon) for s in sorted((root / "skills").iterdir())}
    if check_only:
        return {name: len(files) for name, files in skills.items()}
    package = {".claude-plugin/plugin.json": (root / ".claude-plugin/plugin.json").read_bytes(),
               "INSTALL.md": (root / "INSTALL.md").read_bytes()}
    individual = {"INSTALL.md": package["INSTALL.md"]}
    for name, files in skills.items():
        package.update({f"skills/{name}/{rel}": data for rel, data in files.items()})
        individual[f"{name}.zip"] = archive(files)
    dest = Path(dest or root / "dist")
    dest.mkdir(exist_ok=True)
    out = {}
    for name, files in ((f"aissociate-{manifest['version']}.zip", package),
                        (f"aissociate-individual-skills-{manifest['version']}.zip", individual)):
        (dest / name).write_bytes(archive(files))
        out[name] = len(files)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv not in ([], ["--check"]):
        print("usage: package.py [--check]", file=sys.stderr)
        return 1
    try:
        result = build(check_only="--check" in argv)
    except (PackageError, OSError, ValueError) as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    for name, count in result.items():
        print(f"{name}: {count} files OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
