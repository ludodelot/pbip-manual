# PBIR cheat sheet (offline)

PBIR = "Power BI enhanced report format": one JSON file per page and per visual instead of one big `report.json`. It lives inside a PBIP project. Written from knowledge of the format; always re-check against the `$schema` URLs found inside the files if a field looks different.

## Project layout

```
Demo.pbip                         # entry file (JSON), points to the report
Demo.Report/
  definition.pbir                 # links report to its semantic model (byPath / byConnection)
  definition/
    version.json
    report.json                   # report-level settings, theme, filters
    reportExtensions.json         # optional: report-level measures
    pages/
      pages.json                  # { "pageOrder": [...], "activePageName": "..." }
      <pageId>/
        page.json                 # name, displayName, width, height, pageBinding, visibility
        visuals/
          <visualId>/
            visual.json
    bookmarks/                    # optional
Demo.SemanticModel/
  definition/                     # TMDL (see tmdl-format.md)
```

Legacy PBIR ("PBIR-Legacy") has a single `report.json` with all pages inside. This skill does not read it. Convert by opening in Power BI Desktop with PBIR enabled and saving as PBIP.

## page.json (fields used)

| Field | Meaning |
|---|---|
| `name` | page id (folder name) |
| `displayName` | tab name the user sees |
| `width`, `height` | canvas size in px (default 1280x720) |
| `pageBinding.type` | `Drillthrough` or `Tooltip` for special pages |
| `visibility` | `HiddenInViewMode` for hidden pages |

## visual.json (fields used)

| Path | Meaning |
|---|---|
| `name` | visual id |
| `position.{x,y,z,width,height}` | box on the page canvas, origin top-left |
| `isHidden` | hidden visual |
| `parentGroupName` | visual belongs to a group |
| `visualGroup.displayName` | present when the item is a group, not a visual |
| `visual.visualType` | `card`, `lineChart`, `tableEx`, `slicer`, `textbox`, ... |
| `visual.query.queryState.<Role>.projections[].field` | fields bound to a role (`Values`, `Category`, `Y`, `Rows`, ...) |
| `visual.visualContainerObjects.title[0].properties.text.expr.Literal.Value` | title text, wrapped in single quotes |
| `visual.objects.general[0].properties.paragraphs[].textRuns[].value` | text of a textbox |

Field shapes: `{"Column": {"Expression": {"SourceRef": {"Entity": "T"}}, "Property": "C"}}`, same with `Measure`, `Aggregation` (nested `Column` + `Function`), `HierarchyLevel`.

## Visual families used for the manual

| Family | visualType examples |
|---|---|
| kpi | card, multiRowCard, kpi, gauge |
| chart | bar/column/line/area/pie/donut/treemap/scatter/map/waterfall/funnel |
| table | tableEx, pivotTable |
| filter | slicer |
| text | textbox, shape, image, actionButton |

## Pitfalls

- Files may start with a UTF-8 BOM: open with `utf-8-sig`.
- Visual `x/y` are in the page's own units; scale using `page.width/height`, not the screen.
- Hidden visuals and groups must be skipped when drawing the wireframe.
- Never write into the project folder; Power BI Desktop validates files strictly and a bad edit can make the report unopenable.
