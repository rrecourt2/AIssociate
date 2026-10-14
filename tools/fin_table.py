#!/usr/bin/env python3
"""Turn the spreading export into the FP's financial table, with traceable sources.

  fin_table.py SPREAD.xlsx MAPPING.json [--json OUT.json]

Prints a Markdown table for the FP text draft. Every value is either copied from a named
cell or computed by one of four formulas: {A} / {B}, {A} - {B}, {A} + {B}, growth({A}).
Require "identity" for entity, reporting perimeter and currency/scale. Each entry is
{value, cell} in the selected sheet, or {value, basis, reviewed_by} when metadata is absent.
"unit" must agree with identity.unit.value; no currency or scale conversion is performed.
Optional "expect" checks other cells. Labels or periods that appear twice are refused.
Formula cells in the selected sheet are refused unless "trust_formula_values" is true
and "recalculation_basis" records who recalculated and saved it, when, and with which tool.
The output records the export path/hash, checked identity cells, and this trust basis.
Standard library only. The mapping is set up once per spreading-export layout:

  {"sheet": "Spread", "label_column": "A", "header_row": 1, "unit": "EUR m",
   "identity": {"entity": {"value": "Example Group", "cell": "E1"},
                "perimeter": {"value": "consolidated", "cell": "E2"},
                "unit": {"value": "EUR m", "cell": "A1"}},
   "expect": {"B1": "FY2024"},
   "periods": ["FY2024", "FY2025"],
   "rows": [{"label": "Revenue", "source": "Total revenue"},
            {"label": "EBITDA", "source": "EBITDA"},
            {"label": "EBITDA margin", "formula": "{EBITDA} / {Revenue}", "format": "pct"}]}
"""
import argparse
import hashlib
import json
import math
import os
import posixpath
import re
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from io import BytesIO

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
FORMULA = re.compile(r"^\s*(?:growth\(\{(?P<g>[^}]+)\}\)|\{(?P<a>[^}]+)\}\s*(?P<op>[-+/])\s*\{(?P<b>[^}]+)\})\s*$")


class TableError(Exception):
    """The table cannot be built as specified; nothing is guessed."""


