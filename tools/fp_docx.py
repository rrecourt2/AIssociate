#!/usr/bin/env python3
"""Read, build and check FP Word files with the Python standard library only.

document.xml is changed by splicing byte ranges; XML this tool did not generate is
never re-serialised. Other parts are copied unchanged except our two custom identity
properties, their package metadata, and a .dotx main content type. Macro-enabled files are refused.
A section is the body between one heading and the next heading of any level.

  fp_docx.py inspect DOCX [--markdown]
  fp_docx.py build --base BASE.docx --content CONTENT.md --out OUT.docx [--first | --existing]
                   [--template BLANK.docx] [--fields FIELDS.json] [--protect ID,ID]
                   [--record SOURCE.sections.json] [--deal-id DEAL]
  fp_docx.py find-record DOCX [--folder DIR]
  fp_docx.py check DOCX [--template TEMPLATE.docx]

Build modes (a section with comments or tracked changes is never rewritten in any mode):
  --first     a new FP from the blank template; BASE must be byte-identical to --template.
  --existing  an officer's draft without an assistant record, checked against --template; every
              section named in the draft is rewritten except those listed in --protect and those
              holding a missing template heading as plain text.
  (neither)   a later round; needs BASE.sections.json (or --record for a renamed copy, found with
              find-record) and rewrites only sections the assistant wrote that nobody has changed since.
"""
import argparse
import hashlib
import json
import os
import posixpath
import shutil
import re
import sys
import tempfile
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.parsers import expat
from xml.sax.saxutils import escape

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
XML_SPACE = "http://www.w3.org/XML/1998/namespace space"
AI_TAG = "fp-assistant"
ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
TAG = re.compile(r"\s*\[[SRMOGTC]-\d+[^\]]*\]")
TAG_ID = re.compile(r"\b[SRMOGTC]-\d+\b")
TRACKED = {"ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "tblPrChange",
           "trPrChange", "tcPrChange", "sectPrChange", "cellIns", "cellDel"}
COMMENT = {"commentRangeStart", "commentRangeEnd", "commentReference"}
FIXED = {"drawing", "pict", "object", "fldChar", "fldSimple", "instrText", "sectPr", "sdt",
         "AlternateContent", "oMath", "footnoteReference", "endnoteReference"}
NOISE = {"proofErr", "lastRenderedPageBreak"}
TEMPLATE_MAIN, DOCUMENT_MAIN = b"wordprocessingml.template.main+xml", b"wordprocessingml.document.main+xml"


class Refuse(Exception):
    """A requested change is unsafe or impossible; existing files are preserved."""


# ---------- reading: byte-exact element tree ----------

def tag_end(buf, pos):
    """Index just past the '>' of the tag starting at pos, honouring quoted attributes."""
    quote, i = None, pos + 1
    while True:
        c = buf[i]
        if quote:
            if c == quote:
                quote = None
        elif c in (34, 39):
            quote = c
        elif c == 62:
            return i + 1
        i += 1


class Node:
    __slots__ = ("uri", "tag", "attrs", "start", "end", "parent", "kids", "text")

    def __init__(self, uri, tag, attrs, start, parent):
        self.uri, self.tag, self.attrs, self.start, self.parent = uri, tag, attrs, start, parent
        self.end, self.kids, self.text = None, [], []

    def iter(self):
        yield self
        for k in self.kids:
            yield from k.iter()

    def find(self, *path):
        n = self
        for t in path:
            n = next((k for k in n.kids if k.uri == W and k.tag == t), None)
            if n is None:
                return None
        return n

    def wattr(self, name):
        return self.attrs.get(f"{W} {name}")

    def deleted(self):
        n = self.parent
        while n is not None:
            if n.tag in ("del", "moveFrom"):
                return True
            n = n.parent
        return False

    def plain(self):
        """Text as if tracked changes were accepted, with tabs and line breaks."""
        out = []
        for n in self.iter():
            s = ("".join(n.text) if n.tag == "t" else "\t" if n.tag == "tab" and n.parent.tag == "r"
                 else "\n" if n.tag == "br" and n.wattr("type") not in ("page", "column") else "")
            if s and n.uri == W and not n.deleted():
                out.append(s)
        return "".join(out)


def scan(buf):
    parser = expat.ParserCreate(namespace_separator=" ")
    parser.buffer_text = True
    stack, roots = [], []

    def start(name, attrs):
        uri, _, tag = name.rpartition(" ")
        node = Node(uri, tag, attrs, parser.CurrentByteIndex, stack[-1] if stack else None)
        (stack[-1].kids if stack else roots).append(node)
        stack.append(node)

    def end(name):
        node = stack.pop()
        se = tag_end(buf, node.start)
        node.end = se if buf[se - 2:se] == b"/>" else buf.index(b">", parser.CurrentByteIndex) + 1

    def data(text):
        if stack:
            stack[-1].text.append(text)

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.CharacterDataHandler = data
    parser.Parse(buf, True)
    return roots[0]


def norm(text):
    text = re.sub(r"^\s*\d+(\.\d+)*(?:\.\s*|\s+)", "", text or "")
    return re.sub(r"\s+", " ", text).strip().rstrip(":").strip().casefold()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", norm(text)).strip("-") or "section"


def style_info(styles_xml):
    """styleId -> (name, heading level or None), levels following basedOn chains; the id of the
    default paragraph style; and the list styles (named "List ..." or carrying numbering)."""
    if not styles_xml:
        return {}, "Normal", set()
    w = "{%s}" % W
    raw, default, lists = {}, "Normal", set()
    for s in ET.fromstring(styles_xml).iter(w + "style"):
        sid = s.get(w + "styleId")
        if s.get(w + "type") == "paragraph" and s.get(w + "default") in ("1", "true", "on"):
            default = sid
        name = s.find(w + "name")
        lvl = s.find(f"{w}pPr/{w}outlineLvl")
        base = s.find(w + "basedOn")
        raw[sid] = (name.get(w + "val") if name is not None else sid,
                    int(lvl.get(w + "val")) if lvl is not None else None,
                    base.get(w + "val") if base is not None else None)
        if "list" in (raw[sid][0] or "").lower() or s.find(f"{w}pPr/{w}numPr") is not None:
            lists.add(sid)

    def level(sid, seen=()):
        if sid not in raw or sid in seen:
            return None
        _, lvl, base = raw[sid]
        if lvl is not None:
            return lvl + 1 if lvl < 9 else None
        return level(base, seen + (sid,)) if base else None

    return {sid: (v[0], level(sid)) for sid, v in raw.items()}, default, lists


