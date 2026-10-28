# Getting real page images (offline-friendly options)

The manual works without screenshots (wireframe). Real images are nicer. Options, best first for a closed corporate setup. Checked 2026-10-28; limits come from Microsoft Learn pages and a release note, re-check them before relying on this.

## 1. Manual export from Power BI Desktop (zero risk)

File > Export > PDF, or Export to PowerPoint, then extract one image per page (pymupdf can render PDF pages to PNG). Name files `<pageId>.png` using the ids in `extract.json`. Works with no capacity or admin rights. Slowest if the report has many pages.

## 2. REST `exportToFile` (service, automated)

- Formats: PDF, PPTX, PNG. A multi-page PNG export comes back as a `.zip` with one file per page; names match the Get Pages API.
- Needs the report in a workspace on **Premium, Embedded or Fabric capacity**.
- Not supported for **Premium Per User (PPU)**.
- PNG export needs a tenant setting that is **disabled by default**: ask the Power BI admin. PDF/PPTX export is enabled by default.
- The download URL from polling is valid for 24 hours.
- Asynchronous: start job, poll, download. Limits on concurrent requests and pages per interval apply (429 if exceeded).
- Row-level security can be applied per identity; sensitivity labels can block export with a service principal.
- Needs credentials / app registration: **decision for IT**; never store tokens in the repo.

## 3. Automating Power BI Desktop

A public CLI (`pbir`, project "pbir.tools") documents a `desktop screenshot --all` command that captures pages from an open Power BI Desktop. Licence not verified. Treat as an **idea**: it drives Desktop on the user's machine. Do not install in a closed environment without IT approval.

## 4. Service web UI via browser automation

Not recommended: needs interactive login/SSO, breaks with UI changes, and may conflict with terms of use. Risk: high.

## 5. Wireframe (default)

Vector boxes from real positions and titles. Always available, fully offline. Limits: no real data, no visual styling.

## Rules for images in the manual

- Use demo/anonymized data when the manual leaves the team; screenshots show real numbers.
- PNG aspect ratio should match the page (16:9 for 1280x720) so zone rectangles line up.
- Save as `<pageId>.png` in a `screenshots/` folder and pass `--screenshots`.