def norm(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def read_sheet(path, name):
    """({"B7": value}, {cells holding formulas}) for one worksheet; numbers as float, text as str."""
    with zipfile.ZipFile(path) as z:
        sheets = {s.get("name"): s.get(REL + "id") for s in ET.fromstring(z.read("xl/workbook.xml")).iter(MAIN + "sheet")}
        if name not in sheets:
            raise TableError(f"no sheet {name!r}; the workbook has {sorted(sheets)}")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relation = next((r for r in rels if r.get("Id") == sheets[name]), None)
        if relation is None or relation.get("TargetMode") == "External":
            raise TableError(f"sheet {name!r} has no local worksheet part")
        target = relation.get("Target", "")
        part = posixpath.normpath(target.lstrip("/") if target.startswith("/") else "xl/" + target)
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = ["".join(t.text or "" for t in si.iter(MAIN + "t"))
                      for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(MAIN + "si")]
        cells, formulas = {}, set()
        for c in ET.fromstring(z.read(part)).iter(MAIN + "c"):
            if c.find(MAIN + "f") is not None:
                formulas.add(c.get("r"))
            kind, v = c.get("t"), c.find(MAIN + "v")
            if kind == "s":
                value = shared[int(v.text)]
            elif kind == "inlineStr":
                value = "".join(t.text or "" for t in c.iter(MAIN + "t"))
            elif kind in ("str", "e"):
                value = v.text if v is not None else ""
            elif kind == "b":
                value = v is not None and v.text == "1"
            else:
                value = float(v.text) if v is not None and v.text else None
            cells[c.get("r")] = value
    return cells, formulas


def split_ref(ref):
    m = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    if not m:
        raise TableError(f"invalid cell reference {ref!r}")
    return m.group(1), int(m.group(2))


def compute(expr, values):
    m = FORMULA.match(expr)
    if not m:
        raise TableError(f"unsupported formula {expr!r}; use {{A}} / {{B}}, {{A}} - {{B}}, {{A}} + {{B}} or growth({{A}})")
    for name in filter(None, (m["g"], m["a"], m["b"])):
        if name not in values:
            raise TableError(f"formula {expr!r} uses {name!r}, which is not an earlier row")
    if m["g"]:
        a = values[m["g"]]
        return [None] + [(cur - prev) / prev if prev and prev > 0 and cur is not None else None
                         for prev, cur in zip(a, a[1:])]
    out = []
    for x, y in zip(values[m["a"]], values[m["b"]]):
        if x is None or y is None or (m["op"] == "/" and not y):
            out.append(None)
        else:
            out.append(x / y if m["op"] == "/" else x - y if m["op"] == "-" else x + y)
    return out


def build_table(spread, mapping):
    if not isinstance(mapping, dict):
        raise TableError("mapping must be a JSON object")
    for key in ("sheet", "label_column", "header_row", "periods", "rows", "identity", "unit"):
        if key not in mapping:
            raise TableError(f"mapping requires {key}")
    periods = mapping["periods"]
    specs = mapping["rows"]
    if not isinstance(periods, list) or not periods or any(not norm(p) for p in periods):
        raise TableError("periods must be a nonempty list")
    if len({norm(p) for p in periods}) != len(periods):
        raise TableError("duplicate periods in mapping")
    if not isinstance(specs, list):
        raise TableError("rows must be a list")
    output_labels = set()
    for spec in specs:
        if not isinstance(spec, dict) or not isinstance(spec.get("label"), str) or not spec["label"].strip():
            raise TableError("each row needs a nonempty label")
        if norm(spec["label"]) in output_labels:
            raise TableError(f"duplicate row label {spec['label']!r} in mapping")
        output_labels.add(norm(spec["label"]))
        if ("source" in spec) == ("formula" in spec):
            raise TableError(f"{spec['label']}: specify exactly one source or formula")
        if spec.get("format", "num") not in ("num", "pct", "x"):
            raise TableError(f"{spec['label']}: unsupported format")
    sheet = mapping["sheet"]
    export_bytes = Path(spread).read_bytes()
    cells, formulas = read_sheet(BytesIO(export_bytes), sheet)
    trust = mapping.get("trust_formula_values", False)
    basis = mapping.get("recalculation_basis", "")
    if type(trust) is not bool:
        raise TableError("trust_formula_values must be true or false")
    if formulas and not trust:
        raise TableError("selected sheet holds formulas; use a values-only export, or set trust_formula_values "
                         "with a recorded recalculation_basis after recalculating and saving")
    if trust and (not isinstance(basis, str) or not basis.strip()):
        raise TableError("trust_formula_values requires a nonempty recalculation_basis")
    identity = mapping["identity"]
    if not isinstance(identity, dict) or set(identity) != {"entity", "perimeter", "unit"}:
        raise TableError("identity requires exactly entity, perimeter and unit")
    for field, entry in identity.items():
        if not isinstance(entry, dict) or set(entry) not in ({"value", "cell"}, {"value", "basis", "reviewed_by"}):
            raise TableError(f"identity.{field} requires {{value, cell}} or {{value, basis, reviewed_by}}")
        if any(not isinstance(value, str) or not value.strip() for value in entry.values()):
            raise TableError(f"identity.{field} fields must be nonempty strings")
        if "cell" in entry:
            ref = entry["cell"]
            if not re.fullmatch(r"[A-Z]+[1-9]\d*", ref):
                raise TableError(f"identity.{field} requires a cell reference in the selected sheet")
            actual = cells.get(ref)
            if not isinstance(actual, str) or not actual.strip() or norm(actual) != norm(entry["value"]):
                raise TableError(f"identity.{field}: {sheet}!{ref} holds {actual!r}, expected {entry['value']!r}")
    unit = mapping["unit"]
    if not isinstance(unit, str) or not unit.strip() or norm(unit) != norm(identity["unit"]["value"]):
        raise TableError("unit must agree with identity.unit.value, including currency and scale; no conversion is performed")
    wrong = [f"{ref} holds {cells.get(ref)!r}, expected {want!r}" for ref, want in mapping.get("expect", {}).items()
             if norm(cells.get(ref, "")) != norm(want)]
    if wrong:
        raise TableError("this is not the expected export: " + "; ".join(wrong))
    label_col, header_row = mapping["label_column"].upper(), int(mapping["header_row"])
    label_rows, header_cols = {}, {}
    for ref, value in cells.items():
        col, row = split_ref(ref)
        if col == label_col and isinstance(value, str) and value.strip():
            label_rows.setdefault(norm(value), []).append(row)
        if row == header_row and value not in (None, ""):
            header_cols.setdefault(norm(value), []).append(col)
    sources = [r["source"] for r in mapping["rows"] if "source" in r]
    missing = [f"period {p!r}" for p in periods if norm(p) not in header_cols]
    missing += [f"row {s!r}" for s in sources if norm(s) not in label_rows]
    if missing:
        raise TableError("not found in the spreading export: " + ", ".join(missing))
    twice = [f"period {p!r}" for p in periods if len(header_cols[norm(p)]) > 1]
    twice += [f"row {s!r}" for s in sources if len(label_rows[norm(s)]) > 1]
    if twice:
        raise TableError("ambiguous in the spreading export (appears more than once): " + ", ".join(twice))
    labels = {k: v[0] for k, v in label_rows.items()}
    headers = {k: v[0] for k, v in header_cols.items()}
    values, rows = {}, []
    for spec in mapping["rows"]:
        row = {"label": spec["label"], "format": spec.get("format", "num")}
        if "source" in spec:
            r = labels[norm(spec["source"])]
            refs = [f"{headers[norm(p)]}{r}" for p in periods]
            vals = [cells.get(ref) for ref in refs]
            wrong = [ref for ref, v in zip(refs, vals) if v is not None
                     and (not isinstance(v, float) or not math.isfinite(v))]
            if wrong:
                raise TableError(f"{spec['label']}: cells {wrong} are not numbers")
            if any(ref in formulas and v is None for ref, v in zip(refs, vals)):
                raise TableError(f"{spec['label']}: a formula cell has no stored value; recalculate and save the export")
            row.update(values=vals, source=[f"{sheet}!{ref}" for ref in refs])
        else:
            row.update(values=compute(spec["formula"], values), formula=spec["formula"])
        values[spec["label"]] = row["values"]
        rows.append(row)
    return {"unit": unit, "identity": identity, "periods": [str(p) for p in periods], "rows": rows,
            "export": {"path": str(Path(spread).resolve()), "sha256": hashlib.sha256(export_bytes).hexdigest(),
                       "sheet": sheet, "expect": mapping.get("expect", {}), "formula_cells": sorted(formulas),
                       "trust_formula_values": trust, "recalculation_basis": basis if trust else ""},
            "mapping_sha256": hashlib.sha256(json.dumps(mapping, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def fmt(value, kind):
    if value is None:
        return "n/a"
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "x":
        return f"{value:.1f}x"
    return f"{value:,.1f}"


def markdown(table):
    lines = ["| " + " | ".join([table["unit"]] + table["periods"]) + " |",
             "|---|" + "---:|" * len(table["periods"])]
    lines += ["| " + " | ".join([r["label"]] + [fmt(v, r["format"]) for v in r["values"]]) + " |"
              for r in table["rows"]]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spread", help="spreading export (.xlsx)")
    ap.add_argument("mapping")
    ap.add_argument("--json", help="also write the table with its sources to this file")
    args = ap.parse_args(argv)
    try:
        if args.json:
            out = Path(args.json)
            if out.resolve() in (Path(args.spread).resolve(), Path(args.mapping).resolve()):
                raise TableError("output must not overwrite an input")
            if out.exists() or out.is_symlink():
                raise TableError(f"output already exists: {out}")
        mapping_bytes = Path(args.mapping).read_bytes()
        table = build_table(args.spread, json.loads(mapping_bytes))
        table["mapping_path"] = str(Path(args.mapping).resolve())
        table["mapping_sha256"] = hashlib.sha256(mapping_bytes).hexdigest()
        md = markdown(table)
        if args.json:
            # Publish a complete file without clobbering an output created since the check.
            fd, tmp = tempfile.mkstemp(dir=out.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(table, f, indent=1, allow_nan=False)
                os.link(tmp, out)
            finally:
                os.unlink(tmp)
        print(md)
    except (TableError, KeyError, ValueError, TypeError, zipfile.BadZipFile, ET.ParseError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
