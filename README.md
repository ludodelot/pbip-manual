# pbip-manual

A Claude Code skill that turns a **Power BI PBIP project** (PBIR report + TMDL model) into a **16:9 PDF user manual** in English, Spanish, Italian and French.

- Runs **fully offline**: Python 3 standard library + `reportlab`.
- **Read-only** on your project. No Power BI Desktop or service needed.
- One page per report page: numbered diagram, zone list, and a "Use it when / Source / Refresh / Granularity / Main KPI / Comparison" table. Glossary at the end.
- Includes offline reference notes (PBIR, TMDL, screenshots, PDF engines, translation workflow, prior art).

## Install as a Claude Code skill

Copy this folder to `~/.claude/skills/pbip-manual/` (or your project's `.claude/skills/`). Then ask Claude: *"Create a user manual for the Power BI project in `<path>`"*.

## Requirements

Python 3.10+ and `reportlab`. Optional: `pymupdf` to rasterize the PDF for visual checks.

## Tests

`python -m unittest discover -s tests`

## Limits

- PBIR only (folder-based). Legacy `report.json` reports must be converted in Power BI Desktop first.
- The wireframe is approximate: it shows visual boxes, types and titles, not real rendering.
- Texts are written by you or by Claude. Review them: nothing is guessed about refresh, owners or sources.

## Licence

MIT. See `LICENSE`.