class Doc:
    """A .docx opened for reading: zip entries, document.xml bytes, tree, styles, sections."""

    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as z:
            self.infos = z.infolist()
            self.parts = {i.filename: z.read(i.filename) for i in self.infos}
        self.xml = self.parts["word/document.xml"]
        types = self.parts.get("[Content_Types].xml", b"")
        self.template, self.macro = TEMPLATE_MAIN in types, b"macroEnabled" in types
        self.root = scan(self.xml)
        head = self.xml[self.root.start:tag_end(self.xml, self.root.start)]
        m = re.search(rb'xmlns:(\w+)="' + re.escape(W.encode()) + b'"', head)
        if not m:
            raise Refuse("the Word main namespace has no prefix; refusing to guess")
        self.w = m.group(1).decode()
        self.styles, self.default_style, self.list_styles = style_info(self.parts.get("word/styles.xml"))
        w = "{" + W + "}"
        defaults = [s for s in ET.fromstring(self.parts.get("word/styles.xml", b"<styles/>"))
                    if s.get(w + "type") == "table" and s.get(w + "default") in ("1", "true", "on")]
        self.plain_default_table = all(s.find(w + "tblStylePr") is None and s.find(w + "basedOn") is None
                                       for s in defaults)
        self.style_id = {name: sid for sid, (name, _) in self.styles.items()}
        self.body = self.root.find("body")
        if self.body is None:
            raise Refuse(f"{self.path.name} has no document body")
        self.incidental = self._incidental_bookmarks()
        self.sections = self._sections()

    def level(self, node):
        if node.tag != "p":
            return None
        lvl = node.find("pPr", "outlineLvl")
        if lvl is not None:
            v = int(lvl.wattr("val"))
            return v + 1 if v < 9 else None
        ps = node.find("pPr", "pStyle")
        return self.styles.get(ps.wattr("val"), (None, None))[1] if ps is not None else None

    def _sections(self):
        kids = self.body.kids
        heads = [i for i, k in enumerate(kids) if self.level(k)]
        out, seen = [], {}
        for n, i in enumerate(heads):
            j = heads[n + 1] if n + 1 < len(heads) else len(kids)
            body = [k for k in kids[i + 1:j] if k.tag != "sectPr"]
            sid = slug(kids[i].plain())
            seen[sid] = seen.get(sid, 0) + 1
            if seen[sid] > 1:
                sid = f"{sid}-{seen[sid]}"
            out.append({"id": sid, "heading": kids[i].plain().strip(), "level": self.level(kids[i]),
                        "head": kids[i], "body": body, "doc": self})
        return out

    def _incidental_bookmarks(self):
        """Bookmark markers that are noise, as (tag, id): those of _GoBack and of the _Hlk... bookmarks Word
        adds on its own when nothing refers to them, and an end whose start is gone (its paragraph was
        rewritten). A name used by a hyperlink anchor or a field (REF, PAGEREF, HYPERLINK \\l ...) in the body,
        headers, footers or notes makes the bookmark functional content."""
        anchors, codes = [], []
        for name, data in self.parts.items():
            if re.fullmatch(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml", name):
                for n in (self.root if name == "word/document.xml" else scan(data)).iter():
                    if n.tag in ("hyperlink", "fldSimple"):
                        anchors.append(n.wattr("anchor") or n.wattr("instr") or "")
                    elif n.tag == "instrText":
                        codes.append("".join(n.text))  # a field code may be split over runs
        refs = "\n".join(anchors) + "\n" + "".join(codes)
        marks = [(n.tag, n.wattr("id"), n.wattr("name") or "") for n in self.root.iter()
                 if n.tag in ("bookmarkStart", "bookmarkEnd")]
        starts = {i for tag, i, _ in marks if tag == "bookmarkStart"}
        hidden = {i for tag, i, name in marks if tag == "bookmarkStart"
                  and re.match(r"_GoBack$|_Hlk", name) and name not in refs}
        return {(tag, i) for tag, i, _ in marks if i in hidden or i not in starts}

    def comments(self):
        """Comment id -> {author, date, text}."""
        xml = self.parts.get("word/comments.xml")
        if not xml:
            return {}
        return {c.wattr("id"): {"author": c.wattr("author") or "", "date": c.wattr("date") or "",
                                "text": c.plain().strip()}
                for c in scan(xml).kids if c.tag == "comment"}


def harmless(k):
    """Table layout Word recomputes when it saves (tests/fixtures/word-saved): the grid, automatic
    widths, row exceptions, indent and cell margins."""
    return (k.tag in ("tblGrid", "tblPrEx", "tblInd", "tblCellMar")
            or (k.tag in ("tblW", "tcW") and k.wattr("type") in ("auto", "nil")))


def table_look(n):
    """The six table-look flags; explicit flags take precedence over the hexadecimal bitmask."""
    bits = int(n.wattr("val") or "0", 16)
    return tuple(n.wattr(flag) in ("1", "true", "on") if n.wattr(flag) is not None else bool(bits & (32 << i))
                 for i, flag in enumerate(("firstRow", "lastRow", "firstColumn", "lastColumn", "noHBand", "noVBand")))


def canon(n, doc, inc, masked=()):
    """n as nested lists [tag, attributes, text, children] without the noise of a Word save: w14 and
    rsid attributes, xml:space (the exact text is kept), proofing marks, the incidental bookmark markers
    `inc`, run languages, paragraph-mark properties, the default paragraph style and harmless table layout.
    Adjacent runs with equal properties are merged. A cell in `masked` (filled through --fields) counts
    by its formatting and protected marks only."""
    if id(n) in masked:
        p = n.find("p")
        r = p.find("r") if p is not None else None
        keep = [x for x in (p and p.find("pPr"), r and r.find("rPr")) if x is not None]
        return ["filled cell", [], "", [canon(x, doc, inc) for x in keep + [
            x for x in n.iter() if x.tag in COMMENT | TRACKED | {"hyperlink"}]]]
    attrs = sorted([k, v] for k, v in n.attrs.items() if k != XML_SPACE and not k.startswith(W14 + " ")
                   and not k.rpartition(" ")[2].startswith("rsid"))
    if n.tag == "tblLook":
        attrs = list(table_look(n))
    if n.tag == "tbl":
        attrs.append(["assistant table", str(not is_fixed(n))])
    text = "".join(n.text)
    out = [n.tag if n.uri == W else f"{n.uri} {n.tag}", attrs,
           text if n.tag in ("t", "delText", "instrText") else text.strip(), []]
    for k in n.kids:
        default_style = k.tag == "pStyle" and k.wattr("val") == doc.default_style
        # Word 16.113 also writes 04A0 on unstyled tables; it has no effect without conditional styles.
        default_look = (k.tag == "tblLook" and (
            table_look(k) == ((True, False, True, False, False, True)
                             if n.find("tblStyle") is not None else (False,) * 6)
            or n.find("tblStyle") is None and doc.plain_default_table
            and table_look(k) == (True, False, True, False, False, True)))
        if (k.tag in NOISE or harmless(k) or (n.tag == "rPr" and k.tag in ("lang", "noProof"))
                or (k.tag, k.wattr("id")) in inc or default_look
                or (n.tag == "pPr" and (k.tag == "rPr" or default_style))):
            continue
        c = canon(k, doc, inc, masked)
        if not (k.tag in ("pPr", "rPr", "tblPr", "trPr", "tcPr") and not c[1] and not c[3]):  # now empty
            merge(out[3], c)
    return out


def merge(kids, c):
    """Append canonical node c, joining adjacent text, and adjacent runs with equal properties."""
    last, props = kids[-1] if kids else None, lambda r: [x for x in r[3] if x[0] == "rPr"]
    if last and last[0] == c[0] == "t":
        last[2] += c[2]
    elif last and last[0] == c[0] == "r" and props(last) == props(c):
        for x in c[3]:
            if x[0] != "rPr":
                merge(last[3], x)
    else:
        kids.append(c)


def signature(sec, inc):
    """The hash of a section's canonical form, leaving out the incidental bookmark markers `inc`."""
    data = json.dumps([canon(k, sec["doc"], inc) for k in [sec["head"]] + sec["body"]])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def signatures(doc):
    """Section id -> signature, judged by the document's own incidental bookmarks."""
    return {s["id"]: signature(s, doc.incidental) for s in doc.sections}


def fixed_node(n, inc):
    """An object, field, control, section break, note reference, bookmark marker (except the incidental
    markers `inc`) or page/column break."""
    return (n.tag in FIXED or (n.tag in ("bookmarkStart", "bookmarkEnd") and (n.tag, n.wattr("id")) not in inc)
            or (n.tag == "br" and n.wattr("type") in ("page", "column")))


def is_fixed(k, incidental=()):
    """Content this tool must keep in place: template tables, captions and paragraphs with fixed nodes
    (bookmarks other than the incidental ones, given as Doc.incidental)."""
    if k.tag == "tbl":
        d = k.find("tblPr", "tblDescription")
        return not (d is not None and d.wattr("val") == AI_TAG)
    if k.tag != "p":
        return True
    if any(fixed_node(n, incidental) for n in k.iter()):
        return True
    style = k.find("pPr", "pStyle")
    return style is not None and "caption" in (style.wattr("val") or "").lower()


def inventory(doc, inc, filled=()):
    """The fixed objects of the whole body as a sorted list (a multiset), leaving out the incidental bookmark
    markers `inc`. Cover cells filled through --fields (indexes among all w:tc) count by their formatting only."""
    tcs = [n for n in doc.body.iter() if n.tag == "tc"]
    masked, out = {id(tcs[i]) for i in filled}, []
    for n in doc.body.iter():
        if n.tag == "bookmarkStart" and (n.tag, n.wattr("id")) not in inc:
            out.append(f"bookmark {n.wattr('name')}")
        elif n.tag in ("instrText", "fldSimple"):
            out.append("field " + (n.wattr("instr") or "".join(n.text)))
        elif n.tag in ("drawing", "pict", "object"):
            out.append("object")
        elif n.tag == "tbl" and is_fixed(n):
            out.append("table " + json.dumps(canon(n, doc, inc, masked)))
        elif n.tag in ("sdt", "sectPr", "footnoteReference", "endnoteReference"):
            out.append(f"{n.tag} {n.wattr('id') or ''}")
        elif n.tag == "br" and n.wattr("type") in ("page", "column"):
            out.append(f"break {n.wattr('type')}")
    return sorted(out)


def flags(sec, inc):
    tags = {n.tag for k in [sec["head"]] + sec["body"] for n in k.iter()}
    return {"has_comments": bool(tags & COMMENT), "has_tracked_changes": bool(tags & TRACKED),
            "fixed_objects": sum(is_fixed(k, inc) for k in sec["body"])}


def section_comment_ids(sec):
    return sorted({n.wattr("id") for k in [sec["head"]] + sec["body"] for n in k.iter()
                   if n.tag in COMMENT})


def sidecar_path(docx):
    return Path(docx).with_suffix(".sections.json")


CUSTOM = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
CUSTOM_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
CUSTOM_TYPE = "application/vnd.openxmlformats-officedocument.custom-properties+xml"
IDENTITY_NAMES = {"deal_id": "FPAssistantDealId", "build_id": "FPAssistantBuildId"}


def custom_part(parts):
    root = ET.fromstring(parts.get("_rels/.rels", f'<Relationships xmlns="{RELS}"/>'))
    rels = [r for r in root if r.get("Type") == CUSTOM_REL]
    if len(rels) > 1 or any(r.get("TargetMode") == "External" for r in rels):
        raise Refuse("ambiguous Word custom-property relationship")
    target = posixpath.normpath(rels[0].get("Target", "").lstrip("/")) if rels else "docProps/custom.xml"
    if target in (".", "..") or target.startswith("../"):
        raise Refuse("invalid Word custom-property relationship")
    if rels and target not in parts:
        raise Refuse("Word custom-property relationship has no target")
    return target


def read_identity(doc):
    """Embedded identity, or {} for a legacy/imported file. Partial identity is unsafe."""
    doc = doc if isinstance(doc, Doc) else Doc(doc)
    data = doc.parts.get(custom_part(doc.parts))
    found = {}
    if data:
        root = ET.fromstring(data)
        for key, name in IDENTITY_NAMES.items():
            props = [p for p in root if p.get("name") == name]
            if props:
                if (len(props) != 1 or len(props[0]) != 1 or props[0][0].tag != f"{{{VT}}}lpwstr"
                        or not (props[0][0].text or "").strip()):
                    raise Refuse("malformed Word assistant identity")
                found[key] = props[0][0].text
    if found and set(found) != set(IDENTITY_NAMES):
        raise Refuse("incomplete Word assistant identity")
    return found


def append_xml(data, fragment):
    """Append a child without reserialising the original package metadata."""
    root = scan(data)
    end = data.rfind(b"</", root.start, root.end)
    if end < 0:  # empty self-closing root
        head_end = tag_end(data, root.start)
        head = data[root.start:head_end]
        name = re.match(rb"<([^\s/>]+)", head).group(1)
        return data[:head_end - 2] + b">" + fragment + b"</" + name + b">" + data[head_end:]
    return data[:end] + fragment + data[end:]


def identity_parts(parts, identity):
    """Change only our two custom properties; retain other properties and relationships."""
    parts = dict(parts)
    target = custom_part(parts)
    data = parts.get(target, f'<Properties xmlns="{CUSTOM}"/>'.encode())
    root = scan(data)
    pids = [int(p.attrs.get("pid", "1")) for p in root.kids]
    for key, name in IDENTITY_NAMES.items():
        root = scan(data)
        old = next((p for p in root.kids if p.attrs.get("name") == name), None)
        pid = old.attrs["pid"] if old else str(max(pids + [1]) + 1)
        pids.append(int(pid))
        prop = (f'<property xmlns="{CUSTOM}" fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" '
                f'pid="{pid}" name="{name}"><vt:lpwstr xmlns:vt="{VT}">'
                f'{escape(identity[key])}</vt:lpwstr></property>').encode()
        data = splice(data, [(old.start, old.end, prop)]) if old else append_xml(data, prop)
    parts[target] = data
    rels = parts.get("_rels/.rels", f'<Relationships xmlns="{RELS}"/>'.encode())
    root = ET.fromstring(rels)
    if not any(r.get("Type") == CUSTOM_REL for r in root):
        used = {r.get("Id") for r in root}
        rid = next(f"fpAssistant{i}" for i in range(len(used) + 1) if f"fpAssistant{i}" not in used)
        rels = append_xml(rels, (f'<Relationship xmlns="{RELS}" Id="{rid}" Type="{CUSTOM_REL}" '
                                 f'Target="{target}"/>').encode())
    parts["_rels/.rels"] = rels
    types = parts["[Content_Types].xml"]
    if not any(t.get("PartName") == "/" + target for t in ET.fromstring(types)):
        types = append_xml(types, (f'<Override xmlns="{CONTENT_TYPES}" PartName="/{target}" '
                                   f'ContentType="{CUSTOM_TYPE}"/>').encode())
    parts["[Content_Types].xml"] = types
    return parts


def read_record(p, doc=None):
    """Validate every ownership field before use, including records beside a Word file."""
    data = read_json(p)
    valid = isinstance(data, dict) and isinstance(data.get("sections"), dict)
    if valid:
        for sid, sec in data["sections"].items():
            valid = (isinstance(sid, str) and bool(sid) and isinstance(sec, dict)
                     and sec.get("owner") in ("ai", "other")
                     and isinstance(sec.get("signature"), str)
                     and re.fullmatch(r"[0-9a-f]{64}", sec["signature"]) is not None
                     and isinstance(sec.get("ids"), list)
                     and all(isinstance(i, str) for i in sec["ids"]))
            if not valid:
                break
    version = data.get("schema_version") if isinstance(data, dict) else None
    if isinstance(data, dict) and "schema_version" in data:
        valid = (valid and type(version) is int and version == 1
                 and all(isinstance(data.get(k), str) and data[k].strip() for k in IDENTITY_NAMES)
                 and "parent_build_id" in data
                 and (data["parent_build_id"] is None or
                      isinstance(data["parent_build_id"], str) and bool(data["parent_build_id"].strip()))
                 and isinstance(data.get("docx_sha256"), str)
                 and re.fullmatch(r"[0-9a-f]{64}", data["docx_sha256"]) is not None)
    if isinstance(data, dict) and "schema_version" not in data and any(k in data for k in IDENTITY_NAMES):
        valid = False
    if not valid:
        raise Refuse(f"{Path(p).name} is not a valid assistant record")
    if doc is not None:
        identity = read_identity(doc)
        if identity:
            if version != 1 or any(data.get(k) != v for k, v in identity.items()):
                raise Refuse(f"{Path(p).name}: record identity does not match the Word deal/build identity")
        elif version is not None or data.get("docx_sha256") != file_sha256(doc.path):
            raise Refuse(f"{Path(p).name}: legacy Word provenance is unverified; similarity cannot authorise "
                         "replacement. Establish the actual source record or prepare proposals separately")
    return data


def load_sidecar(docx):
    p = sidecar_path(docx)
    return read_record(p, Doc(docx)) if p.exists() else {"sections": {}}


def find_record(docx, folder=None):
    """Similarity ranks candidates only. Only exact embedded identity can name a source."""
    folder = Path(folder) if folder else Path(docx).parent
    doc = Doc(docx)
    sigs, identity, candidates, exact = signatures(doc), read_identity(doc), [], []
    for p in sorted(folder.glob("*.sections.json")):
        try:
            data = read_record(p)
        except Refuse:
            continue
        secs = data["sections"]
        matches = bool(identity) and all(data.get(k) == v for k, v in identity.items())
        if matches:
            exact.append(str(p))
        candidates.append({"record": str(p), "matching": sum(secs.get(i, {}).get("signature") == sig
                                                             for i, sig in sigs.items()),
                           "total": len(sigs), "same_ids": list(secs) == list(sigs)})
    candidates.sort(key=lambda c: (c["record"] not in exact, -c["matching"], not c["same_ids"]))
    return {"docx": str(docx), "folder": str(folder), "candidates": candidates,
            "source": exact[0] if len(exact) == 1 else None, "ambiguous": len(exact) != 1}


def read_text(path):
    """UTF-8 text without a byte order mark; anything else is refused."""
    try:
        return Path(path).read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Refuse(f"{Path(path).name} is not UTF-8 text") from None


def read_json(path):
    try:
        return json.loads(read_text(path))
    except ValueError as e:
        raise Refuse(f"{Path(path).name} is not valid JSON ({e})") from None


def publish(path, write):
    """Call write(temp path) for a temp file next to path, then rename it into place with mode 0644."""
    fd, tmp = tempfile.mkstemp(dir=Path(path).parent, suffix=".tmp")
    os.close(fd)
    try:
        write(tmp)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def write_text_file(path, text):
    publish(path, lambda tmp: Path(tmp).write_text(text, encoding="utf-8"))


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- content markdown ----------

def parse_content(text):
    """'## section' blocks -> ({section_id: {"blocks": [...], "raw": str, "ids": [...]}}, warnings)."""
    raw, cur, stray = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S.*?)\s*$", line)
        if m and not line.startswith("###"):
            cur = slug(m.group(1))
            if cur in raw:
                raise Refuse(f"the draft has more than one '## {cur}' section")
            raw[cur] = []
        else:
            (stray if cur is None else raw[cur]).append(line)
    stray = "\n".join(stray).strip()
    warnings = [f"text before the first '## section' heading was not used: {stray}"] if stray else []
    return {k: {"blocks": blocks(v), "raw": "\n".join(v).strip(),
                "ids": sorted(set(TAG_ID.findall("\n".join(v))))} for k, v in raw.items()}, warnings


