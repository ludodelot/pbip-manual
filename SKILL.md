---
name: pbip-manual
description: Generate a 16:9 end-user PDF manual (EN/ES/IT/FR) from a Power BI PBIP project (PBIR report + TMDL model). Use when the user wants a user guide, manual, page-by-page cheat sheet or glossary for a Power BI report, or asks to document report pages, visuals and measures for business users. Works fully offline with Python + reportlab.
---

# pbip-manual

Builds a visual user manual for a Power BI report from its **PBIP source files**. No Power BI Desktop, no service, no internet needed.

Each report page gets a **ficha** (one slide-style page):

1. A numbered **page diagram** (vector wireframe drawn from real visual positions, or a PNG screenshot if you provide one).
2. A numbered list of **what is in each zone**.
3. A table: *Use it when / Source / Refresh / Granularity / Main KPI / Comparison*.

The manual ends with a **glossary**. Languages: `en`, `es`, `it`, `fr`.

## Pipeline

```
PBIP project ──extract_report.py──> extract.json ──(you/Claude write)──> content.json
                                                                          │
screenshots/<pageId>.png (optional) ───────────────┐                      │
                                                   ▼                      ▼
                          validate_content.py ─> check_glossary.py ─> build_manual.py ─> manual_<lang>.pdf
```

## Workflow (follow in order)

1. **Locate the project.** Folder containing `*.pbip`, `*.Report/` and `*.SemanticModel/`. Only PBIR (folder-based `definition/pages/...`) is supported. If the report has a single `report.json`, it is legacy: ask the user to open it in Power BI Desktop and save as PBIP with PBIR enabled. Never edit the user's files; all outputs go to a separate work folder.
2. **Extract.** `python scripts/extract_report.py <project_dir> --out work/extract.json`. Read `work/extract.json`: pages, visuals (type, x/y/w/h, title, fields), view families, and used measures with DAX + `///` descriptions.
3. **Write `work/content.json`.** Start from `assets/content.example.json`. For each page write the ficha in all requested languages. Rules:
   - Source of truth for all texts is **English**; translate from it, never between other languages.
   - Describe business meaning, not DAX. Use measure descriptions (`///`) when present; otherwise infer from name + DAX and mark uncertain items with `"review": true`.
   - Define 2-6 **zones** per page (a rectangle or a list of visual ids) with a number and a one-line text per language.
   - Do not invent refresh schedules, sources or granularity. If not in the model (partition source, `refresh` annotations) or told by the user, write `"TBD"` and list it under open questions at the end of the answer.
4. **Glossary.** Copy `assets/glossary.json` to `work/` and extend it. Every domain term appears once with all four languages. See `references/translation.md`.
5. **Validate.** `python scripts/validate_content.py work/extract.json work/content.json` then `python scripts/check_glossary.py work/glossary.json work/content.json`. Fix every error; review warnings.
6. **Screenshots (optional).** If PNGs exist, put them in `work/screenshots/<pageId>.png`. How to get them: `references/screenshots.md`. Without them the manual uses the wireframe.
7. **Build.** `python scripts/build_manual.py work/extract.json work/content.json --glossary work/glossary.json --out work/out --langs en,es,it,fr`.
8. **Check the PDFs.** Rasterize 2-3 pages (pymupdf if installed) and look for: text overflow, overlapping zone markers, empty cells, wrong accents. Fix `content.json` (shorten texts) rather than the layout.

## Hard rules

- Read-only on the PBIP project. Never run anything from the project folder.
- No company data in this repo (public). Real `extract.json`/`content.json` stay in the user's private work folder.
- Never fabricate numbers, owners, refresh times or sources.
- Keep one terminology per language (glossary). A term changed in one language must be changed in all four.
- Third-party tools mentioned in `references/prior-art.md` are **ideas to reimplement**, not dependencies. Do not download or run them in a closed environment.

## Files

| Path | Purpose |
|---|---|
| `scripts/extract_report.py` | PBIR + TMDL reader (stdlib only) |
| `scripts/build_manual.py` | PDF builder (reportlab) |
| `scripts/validate_content.py` | Structure / coverage checks |
| `scripts/check_glossary.py` | Terminology consistency across languages |
| `assets/content.example.json` | Content template |
| `assets/glossary.json` | Starter glossary (Power BI + BI terms) |
| `references/pbir-format.md` | PBIR folder/JSON cheat sheet |
| `references/tmdl-format.md` | TMDL cheat sheet |
| `references/screenshots.md` | Ways to get page images, with limits |
| `references/model-documentation.md` | What good model docs contain |
| `references/pdf-engines.md` | reportlab vs Typst vs Chromium vs WeasyPrint |
| `references/translation.md` | Glossary + review workflow |
| `references/prior-art.md` | Public projects studied, licences, risks |
| `tests/` | Fixture project and unit tests |
