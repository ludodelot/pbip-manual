#!/usr/bin/env python3
"""Validate content.json against extract.json.

Usage: python validate_content.py extract.json content.json [--langs en,es,it,fr]
Exit code 1 if there are errors (warnings do not fail).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FICHA_FIELDS = ["use_it_when", "source", "refresh", "granularity", "main_kpi", "comparison"]
MAX_LEN = {"headline": 90, "use_it_when": 160, "source": 120, "refresh": 80,
           "granularity": 100, "main_kpi": 100, "comparison": 120, "zone_text": 150}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def validate(extract: dict, content: dict, langs: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    for lang in langs:
        if lang not in content.get("languages", []):
            errors.append(f"language '{lang}' not declared in content.languages")
        if lang not in content.get("title", {}):
            errors.append(f"title missing for '{lang}'")
    cpages = content.get("pages", {})
    for page in extract["pages"]:
        pid = page["id"]
        if page["kind"] in ("tooltip",):
            continue
        if pid not in cpages:
            errors.append(f"page {pid} ({page['name']}): no content")
            continue
        c = cpages[pid]
        vids = {v["id"] for v in page["visuals"]}
        for lang in langs:
            L = c.get("text", {}).get(lang)
            if not L:
                errors.append(f"page {pid}: missing text for '{lang}'")
                continue
            if not L.get("headline"):
                errors.append(f"page {pid}/{lang}: headline empty")
            for f in FICHA_FIELDS:
                val = L.get(f)
                if not val:
                    errors.append(f"page {pid}/{lang}: '{f}' empty")
                elif val.strip().upper() == "TBD":
                    warns.append(f"page {pid}/{lang}: '{f}' is TBD")
                elif len(val) > MAX_LEN[f]:
                    warns.append(f"page {pid}/{lang}: '{f}' is {len(val)} chars (max {MAX_LEN[f]}); may overflow")
            if len(L.get("headline", "")) > MAX_LEN["headline"]:
                warns.append(f"page {pid}/{lang}: headline too long")
        zones = c.get("zones", [])
        if not zones:
            errors.append(f"page {pid}: no zones")
        nums = [z.get("n") for z in zones]
        if nums != list(range(1, len(zones) + 1)):
            errors.append(f"page {pid}: zone numbers must be 1..N in order, got {nums}")
        for z in zones:
            has_rect = isinstance(z.get("rect"), list) and len(z["rect"]) == 4
            has_vis = bool(z.get("visuals"))
            if not (has_rect or has_vis):
                errors.append(f"page {pid} zone {z.get('n')}: needs 'rect' [x,y,w,h] or 'visuals' [ids]")
            for vid in z.get("visuals", []):
                if vid not in vids:
                    errors.append(f"page {pid} zone {z.get('n')}: unknown visual id '{vid}'")
            for lang in langs:
                t = z.get("text", {}).get(lang)
                if not t:
                    errors.append(f"page {pid} zone {z.get('n')}: missing text for '{lang}'")
                elif len(t) > MAX_LEN["zone_text"]:
                    warns.append(f"page {pid} zone {z.get('n')}/{lang}: {len(t)} chars; may overflow")
        if len(zones) > 8:
            warns.append(f"page {pid}: {len(zones)} zones; the list may not fit, consider merging")
    known = {p["id"] for p in extract["pages"]}
    for pid in cpages:
        if pid not in known:
            warns.append(f"content has page '{pid}' not present in extract")
    return errors, warns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extract")
    ap.add_argument("content")
    ap.add_argument("--langs", default="en,es,it,fr")
    a = ap.parse_args(argv)
    errors, warns = validate(load(a.extract), load(a.content), a.langs.split(","))
    for w in warns:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