def blocks(lines):
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append(("p", " ".join(para)))
            para.clear()

    while i < len(lines):
        s = lines[i].strip()
        keep = re.fullmatch(r"\{\{keep:(\d+)\}\}", s)
        if s.startswith("<!--"):  # read-only notes from inspect --markdown are never written
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if not s:
            flush()
        elif keep:
            flush()
            out.append(("keep", int(keep.group(1))))
        elif re.match(r"^[-*]\s+", s):
            flush()
            out.append(("bullet", re.sub(r"^[-*]\s+", "", s)))
        elif re.match(r"^\d+[.)]\s+", s):
            flush()
            out.append(("p", s))
        elif s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append(("table", rows))
            continue
        else:
            para.append(s)
        i += 1
    flush()
    return out


# ---------- writing ----------

class Gen:
    """WordprocessingML strings using the document's own prefix for the main namespace."""

    def __init__(self, doc):
        self.w, self.ids, self.default = doc.w, doc.style_id, doc.default_style

    def runs(self, text):
        w, out = self.w, []
        text = ILLEGAL.sub("", TAG.sub("", text))
        for part in re.split(r"(\*\*[^*]+\*\*)", text):
            bold = len(part) > 4 and part.startswith("**") and part.endswith("**")
            body = part[2:-2] if bold else part
            if body:
                rpr = f"<{w}:rPr><{w}:b/></{w}:rPr>" if bold else ""
                out.append(f'<{w}:r>{rpr}<{w}:t xml:space="preserve">{escape(body)}</{w}:t></{w}:r>')
        return "".join(out)

    def p(self, text, style_id):
        w = self.w
        explicit = style_id not in (None, self.default)  # the default style is never written out
        ppr = f'<{w}:pPr><{w}:pStyle {w}:val="{style_id}"/></{w}:pPr>' if explicit else ""
        return f"<{w}:p>{ppr}{self.runs(text)}</{w}:p>"

    def table(self, rows, width=9000):
        w, n = self.w, max(len(r) for r in rows)
        cw = width // n
        style = self.ids.get("Table Grid")
        tstyle = f'<{w}:tblStyle {w}:val="{style}"/>' if style else ""
        grid = "".join(f'<{w}:gridCol {w}:w="{cw}"/>' for _ in range(n))
        trs = "".join(f"<{w}:tr>" + "".join(
            f'<{w}:tc><{w}:tcPr><{w}:tcW {w}:w="0" {w}:type="auto"/></{w}:tcPr>'
            f"<{w}:p>{self.runs(r[c] if c < len(r) else '')}</{w}:p></{w}:tc>" for c in range(n))
            + f"</{w}:tr>" for r in rows)
        return (f"<{w}:tbl><{w}:tblPr>{tstyle}<{w}:tblW {w}:w=\"0\" {w}:type=\"auto\"/>"
                f'<{w}:tblLook {w}:val="04A0" {w}:firstRow="1" {w}:lastRow="0" {w}:firstColumn="1" '
                f'{w}:lastColumn="0" {w}:noHBand="0" {w}:noVBand="1"/>'
                f'<{w}:tblDescription {w}:val="{AI_TAG}"/></{w}:tblPr>'
                f"<{w}:tblGrid>{grid}</{w}:tblGrid>{trs}</{w}:tbl>")


