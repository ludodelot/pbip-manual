# Documenting a semantic model: what good output contains

Distilled from public documentation generators for TMDL/PBIP (see `prior-art.md`). Reimplement what you need; do not depend on them.

## Sections that recur across tools

| Section | Content | Cost to add here |
|---|---|---|
| Overview | counts of tables, columns, measures, relationships; storage modes | S |
| Tables | columns with type, description, hidden flag | S |
| Measures index (A-Z) | name, folder, format string, DAX, description | S (already extracted) |
| Auto-description | when a measure has no `///`, describe from DAX patterns (YTD, PY, ratio, ranking) | S, see pattern table in `tmdl-format.md` |
| Relationships | from/to, cardinality, cross-filter direction, active/inactive | M |
| Data sources | connection function + server/db from M partitions | S (hint only) |
| Measure lineage | which measures/tables a measure depends on, from DAX references + relationship graph; Mermaid or HTML | M |
| Security roles | RLS roles and filters | S |
| Calculation groups | items and precedence | M |
| Complexity index | normalized score from counts of tables/measures/DAX patterns | optional |

## Output formats seen

Markdown with table of contents and collapsible sections; self-contained HTML (printable to PDF); JSON for pipelines; JSONL for retrieval; Mermaid diagrams for lineage. One tool offers an LLM "prompt pack" built from the TMDL text to draft data-dictionary definitions.

## For end-user manuals (this skill)

End users do not need DAX. Keep model detail to what changes a reader's decision:

1. KPI meaning in one sentence (from `///` or name).
2. Comparison basis (PY, YTD, target).
3. Source system and refresh (ask if unknown).
4. Granularity.
5. Caveats (excludes returns, in EUR, etc.). Only if present in the model or told by the owner.

Put technical detail (DAX, lineage, relationships) in a separate maintainer document, not in the end-user PDF.

## Quality checklist for a measure description

- Says what is counted, in business words.
- States unit and currency.
- States period logic (month, YTD, rolling).
- Names exclusions.
- Under 25 words.
