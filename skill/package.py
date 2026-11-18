"""Pack the skill: its instructions, the tool and the standard, in one zip.

    python3 skill/package.py        writes dist/aissociate.zip
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skill", "aissociate")
TOOL = os.path.join(ROOT, "bankability2")
OUT = os.path.join(ROOT, "dist", "aissociate.zip")


def main():
    packed = []
    for folder, _, names in os.walk(SKILL):
        packed += [(os.path.join(folder, name), os.path.relpath(os.path.join(folder, name), SKILL)) for name in names]
    packed += [(os.path.join(TOOL, name), f"scripts/bankability2/{name}")
               for name in os.listdir(TOOL) if name.endswith((".py", ".json", ".html"))]  # the code, the standard, the wiki view
    packed.append((os.path.join(ROOT, "LICENSE"), "LICENSE"))
    if len(packed) > 20:  # Copilot Cowork allows a skill 20 files
        raise SystemExit(f"{len(packed)} files: a skill may hold 20")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, name in sorted(packed, key=lambda item: item[1]):
            archive.write(path, name.replace(os.sep, "/"))  # SKILL.md at the root of the archive, as Copilot Cowork asks
    print(f"{OUT}: {len(packed)} files")


if __name__ == "__main__":
    main()
