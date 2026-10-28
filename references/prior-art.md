# Prior art studied (public projects)

Snapshot of 2026-10-28, built from web search results and package pages, **not from reading the source code**. Licence and activity are stated only where a source showed them; otherwise "not verified". Everything here is an **idea to reimplement**. Do not download or run third-party code in a closed environment. Re-verify before reuse.

| Project | Where | Licence | Activity seen | What it offers | Idea reused here | Risk |
|---|---|---|---|---|---|---|
| pbi-semantic-doc | PyPI `pbi-semantic-doc` (github ViciusLio/pbi-semantic-doc) | MIT | v0.6.x on PyPI | Docs for TMDL models + PBIR report analysis; MD/HTML/JSON; per-measure lineage; auto-descriptions from DAX patterns; complexity index | Auto-description from DAX, lineage idea, printable single HTML | low |
| pbir-utils | PyPI `pbir-utils` | MIT | v2.5.2 | Validate/sanitize PBIR, extract metadata to CSV, wireframe visualizer | Compare wireframe geometry rules | low |
| tmdl-lens | PyPI `tmdl-lens` | not verified | not verified | HTML/MD/text/JSON docs of data sources, tables, measures, relationships, roles; Mermaid source->table lineage; owner/team/refresh metadata via config | Config file for owner/refresh metadata; source->table diagram | low-medium (also distributed as a standalone app) |
| PBI Doc Generator | github djrien-ai/pbi-doc-generator (releases page) | not verified | releases in 2026 | Offline docs from pbix/pbip; to-scale SVG wireframe per page; fields per visual role; offline Mermaid; optional LLM prompt pack | SVG wireframe with data roles per visual | medium (ships as an executable) |
| pbir / pbir.tools | github maxanatsko/pbir.tools | not verified | releases through 2026 | PBIR CLI: validate, BPA rules, bulk edits, `desktop screenshot --all` | Screenshot automation concept; schema validation with provenance | medium (installs CLI, drives Desktop, edits reports) |
| pbi-cli | github MinaSaad1/pbi-cli | not verified | not verified | Claude Code skills for model and PBIR work; needs Desktop connection | How skills are split by layer (model vs report) | high (executes code, connects to Desktop) |
| power-bi-agentic-development | marketplace of Power BI/Fabric skills, subagents, hooks | GPL-3.0 | not verified | Hooks that validate PBIR, TMDL, bindings, DAX refs | Deterministic validation hooks idea only | medium: copyleft, **do not copy code** |
| josiahsiegel/claude-plugin-marketplace (programmatic-development, tmdl-mastery) | github, listed on claudeskills.info | MIT | updated 2026-06-18 on listing | PBIP/PBIR/TMDL reference skills with references/ folders, tool-choice tables | `references/` layout, tool decision table | medium (contains deployment scripts) |
| julianobarbosa/claude-code-skills `power-bi` | github, listed on skills.sh | not verified | updated 2026-07-22 on listing | PBIP project skill with workflow routing tables and rules ("PBIP only") | SKILL.md routing table style | medium |
| Microsoft `exportToFile` REST API | learn.microsoft.com Power BI embedded docs | n/a | current docs | PDF/PPTX/PNG export; capacity requirements | see `screenshots.md` | low (credentials: IT decision) |

## Take-aways baked into this skill

1. Plain Python, no runtime dependencies beyond reportlab, so it works in a closed environment.
2. Separate **extract -> content -> build** with JSON in the middle: any engine can replace the builder.
3. Validation scripts (coverage, length, glossary) run before building, like the deterministic hooks in other projects.
4. `references/` hold the knowledge; `SKILL.md` stays a short workflow.
5. Maintainer-level model docs (lineage, relationships) are a separate deliverable from the end-user manual.

## Not found / open

- A public tool that renders PBIR to a faithful image or HTML: none verified. Only approximate wireframes.
- A dedicated EN/ES/IT/FR terminology workflow for Power BI: none found.
- Playwright against the Power BI service: no reliable public source reviewed.