def render(doc, sec, items, inc):
    """New XML for a section body; fixed content is placed at {{keep:N}} or appended. Prose takes the
    style of the section's first plain paragraph that is not a list."""
    gen = Gen(doc)
    fixed = [k for k in sec["body"] if is_fixed(k, inc)]
    styles = [k.find("pPr", "pStyle") for k in sec["body"] if not is_fixed(k, inc) and k.tag == "p"]
    styles = [s.wattr("val") if s is not None else doc.default_style for s in styles]
    body_style = next((s for s in styles if s not in doc.list_styles), doc.default_style)
    bullet_style = doc.style_id.get("List Bullet")
    keep = lambda k: (k if k.tag == "tbl" else None, doc.xml[k.start:k.end].decode("utf-8"))  # noqa: E731
    out, used = [], set()  # (kept table node, "generated" or None; xml)
    for kind, value in items:
        if kind == "p":
            out.append((None, gen.p(value, body_style)))
        elif kind == "bullet":
            out.append((None, gen.p(value, bullet_style) if bullet_style else gen.p("• " + value, body_style)))
        elif kind == "table" and value:
            out.append(("generated", gen.table(value)))
        elif kind == "keep" and 1 <= value <= len(fixed) and value not in used:
            out.append(keep(fixed[value - 1]))
            used.add(value)
    out += [keep(k) for n, k in enumerate(fixed, 1) if n not in used]
    pos = {id(k): i for i, k in enumerate(sec["body"])}
    xml, before = "", None
    for table, x in out:  # Word merges tables that touch; keep them apart unless they touched in the base
        if table is not None and before is not None and not (
                isinstance(table, Node) and isinstance(before, Node) and pos[id(table)] == pos[id(before)] + 1):
            xml += f"<{doc.w}:p/>"
        xml, before = xml + x, table
    return xml


