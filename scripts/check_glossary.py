#!/usr/bin/env python3
"""Terminology consistency check across EN/ES/IT/FR.

Usage: python check_glossary.py glossary.json content.json [--langs en,es,it,fr]

For every glossary term whose English form appears in an English text, the
same text in each other language must contain that language's canonical form.
Forbidden variants (glossary 'avoid' lists) are errors in any text.
Matching is case-insensitive and accent-sensitive.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def contains(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text.lower()) is not None


def texts_by_item(content: dict, langs):
    """Yield (item_id, {lang: text}) pairs for every translatable string."""
    for pid, page in content.get("pages", {}).items():
        by_field: dict[str, dict] = {}
        for lang in langs:
            for field, val in page.get("text", {}).get(lang, {}).items():
                if isinstance(val, str):
                    by_field.setdefault(field, {})[lang] = val
        for field, d in by_field.items():
            yield f"{pid}/{field}", d
        for z in page.get("zones", []):
            yield f"{pid}/zone{z.get('n')}", {l: z.get("text", {}).get(l, "") for l in langs}


def check(glossary: dict, content: dict, langs: list[str]):
    errors, warns = [], []
    terms = glossary.get("terms", [])
    for t in terms:
        for lang in langs:
            if not t.get(lang):
                errors.append(f"glossary term '{t.get('en', t.get('id'))}': missing '{lang}'")
    for item, d in texts_by_item(content, langs):
        for lang, text in d.items():
            for t in terms:
                for bad in t.get("avoid", {}).get(lang, []):
                    if contains(text, bad):
                        errors.append(f"{item}/{lang}: uses '{bad}', glossary says '{t.get(lang)}'")
        en = d.get("en", "")
        for t in terms:
            if t.get("en") and contains(en, t["en"]):
                for lang in langs:
                    if lang == "en" or not d.get(lang):
                        continue
                    if t.get(lang) and not contains(d[lang], t[lang]):
                        warns.append(f"{item}/{lang}: EN uses '{t['en']}' but '{t[lang]}' not found")
    return errors, warns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("glossary")
    ap.add_argument("content")
    ap.add_argument("--langs", default="en,es,it,fr")
    a = ap.parse_args(argv)
    errors, warns = check(load(a.glossary), load(a.content), a.langs.split(","))
    for w in warns:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
