#!/usr/bin/env python3
"""Read-only extractor for Power BI PBIP projects (PBIR report + TMDL model).

Usage:
    python extract_report.py <project_dir> [--out extract.json]

<project_dir> contains <name>.Report/ and <name>.SemanticModel/ (or is one of them).
Standard library only. Never writes inside the project folder.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FAMILIES = {
    "kpi": {"card", "multiRowCard", "kpi", "gauge", "cardVisual", "advancedSlicerVisual"},
    "chart": {
        "clusteredBarChart", "clusteredColumnChart", "stackedBarChart", "stackedColumnChart",
        "hundredPercentStackedBarChart", "hundredPercentStackedColumnChart", "lineChart",
        "areaChart", "stackedAreaChart", "lineClusteredColumnComboChart",
        "lineStackedColumnComboChart", "ribbonChart", "waterfallChart", "funnel",
        "pieChart", "donutChart", "treemap", "scatterChart", "map", "filledMap", "shapeMap",
        "azureMap", "decompositionTreeVisual", "keyDriversVisual",
    },
    "table": {"tableEx", "pivotTable", "table", "matrix"},
    "filter": {"slicer", "chicletSlicer", "timeBrief"},
    "text": {"textbox", "shape", "image", "actionButton", "basicShape", "pageNavigator", "bookmarkNavigator"},
}


def family_of(visual_type: str) -> str:
    for fam, types in FAMILIES.items():
        if visual_type in types:
            return fam
    return "other"


def read_json(path: Path):
    # utf-8-sig tolerates a BOM, which some tools write.
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def find_dir(root: Path, suffix: str) -> Path | None:
    if root.name.endswith(suffix):
        return root
    hits = sorted(p for p in root.iterdir() if p.is_dir() and p.name.endswith(suffix))
    return hits[0] if hits else None


def literal(node) -> str | None:
    """Pull a string out of {'expr': {'Literal': {'Value': "'text'"}}} shapes."""
    if isinstance(node, dict):
        if "Literal" in node:
            val = node["Literal"].get("Value")
            if isinstance(val, str) and len(val) >= 2 and val[0] == "'" and val[-1] == "'":
                return val[1:-1].replace("''", "'")
            return val
        for v in node.values():
            found = literal(v)
            if found is not None:
                return found
    elif isinstance(node, list):
        for v in node:
            found = literal(v)
            if found is not None:
                return found
    return None


def find_key(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for v in node.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def field_info(field: dict, role: str) -> dict:
    kind = next(iter(field), "Unknown")
    entity = find_key(field, "Entity")
    prop = find_key(field, "Property")
    if kind == "Aggregation":
        kind = "Aggregation"
    return {"kind": kind, "entity": entity, "name": prop, "role": role}


def visual_title(vis: dict) -> str | None:
    container = vis.get("visual", {}).get("visualContainerObjects", {}).get("title")
    if container:
        props = container[0].get("properties", {})
        if "text" in props:
            return literal(props["text"])
    legacy = vis.get("visual", {}).get("objects", {}).get("title")
    if legacy:
        props = legacy[0].get("properties", {})
        if "text" in props:
            return literal(props["text"])
    return None


def textbox_text(vis: dict) -> str | None:
    general = vis.get("visual", {}).get("objects", {}).get("general")
    if not general:
        return None
    paragraphs = general[0].get("properties", {}).get("paragraphs", [])
    parts = []
    for para in paragraphs:
        for run in para.get("textRuns", []):
            if run.get("value"):
                parts.append(run["value"])
    return " ".join(parts) or None


def parse_visual(path: Path) -> dict:
    vis = read_json(path)
    pos = vis.get("position", {})
    v = vis.get("visual", {})
    vtype = v.get("visualType") or ("group" if "visualGroup" in vis else "unknown")
    fields = []
    for role, state in (v.get("query", {}).get("queryState", {}) or {}).items():
        for proj in state.get("projections", []):
            if "field" in proj:
                fields.append(field_info(proj["field"], role))
    title = visual_title(vis)
    if vtype == "group":
        title = title or vis.get("visualGroup", {}).get("displayName")
    out = {
        "id": vis.get("name", path.parent.name),
        "type": vtype,
        "family": family_of(vtype),
        "x": pos.get("x", 0), "y": pos.get("y", 0),
        "w": pos.get("width", 0), "h": pos.get("height", 0),
        "z": pos.get("z", 0),
        "title": title,
        "hidden": bool(vis.get("isHidden", False)),
        "parent": vis.get("parentGroupName"),
        "fields": fields,
    }
    if vtype == "textbox":
        out["text"] = textbox_text(vis)
    return out


def parse_pages(report_def: Path) -> list[dict]:
    pages_dir = report_def / "pages"
    if not pages_dir.is_dir():
        raise SystemExit(
            f"No PBIR 'pages' folder in {report_def}. Legacy report.json reports are not supported: "
            "open the report in Power BI Desktop, enable PBIR, and save as PBIP."
        )
    order = []
    idx = pages_dir / "pages.json"
    if idx.exists():
        order = read_json(idx).get("pageOrder", [])
    folders = {p.name: p for p in pages_dir.iterdir() if p.is_dir()}
    ids = [i for i in order if i in folders] + sorted(i for i in folders if i not in order)
    pages = []
    for pid in ids:
        pj = folders[pid] / "page.json"
        meta = read_json(pj) if pj.exists() else {}
        binding = (meta.get("pageBinding") or {}).get("type")
        visuals = []
        vdir = folders[pid] / "visuals"
        if vdir.is_dir():
            for vf in sorted(vdir.iterdir()):
                vj = vf / "visual.json"
                if vj.exists():
                    visuals.append(parse_visual(vj))
        kind = "tooltip" if binding == "Tooltip" else "drillthrough" if binding == "Drillthrough" else "standard"
        if meta.get("visibility") == "HiddenInViewMode" and kind == "standard":
            kind = "hidden"
        fam_count: dict[str, int] = {}
        for v in visuals:
            if not v["hidden"] and v["type"] != "group":
                fam_count[v["family"]] = fam_count.get(v["family"], 0) + 1
        pages.append({
            "id": pid,
            "name": meta.get("displayName", pid),
            "kind": kind,
            "width": meta.get("width", 1280),
            "height": meta.get("height", 720),
            "visuals": visuals,
            "families": fam_count,
        })
    return pages


# ---------------------------------------------------------------- TMDL ----

IDENT = r"(?:'(?:[^']|'')+'|[^\s=]+)"


def indent_of(line: str) -> int:
    n = 0
    for ch in line:
        if ch == "\t":
            n += 1
        elif ch == " ":
            n += 0.25
        else:
            break
    return int(n)


def unquote(name: str) -> str:
    name = name.strip()
    if name.startswith("'") and name.endswith("'"):
        return name[1:-1].replace("''", "'")
    return name


def parse_tmdl_table(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    table = {"name": path.stem, "mode": None, "source_hint": None, "measures": []}
    pending_doc: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if s.startswith("///"):
            pending_doc.append(s[3:].strip())
            i += 1
            continue
        m_table = re.match(rf"^table\s+({IDENT})", s)
        if m_table and indent_of(raw) == 0:
            table["name"] = unquote(m_table.group(1))
            pending_doc = []
        m_mode = re.match(r"^mode:\s*(\w+)", s)
        if m_mode:
            table["mode"] = m_mode.group(1)
        m_src = re.search(r"\b(Sql\.Database|Sql\.Databases|Excel\.Workbook|Csv\.Document|SharePoint\.\w+|"
                          r"OData\.Feed|Web\.Contents|Snowflake\.Databases|GoogleBigQuery\.\w+|"
                          r"AzureStorage\.\w+|Lakehouse\.Contents|Databricks\.\w+)\(", s)
        if m_src and not table["source_hint"]:
            table["source_hint"] = m_src.group(1)
        m_meas = re.match(rf"^measure\s+({IDENT})\s*(?:=\s*(.*))?$", s)
        if m_meas:
            base = indent_of(raw)
            meas = {
                "name": unquote(m_meas.group(1)),
                "description": " ".join(pending_doc).strip() or None,
                "expression": "",
                "format": None,
                "folder": None,
            }
            pending_doc = []
            first = (m_meas.group(2) or "").strip()
            in_fence = first.startswith("```")
            expr_lines = [first] if first and not in_fence else []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                ns = nxt.strip()
                if in_fence:
                    if ns.startswith("```"):
                        in_fence = False
                    else:
                        expr_lines.append(ns)
                    i += 1
                    continue
                if ns == "":
                    i += 1
                    continue
                if ns.startswith("```"):
                    in_fence = True
                    i += 1
                    continue
                ind = indent_of(nxt)
                if ind >= base + 2:
                    expr_lines.append(ns)
                    i += 1
                    continue
                if ind == base + 1:
                    mp = re.match(r"^(\w+)\s*:\s*(.*)$", ns)
                    if mp:
                        key, val = mp.group(1), mp.group(2)
                        if key == "formatString":
                            meas["format"] = val.strip('"')
                        elif key == "displayFolder":
                            meas["folder"] = val
                        elif key == "description" and not meas["description"]:
                            meas["description"] = val
                        i += 1
                        continue
                    if ns.startswith("///"):
                        break
                break
            meas["expression"] = "\n".join(e for e in expr_lines if e).strip()
            table["measures"].append(meas)
            continue
        if s and re.match(r"^(column|partition|hierarchy)\b", s):
            pending_doc = []
        i += 1
    return table


def parse_model(model_def: Path) -> dict:
    tables = []
    tdir = model_def / "tables"
    if tdir.is_dir():
        for tf in sorted(tdir.glob("*.tmdl")):
            tables.append(parse_tmdl_table(tf))
    return {"tables": tables}


def report_extension_measures(report_def: Path) -> list[dict]:
    ext = report_def / "reportExtensions.json"
    out = []
    if ext.exists():
        for ent in read_json(ext).get("entities", []):
            for m in ent.get("measures", []):
                out.append({"table": ent.get("name"), "name": m.get("name"),
                            "expression": m.get("expression", ""), "description": None,
                            "format": None, "folder": None, "origin": "report"})
    return out


def build(project: Path) -> dict:
    report_dir = find_dir(project, ".Report")
    if report_dir is None:
        raise SystemExit(f"No *.Report folder found under {project}")
    rdef = report_dir / "definition"
    if not rdef.is_dir():
        raise SystemExit(f"{report_dir} has no 'definition' folder (not PBIR).")
    model_dir = find_dir(project if project.name.endswith(".Report") is False else project.parent, ".SemanticModel")
    model = {"tables": []}
    if model_dir and (model_dir / "definition").is_dir():
        model = parse_model(model_dir / "definition")
    pages = parse_pages(rdef)

    index = {}
    for t in model["tables"]:
        for m in t["measures"]:
            index[(t["name"], m["name"])] = {**m, "table": t["name"], "origin": "model"}
    for m in report_extension_measures(rdef):
        index[(m["table"], m["name"])] = m

    used: dict[str, dict] = {}
    for p in pages:
        for v in p["visuals"]:
            for f in v["fields"]:
                if f["kind"] == "Measure" or (f["entity"], f["name"]) in index:
                    key = (f["entity"], f["name"])
                    info = index.get(key)
                    label = f"{f['entity']}.{f['name']}"
                    entry = used.setdefault(label, {
                        "table": f["entity"], "name": f["name"],
                        "description": info["description"] if info else None,
                        "expression": info["expression"] if info else None,
                        "format": info["format"] if info else None,
                        "folder": info["folder"] if info else None,
                        "found": info is not None, "pages": [],
                    })
                    if p["id"] not in entry["pages"]:
                        entry["pages"].append(p["id"])
    return {
        "report": report_dir.name[: -len(".Report")],
        "pages": pages,
        "model": {"tables": [{"name": t["name"], "mode": t["mode"], "source_hint": t["source_hint"],
                              "measure_count": len(t["measures"])} for t in model["tables"]]},
        "measures_used": used,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("--out", type=Path, default=Path("extract.json"))
    args = ap.parse_args(argv)
    data = build(args.project.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    n_vis = sum(len(p["visuals"]) for p in data["pages"])
    print(f"{data['report']}: {len(data['pages'])} pages, {n_vis} visuals, "
          f"{len(data['measures_used'])} measures used -> {args.out}")
    missing = [k for k, v in data["measures_used"].items() if not v["found"]]
    if missing:
        print(f"warning: measures not found in TMDL: {', '.join(missing)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
