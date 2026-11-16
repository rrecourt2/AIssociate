"""Everything that touches the disk. No other module reads or writes files."""
import hashlib
import json
import os

CLIENT = "Client folder"
MANIFEST = CLIENT + "/manifest.json"
MEMORY = "Internal/record/record.json"  # the record of the deal
OLD_MEMORY = "Internal/memory/memory.json"  # where it was kept before; `upgrade` moves it
WIKI = "Internal/wiki"
OUTPUTS = "Internal/outputs"
EXTRACTS = "Internal/sources/extracts"
BASE = "Internal/standard/base.json"
INSTITUTION = "Internal/standard/institution.json"
DEAL_LAYER = "Internal/standard/deal.json"
INTERNAL_FOLDERS = ("sources", "record", "wiki", "standard", "outputs")

WRITTEN = []  # what this run wrote, for a host that has to save files itself


class Refused(Exception):
    """The input is malformed, or the action would leave the deal folder."""


def inside(deal, relative):
    """The full path of a file in the deal folder. Refuses a path that leads out of it."""
    root = os.path.realpath(deal)
    target = os.path.realpath(os.path.join(root, relative))
    if target != root and not target.startswith(root + os.sep):
        raise Refused(f"{relative} is outside the deal folder")
    return target


def write(deal, relative, text):
    """Write a text file in the deal folder. The only place the tool writes."""
    target = inside(deal, relative)
    if os.path.islink(target + ".tmp"):
        raise Refused(f"{relative}.tmp is a link")  # it could lead out of the deal folder
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(target + ".tmp", target)
    WRITTEN.append(relative)


def write_json(deal, relative, data):
    write(deal, relative, json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def move(deal, source, relative):
    """Move a document that is already in the deal folder to its place. The only place the tool moves."""
    origin, target = inside(deal, source), inside(deal, relative)
    if origin == target:
        return
    if not os.path.isfile(origin):
        raise Refused(f"{source} is not a file in the deal folder")
    if os.path.exists(target):
        raise Refused(f"{relative} already exists")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    os.replace(origin, target)
    WRITTEN.append(relative)


def make_folder(deal, relative):
    os.makedirs(inside(deal, relative), exist_ok=True)


def read(deal, relative, default=None):
    path = inside(deal, relative)
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8-sig") as f:  # also reads a file that starts with a byte-order mark
        return f.read()


def read_json(deal, relative, default=None):
    text = read(deal, relative)
    return default if text is None else json.loads(text)


def read_input(path):
    """Read a JSON file the user or the assistant hands to a command."""
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def fingerprint(deal, relative):
    """The SHA-256 of a file, or None if it is not there."""
    path = inside(deal, relative)
    if not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def listing(deal, relative):
    """Every file under a folder of the deal, as paths from the deal folder."""
    found = []
    for folder, _, names in os.walk(inside(deal, relative)):
        for name in names:
            path = os.path.relpath(os.path.join(folder, name), os.path.realpath(deal))
            found.append(path.replace(os.sep, "/"))
    return sorted(found)


def beside(path, link):
    """Where a relative link in a file leads, as a path from the deal folder."""
    return os.path.normpath(os.path.join(os.path.dirname(path), link)).replace(os.sep, "/")


def packaged(name):
    """The text of a file that ships with the tool."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name), encoding="utf-8") as f:
        return f.read()


def packaged_standard():
    """The standard that ships with the tool."""
    return json.loads(packaged("standard.json"))
