# PDF engines for a restricted Windows machine

Context: Windows corporate, Python 3.13, no admin rights for heavy installs, no internet. Written 2026-10-28 from public docs and release notes; items marked "not verified" were not checked.

| Engine | Needs | Layout power | Offline in closed env | Verdict |
|---|---|---|---|---|
| **reportlab** (canvas) | pure Python wheel (already installed) | manual positioning, full vector control, TTF fonts | Yes | **Default.** Zero new dependencies. Best for diagrams drawn from coordinates |
| Typst | a single compiled binary (no extra toolchain, per a Rust project's docs) | best typography and automatic layout, templates | Yes once the binary is allowed | Best upgrade if IT approves one executable. Learn a new syntax. Wireframe would need to be generated as Typst/SVG |
| HTML + Chromium/Edge "print to PDF" | an installed Chromium-based browser (Edge ships with Windows; not verified for your policy) | full CSS; paged media is incomplete in Chromium, Paged.js fills gaps | Yes if the browser exists | Good fallback for CSS-minded authors. Headless printing from a script may be blocked by policy |
| WeasyPrint | Python package plus native libraries (GTK/Pango) on Windows | good CSS paged media | Not verified on restricted Windows | Avoid here: dependencies are the issue you already have |
| pymupdf (installed) | wheel | PDF editing and rendering, not layout | Yes | Use to **check** output (rasterize pages) and to merge/split, not to design pages |

## Why reportlab stays the default

- Everything is already installed.
- The wireframe is geometry: rectangles from real positions; reportlab draws it exactly and vector-sharp.
- Fixed 16:9 slides do not need a flow layout engine.
- Weakness: text overflow is on you. `build_manual.py` shrinks text to a minimum size; `validate_content.py` warns on long strings. Fix by shortening copy.

## Fonts

Standard Helvetica (WinAnsi) covers EN/ES/IT/FR accents. For consistent glyphs the builder auto-registers Segoe UI or Arial on Windows, DejaVu on Linux, or a font passed with `--font/--font-bold`. Use a licensed font you may embed.

## When to switch

Move to Typst or HTML only if you need: automatic page flow for long text, hyperlinks/TOC with page numbers, or complex tables across pages. Keep `extract.json` + `content.json` as the stable interface so only the renderer changes.