def splice(xml, edits):
    """Apply (start, end, replacement bytes) edits, last first so offsets stay valid."""
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        xml = xml[:start] + new + xml[end:]
    return xml


def fill_fields(doc, xml, fields, inc):
    """Set the cell right of a matching label cell on the cover (before the first heading), keeping
    the first paragraph's pPr and first run's rPr. A cell with comments, tracked changes, fixed
    objects, bookmarks, hyperlinks or nested tables is protected and left alone.
    Returns the new xml, the filled cells (indexes among all w:tc), missing and protected labels."""
    want, done, protected, edits, filled = {norm(k): str(v) for k, v in fields.items()}, set(), set(), [], []
    limit = doc.sections[0]["head"].start if doc.sections else len(xml)  # sections are spliced after this point
    tcs = [n for n in doc.body.iter() if n.tag == "tc"]
    for tr in (n for n in doc.body.iter() if n.tag == "tr" and n.start < limit):
        cells = [c for c in tr.kids if c.tag == "tc"]
        for label, value in zip(cells, cells[1:]):
            key, paras = norm(label.plain()), [k for k in value.kids if k.tag == "p"]
            if key not in want or key in done or not paras:
                continue
            if any(fixed_node(n, inc) or n.tag in COMMENT | TRACKED | {"hyperlink", "tbl"}
                   for n in value.iter()) or any(is_fixed(p, inc) for p in paras):
                protected.add(key)
                continue
            ppr, run = paras[0].find("pPr"), paras[0].find("r")
            rpr = run.find("rPr") if run is not None else None
            w = doc.w
            new = (f"<{w}:p>{xml[ppr.start:ppr.end].decode() if ppr is not None else ''}<{w}:r>"
                   f"{xml[rpr.start:rpr.end].decode() if rpr is not None else ''}"
                   f'<{w}:t xml:space="preserve">{escape(ILLEGAL.sub("", want[key]))}</{w}:t></{w}:r></{w}:p>')
            edits.append((paras[0].start, paras[-1].end, new.encode("utf-8")))
            filled.append(tcs.index(value))
            done.add(key)
    missing = sorted(k for k in fields if norm(k) not in done)
    return splice(xml, edits), filled, missing, [k for k in missing if norm(k) in protected]


def verify(base, new, written, filled):
    """The preservation check: refuse unless everything this build did not write is unchanged. Both are judged
    by one set of incidental bookmark markers, the union of theirs, so a marker made noise by this build (an
    end whose start was rewritten, a bookmark whose only link was rewritten) is noise in both."""
    inc = base.incidental | new.incidental
    if [s["id"] for s in new.sections] != [s["id"] for s in base.sections]:
        raise Refuse("headings changed during the build; nothing written")
    changed = [a["id"] for a, b in zip(base.sections, new.sections)
               if a["id"] not in written and signature(a, inc) != signature(b, inc)]
    if changed:
        raise Refuse(f"sections not written in this build changed ({', '.join(changed)}); nothing written")
    if inventory(base, inc, filled) != inventory(new, inc, filled):
        raise Refuse("fixed objects (bookmarks, fields, objects, tables, content controls, breaks or notes) "
                     "changed; nothing written")


