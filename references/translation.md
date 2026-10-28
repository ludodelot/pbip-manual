# EN / ES / IT / FR: consistent technical translation

No public project dedicated to this was found; this is a lightweight process built from standard localization practice.

## Principles

1. **English is the source.** Translate from EN to each language. Never translate ES -> IT or FR -> ES; that is where drift starts.
2. **One glossary, four columns** (`assets/glossary.json`): id, en, es, it, fr, short definition per language, optional `avoid` list of forbidden variants per language.
3. **Official product terms first.** For Power BI UI words (slicer, drill-through, bookmark, tooltip...), use Microsoft's terms for each language (Microsoft Language Portal). Entries flagged `_review` in the glossary must be confirmed before publishing.
4. **Short texts.** Zone text under 150 characters, ficha fields under 80-160. Italian and French run about 15-25% longer than English; ES about 15%.
5. **Business words, not DAX.** Same rule in all languages.
6. **Keep untranslatable names as-is**: measure names, page names and field names appear in the report in their original language. Quote them exactly; do not translate them.

## Workflow

1. Write or approve the English `content.json` first.
2. Generate ES/IT/FR drafts (Claude or human) using the glossary as hard constraints.
3. Run `check_glossary.py`: errors for forbidden variants, warnings when the English text uses a glossary term and the translation lacks the canonical one.
4. Native reviewer reads only the diff of changed strings (fields with `"review": true`).
5. Back-translation spot check on 5-10 strings per language for key KPIs.
6. Freeze the glossary version with the manual; changing a term means re-running the check on all languages.

## Style per language

| Language | Address | Notes |
|---|---|---|
| EN | you, active voice | simple verbs: see, compare, pick |
| ES | tú (neutral); avoid regional slang | "informe" for report; match the term chosen in the glossary |
| IT | tu or voi, one choice for the whole manual | "report" is common in IT business usage |
| FR | vous | decimal comma, "1 000" thin-space grouping, "%" with narrow space is optional |

Numbers and dates inside examples follow each language's convention; do not paste an English-formatted number into other languages.

## Drift traps

- "dashboard / panel / tablero / tableau de bord": pick one per language and put the others in `avoid`.
- "refresh": ES "actualización", not "refresco".
- "measure" vs "metric": a Power BI measure is not a KPI; keep both terms distinct.
- Verb forms of glossary nouns (filter -> filtrare) trigger warnings in `check_glossary.py`: review, do not auto-fix.
