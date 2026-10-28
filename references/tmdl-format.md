# TMDL cheat sheet (offline)

TMDL = Tabular Model Definition Language, the text format of semantic models inside PBIP (`*.SemanticModel/definition/`). Indentation is significant (one tab per level by default).

```
definition/
  model.tmdl            # model-level properties, culture refs
  relationships.tmdl
  expressions.tmdl      # shared M queries / parameters
  functions.tmdl        # DAX user-defined functions (newer models)
  cultures/*.tmdl
  roles/*.tmdl          # row-level security
  tables/<Table>.tmdl   # table + columns + measures + partitions
```

## Table file

```
table Sales
	lineageTag: ...

	/// Net invoiced sales in EUR          <- description of the NEXT object
	measure 'Total Sales' = SUM(Sales[Amount])
		formatString: #,0
		displayFolder: KPIs

	measure 'Margin %' =
			DIVIDE( SUM(Sales[Margin]), [Total Sales] )
		formatString: 0.0%

	measure 'Sales PY' = ```
			CALCULATE([Total Sales], SAMEPERIODLASTYEAR('Calendar'[Date]))
			```

	column Amount
		dataType: double

	partition Sales = m
		mode: import
		source = ...
```

Rules the parser relies on:

- Object names with spaces are single-quoted; `''` escapes a quote.
- `///` lines directly above an object are its description.
- Properties sit one level deeper than the object; multi-line expressions sit **two** levels deeper, or inside a triple-backtick fence.
- `mode:` in a partition is `import`, `directQuery` or `dual`.
- Source hints: the first M function in the partition (`Sql.Database`, `Excel.Workbook`, `SharePoint.Files`, `Lakehouse.Contents`, ...).

## What to pull for a user manual

| Need | Where |
|---|---|
| Plain-language meaning of a KPI | `///` description, else name + DAX |
| Comparison basis (PY, target, MTD) | DAX patterns: `SAMEPERIODLASTYEAR`, `DATEADD`, `TOTALYTD`, `[Target]` |
| Source system | partition M source hint |
| Granularity | the visual's category fields + date table level |
| Refresh | NOT in TMDL; ask the owner or read it from the service. Write TBD otherwise |

## Related measure DAX pattern -> plain words

| DAX contains | Say |
|---|---|
| `SAMEPERIODLASTYEAR`, `DATEADD(..., -1, YEAR)` | compared with the same period last year |
| `TOTALYTD`, `DATESYTD` | accumulated since 1 January |
| `TOTALMTD`, `DATESMTD` | accumulated since the start of the month |
| `DIVIDE(a, b)` | a as a share of b (ratio) |
| `RANKX`, `TOPN` | ranking / top N |
| `ALL`, `REMOVEFILTERS` | ignores the filters on that field |
| `USERELATIONSHIP` | uses an alternative date (e.g. ship date) |