def write_docx(doc, xml, out, written, filled, identity=None):
    """Write the zip to a temp file, run the preservation check on it, then rename it into place."""
    parts = {**doc.parts, "word/document.xml": xml}
    if doc.template:  # a .dotx base gives a document
        parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(TEMPLATE_MAIN, DOCUMENT_MAIN)

    if identity:
        parts = identity_parts(parts, identity)

    def write(tmp):
        with zipfile.ZipFile(tmp, "w") as z:
            for info in doc.infos:
                z.writestr(info, parts[info.filename])
            for name in parts.keys() - doc.parts.keys():
                z.writestr(name, parts[name])
        verify(doc, Doc(tmp), written, filled)

    publish(out, write)


def check_mode(doc, base, mode, template, record=None):
    """Refuse a build mode that does not fit the base (see the module docstring)."""
    beside = sidecar_path(base).exists()  # BASE.sections.json
    if mode not in ("first", "existing", "normal"):
        raise Refuse(f"unknown build mode {mode!r}")
    if record and mode != "normal":
        raise Refuse("--record is only for a normal round")
    if record and beside:
        raise Refuse(f"--record refused: {sidecar_path(base).name} already exists; use the base's own record")
    if mode != "normal" and read_identity(doc):
        raise Refuse("identified assistant output requires a normal round; identity cannot be reset")
    if doc.macro:
        raise Refuse("macro-enabled Word files (.docm, .dotm) are not supported")
    if doc.template and mode != "first":
        raise Refuse("a Word template (.dotx) can only be the base of --first")
    if mode == "first":
        if not template:
            raise Refuse("--first needs --template: the configured blank FP template")
        if file_sha256(base) != file_sha256(template):
            raise Refuse("--first builds only from the blank template: the base is not identical to it; "
                         "for an officer's draft use --existing")
        if beside:
            raise Refuse(f"{sidecar_path(base).name} exists, so the base is an FP with an assistant record; "
                         "use a normal round")
    elif mode == "existing":
        if beside:
            raise Refuse(f"{sidecar_path(base).name} exists; use a normal round instead of --existing")
        if not template:
            raise Refuse("--existing needs --template: the blank FP template is used to check the draft's "
                         "headings")
    elif not (beside or record):
        raise Refuse(f"no assistant record ({sidecar_path(base).name}) next to the base. If it is a renamed copy "
                     "of an assistant version (Save As), run find-record and pass --record; if it is a genuine "
                     "first draft that never had an assistant version, use --existing --template")


def check_fields(doc, tpl, baseline):
    """Only recognise cover fields when the first heading agrees with the available reference(s)."""
    if not doc.sections:
        raise Refuse("--fields refused: the document has no recognised headings, so its cover cannot be told "
                     "from its body")
    expected = [(tpl.sections[0]["id"] if tpl and tpl.sections else None, "the template's first section is"),
                (next(iter(baseline), None), "the assistant record starts with")]
    for first, source in expected:
        if first and doc.sections[0]["id"] != first:
            raise Refuse(f"--fields refused: the first recognised heading is {doc.sections[0]['id']!r} but "
                         f"{source} {first!r}, so tables before it may not be the cover; give the earlier "
                         "headings their Heading style in Word")


def _render_build(base, content, out, mode="normal", template=None, fields=None, protect=(), record=None, deal_id=None):
    out = Path(out)
    side, proposals = sidecar_path(out), out.with_suffix(".proposals.md")
    for p in (out, side, proposals):
        if p.exists():
            raise Refuse(f"{p.name} already exists; choose a new version name")
    if fields is not None and not isinstance(fields, dict):
        raise Refuse("--fields must be a JSON object of cover label: value")
    doc = Doc(base)
    inc = doc.incidental
    check_mode(doc, base, mode, template, record)
    # A renamed copy (Save As) is compared with its source version's record, never with a fresh one.
    old_record = read_record(record or sidecar_path(base), doc) if mode == "normal" else {}
    baseline = old_record.get("sections", {})
    previous = read_identity(doc)
    if deal_id is not None and (not isinstance(deal_id, str) or not deal_id.strip()):
        raise Refuse("deal_id must be a non-empty string")
    if previous and deal_id is not None and deal_id != previous["deal_id"]:
        raise Refuse("requested deal identity does not match the base Word file")
    identity = {"deal_id": deal_id or previous.get("deal_id") or str(uuid.uuid4()), "build_id": str(uuid.uuid4())}
    parent_build_id = previous.get("build_id")
    wanted, warnings = parse_content(read_text(content))
    by_id = {s["id"]: s for s in doc.sections}
    unknown = sorted(set(protect) - set(by_id))
    if unknown:
        raise Refuse(f"--protect names no section of the document: {', '.join(unknown)}")
    # The writer cannot insert headings, so template sections absent from the base stay absent.
    tpl = Doc(template) if template else None
    structure = compare_headings(doc, tpl)
    missing_sections = structure["missing_sections"]
    warnings.extend(structure["heading_problems"])
    if missing_sections is None:
        warnings.append("missing template sections were not checked: no --template was given")
    if fields:
        check_fields(doc, tpl, baseline)
    base_sig = signatures(doc)
    edits, written, frozen, unmatched = [], [], {}, []
    for sid, item in wanted.items():
        sec = by_id.get(sid)
        if sec is None:
            unmatched.append(sid)
            continue
        f, b = flags(sec, inc), baseline.get(sid, {})
        # A missing template heading typed as plain text: rewriting would delete the text under it.
        headings = [slug(k.plain()) for k in sec["body"] if k.tag == "p" and len(k.plain().split()) <= 10]
        lost = [sid for sid in missing_sections or () if any(h == sid or h.startswith(sid + "-") for h in headings)]
        if f["has_comments"] or f["has_tracked_changes"]:
            frozen[sid] = "has comments or tracked changes"
        elif sid in protect:
            frozen[sid] = "protected at the officer's request"
        elif lost:
            frozen[sid] = (f"contains the missing template heading {', '.join(lost)} as plain text; "
                           "give it a Heading style in Word")
        elif mode == "normal" and b.get("owner") != "ai":
            frozen[sid] = "not written by the assistant in the base version"
        elif mode == "normal" and b.get("signature") != base_sig[sid]:
            frozen[sid] = "edited since the assistant wrote it"
        else:
            start, end = (sec["body"][0].start, sec["body"][-1].end) if sec["body"] else (sec["head"].end,) * 2
            edits.append((start, end, render(doc, sec, item["blocks"], inc).encode("utf-8")))
            written.append(sid)
    xml = splice(doc.xml, edits)
    filled, missing_fields, protected_fields = [], [], []
    if fields:
        xml, filled, missing_fields, protected_fields = fill_fields(doc, xml, fields, inc)
    write_docx(doc, xml, out, written, filled, identity)
    sections = {}
    for sid, sig in signatures(Doc(out)).items():
        old = baseline.get(sid, {})
        # Stays assistant-owned only if nobody changed it since the assistant wrote it.
        untouched_ai = (old.get("owner") == "ai" and sid not in frozen and sid not in written
                        and sid not in protect and old.get("signature") == base_sig.get(sid))
        sections[sid] = {"owner": "ai" if sid in written or untouched_ai else "other", "signature": sig,
                         "ids": wanted[sid]["ids"] if sid in written else old.get("ids", [])}
    write_text_file(side, json.dumps(
        {"schema_version": 1, **identity, "parent_build_id": parent_build_id,
         "base": Path(base).name, "docx_sha256": file_sha256(out), "sections": sections}, indent=1))
    if frozen or unmatched:
        lines = [f"# Proposed text not applied to {out.name}", "",
                 "These sections were left exactly as they are. Copy what you want into Word.", ""]
        for sid in list(frozen) + unmatched:
            reason = frozen.get(sid, "no section with this heading in the document")
            lines += [f"## {sid}", f"_Not applied: {reason}._", "", wanted[sid]["raw"], ""]
        write_text_file(proposals, "\n".join(lines))
    return {"out": str(out), "sidecar": str(side), **identity, "parent_build_id": parent_build_id,
            "written": written, "frozen": frozen, "unmatched": unmatched,
            **structure, "missing_fields": missing_fields,
            "protected_fields": protected_fields, "proposals": str(proposals) if frozen or unmatched else None,
            "warnings": warnings,
            "complete": missing_sections == [] and not (warnings or unmatched or frozen or missing_fields or protected_fields),
            "sha256": file_sha256(out)}


def receipt_path(out):
    out = Path(out).resolve()
    return out.parent / f".{out.name}.build" / "receipt.json"


def request_digest(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()


def publish_receipt(receipt, path, resumed):
    """Check every staged byte and destination before repairing any published files."""
    result = receipt.get("result")
    out = Path(receipt["request"]["out"])
    if (not isinstance(result, dict) or result.get("out") != str(out)
            or result.get("sidecar") != str(sidecar_path(out))
            or result.get("proposals") not in (None, str(out.with_suffix(".proposals.md")))):
        raise Refuse("invalid build recovery receipt paths")
    expected = [str(out), str(sidecar_path(out))] + ([result["proposals"]] if result["proposals"] else [])
    outputs = receipt.get("outputs")
    if (type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1
            or not isinstance(outputs, list) or not all(isinstance(o, dict) for o in outputs)
            or [o.get("path") for o in outputs] != expected):
        raise Refuse("invalid build recovery receipt")
    for item in outputs:
        dest, stage = Path(item["path"]), Path(item["staged"])
        if (dest.parent != path.parent.parent or stage != path.parent / dest.name
                or not stage.is_file() or file_sha256(stage) != item["sha256"]):
            raise Refuse("build recovery staged output is missing or corrupt")
        if dest.exists() and (not dest.is_file() or file_sha256(dest) != item["sha256"]):
            raise Refuse(f"{dest.name}: conflicting existing output; recovery will not overwrite it")
    staged_doc = Doc(outputs[0]["staged"])
    staged_record = read_record(outputs[1]["staged"], staged_doc)
    if staged_record["docx_sha256"] != outputs[0]["sha256"] or result.get("sha256") != outputs[0]["sha256"]:
        raise Refuse("build recovery receipt hashes do not match the staged record")
    if any(read_identity(staged_doc).get(k) != receipt.get(k) or result.get(k) != receipt.get(k)
           for k in IDENTITY_NAMES):
        raise Refuse("build recovery identity does not match staged Word")
    error = None
    try:
        for item in outputs:
            dest = Path(item["path"])
            if not dest.exists():
                publish(dest, lambda tmp, src=item["staged"]: shutil.copyfile(src, tmp))
    except OSError as exc:
        error = str(exc)
    published = [o["path"] for o in outputs if Path(o["path"]).is_file()
                 and file_sha256(o["path"]) == o["sha256"]]
    pending = [o["path"] for o in outputs if o["path"] not in published]
    return {**result, "receipt": str(path), "resumed": resumed, "published": published, "pending": pending,
            "status": "partial_publication" if pending else "published",
            "complete": result["complete"] and not pending,
            **({"error": error, "recovery": "retry the identical build request"} if error else {})}


def build(base, content, out, mode="normal", template=None, fields=None, protect=(), record=None, deal_id=None):
    """Stage the entire validated handoff, then publish or resume its exact bytes."""
    out = Path(out).resolve()
    path = receipt_path(out)
    paths = {"base": base, "content": content}
    if template:
        paths["template"] = template
    if record or mode == "normal" and sidecar_path(base).exists():
        paths["record"] = record or sidecar_path(base)
    request = {"out": str(out), "mode": mode, "fields": fields, "protect": sorted(protect), "deal_id": deal_id,
               "record": str(Path(record).resolve()) if record else None,
               "inputs": {key: {"path": str(Path(p).resolve()), "sha256": file_sha256(p)}
                          for key, p in paths.items()}}
    digest = request_digest(request)
    if path.exists():
        receipt = read_json(path)
        if (not isinstance(receipt, dict) or receipt.get("request_sha256") != digest
                or receipt.get("request") != request):
            raise Refuse("build recovery request differs; choose a new version name")
        return publish_receipt(receipt, path, resumed=True)
    for p in (out, sidecar_path(out), out.with_suffix(".proposals.md"), path.parent):
        if p.exists():
            raise Refuse(f"{p.name} already exists; choose a new version name")
    with tempfile.TemporaryDirectory(dir=out.parent, prefix=f".{out.name}.") as tmp:
        staged = Path(tmp) / out.name
        result = _render_build(base, content, staged, mode, template, fields, protect, record, deal_id)
        # The record and proposals are checked before any user-facing output is published.
        read_record(sidecar_path(staged), Doc(staged))
        names = [staged.name, sidecar_path(staged).name]
        if result["proposals"]:
            read_text(result["proposals"])
            names.append(Path(result["proposals"]).name)
        result.update(out=str(out), sidecar=str(sidecar_path(out)),
                      proposals=str(out.with_suffix(".proposals.md")) if result["proposals"] else None)
        receipt = {"schema_version": 1, "request_sha256": digest, "request": request,
                   **{key: result[key] for key in (*IDENTITY_NAMES, "parent_build_id")}, "result": result,
                   "outputs": [{"path": str(out.parent / name), "staged": str(path.parent / name),
                                "sha256": file_sha256(Path(tmp) / name)} for name in names]}
        write_text_file(Path(tmp) / "receipt.json", json.dumps(receipt, indent=1))
        os.rename(tmp, path.parent)
    return publish_receipt(receipt, path, resumed=False)


# ---------- inspect and check ----------

def inspect(path):
    doc = Doc(path)
    inc = doc.incidental
    baseline = load_sidecar(path)["sections"]
    sigs = signatures(doc)
    comments = doc.comments()
    sections = []
    for sec in doc.sections:
        b = baseline.get(sec["id"], {})
        info = {"id": sec["id"], "heading": sec["heading"], "level": sec["level"],
                "owner": b.get("owner", "unknown"),
                "changed_since_build": bool(b) and b.get("signature") != sigs[sec["id"]],
                **flags(sec, inc)}
        sections.append(info)
    where = {cid: s["id"] for s in doc.sections for cid in section_comment_ids(s)}
    return {"file": str(path), "sha256": file_sha256(path), "identity": read_identity(doc), "sections": sections,
            "comments": [{"id": cid, "section": where.get(cid), **c} for cid, c in comments.items()]}


def to_markdown(path):
    doc = Doc(path)
    inc = doc.incidental
    lines = []
    for sec in doc.sections:
        lines += [f"## {sec['id']}", ""]
        fixed_no = 0
        for k in sec["body"]:
            if is_fixed(k, inc):
                fixed_no += 1
                lines.append(f"{{{{keep:{fixed_no}}}}}")
                if k.tag == "tbl":  # readable for reviewers; build ignores <!-- --> notes
                    lines.append("<!-- kept table, read-only:")
                    lines += ["| " + " | ".join(c.plain() for c in tr.kids if c.tag == "tc") + " |"
                              for tr in k.kids if tr.tag == "tr"]
                    lines.append("-->")
                elif k.plain().strip():
                    lines.append(f"<!-- kept, read-only: {k.plain().strip()} -->")
                lines.append("")
            elif k.tag == "tbl":
                for tr in (r for r in k.kids if r.tag == "tr"):
                    lines.append("| " + " | ".join(c.plain() for c in tr.kids if c.tag == "tc") + " |")
                lines.append("")
            elif k.plain().strip():
                ps = k.find("pPr", "pStyle")
                name = doc.styles.get(ps.wattr("val"), ("",))[0] if ps is not None else ""
                prefix = "- " if "list" in name.lower() else ""
                lines += [prefix + k.plain().strip(), ""]
    comments = inspect(path)["comments"]
    if comments:  # a read-only note, so feeding this text back to build adds no section
        lines.append("<!-- comments, read-only (not part of the FP):")
        lines += [f"- [{c['section']}] {c['author']}: {c['text']}".replace("-->", "- ->") for c in comments]
        lines.append("-->")
    return "\n".join(lines).rstrip() + "\n"


def compare_headings(doc, tpl):
    missing, order, levels, problems = None, None, None, []
    if tpl:
        actual = {s["id"]: s["level"] for s in doc.sections}
        expected = {s["id"]: s["level"] for s in tpl.sections}
        missing = [sid for sid in expected if sid not in actual]
        order = [sid for sid in actual if sid in expected] == [sid for sid in expected if sid in actual]
        levels = [sid for sid in expected if sid in actual and expected[sid] != actual[sid]]
        if not order:
            problems.append("template heading order differs")
        if levels:
            problems.append("template heading levels differ: " + ", ".join(levels))
    return {"missing_sections": missing, "heading_order_matches": order,
            "heading_level_mismatches": levels, "heading_problems": problems}


def check(path, template=None):
    problems = []
    doc = Doc(path)
    text = "\n".join(k.plain() for k in doc.body.kids)
    if TAG.search(text):
        problems.append("source tags left in the text")
    if "{{keep:" in text:
        problems.append("unplaced {{keep:N}} markers left in the text")
    tpl = Doc(template) if template else None
    structure = compare_headings(doc, tpl)
    problems.extend(structure["heading_problems"])
    if tpl:
        missing = structure["missing_sections"]
        if missing:
            problems.append(f"template sections missing or renamed: {', '.join(missing)}")
        by_id = {s["id"]: s for s in doc.sections}
        for s in tpl.sections:
            guidance = " ".join(k.plain() for k in s["body"]).strip()
            mine = by_id.get(s["id"])
            if guidance and mine and " ".join(k.plain() for k in mine["body"]).strip() == guidance:
                problems.append(f"{s['id']}: still contains the template's guidance text")
    info = inspect(path)
    return {"file": str(path), "problems": problems, **structure,
            "writer_limits": ["missing headings are not inserted", "predefined tables are preserved, not populated",
                              "comments, tracked changes and fixed structures are preserved"],
            "protected_structures": [{"section": s["id"], "fixed_objects": s["fixed_objects"],
                                      "comments": s["has_comments"], "tracked_changes": s["has_tracked_changes"]}
                                     for s in info["sections"] if s["fixed_objects"] or s["has_comments"]
                                     or s["has_tracked_changes"]],
            "sections_with_comments": [s["id"] for s in info["sections"] if s["has_comments"]],
            "sections_with_tracked_changes": [s["id"] for s in info["sections"] if s["has_tracked_changes"]]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("inspect")
    a.add_argument("docx")
    a.add_argument("--markdown", action="store_true")
    b = sub.add_parser("build")
    b.add_argument("--base", required=True)
    b.add_argument("--content", required=True)
    b.add_argument("--out", required=True)
    m = b.add_mutually_exclusive_group()
    m.add_argument("--first", action="store_true")
    m.add_argument("--existing", action="store_true")
    b.add_argument("--template")
    b.add_argument("--fields")
    b.add_argument("--protect", default="", help="comma-separated section ids to keep as they are")
    b.add_argument("--deal-id", help="deal identity for a first/imported build; inherited on revisions")
    b.add_argument("--record", help="the source version's record, for a renamed copy (normal rounds)")
    f = sub.add_parser("find-record")
    f.add_argument("docx")
    f.add_argument("--folder")
    c = sub.add_parser("check")
    c.add_argument("docx")
    c.add_argument("--template")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "inspect":
            print(to_markdown(args.docx) if args.markdown else json.dumps(inspect(args.docx), indent=1))
        elif args.cmd == "build":
            fields = read_json(args.fields) if args.fields else None
            mode = "first" if args.first else "existing" if args.existing else "normal"
            protect = [s.strip() for s in args.protect.split(",") if s.strip()]
            result = build(args.base, args.content, args.out, mode, args.template, fields, protect, args.record, args.deal_id)
            print(json.dumps(result, indent=1))
            if result["status"] == "partial_publication":
                return 2
        elif args.cmd == "find-record":
            print(json.dumps(find_record(args.docx, args.folder), indent=1))
        elif args.cmd == "check":
            result = check(args.docx, args.template)
            print(json.dumps(result, indent=1))
            return 1 if result["problems"] else 0
    except (Refuse, KeyError, ValueError, zipfile.BadZipFile, expat.ExpatError, ET.ParseError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
