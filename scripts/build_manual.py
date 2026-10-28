#!/usr/bin/env python3
"""Build 16:9 PDF user manuals (one per language) from extract.json + content.json.

Usage:
    python build_manual.py extract.json content.json --glossary glossary.json \
        --out out_dir [--langs en,es,it,fr] [--screenshots dir] [--font file.ttf --font-bold file.ttf]

Needs: reportlab. Screenshots are optional: <screenshots>/<pageId>.png replaces the wireframe.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = 960, 540
MARGIN = 40
NAVY = colors.HexColor("#1F2937")
ACCENT = colors.HexColor("#E4572E")
GREY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F3F4F6")
FAMILY_FILL = {
    "kpi": colors.HexColor("#DBEAFE"), "chart": colors.HexColor("#E0F2FE"),
    "table": colors.HexColor("#E5E7EB"), "filter": colors.HexColor("#FEF3C7"),
    "text": colors.HexColor("#F9FAFB"), "other": colors.HexColor("#F1F5F9"),
}

LABELS = {
    "en": {"manual": "User manual", "contents": "Contents", "glossary": "Glossary", "page": "Page",
           "diagram": "Page diagram", "zones": "What you will find here", "term": "Term",
           "definition": "Definition", "drill": "drill-through page", "hidden": "hidden page",
           "use_it_when": "Use it when", "source": "Source", "refresh": "Refresh",
           "granularity": "Granularity", "main_kpi": "Main KPI", "comparison": "Comparison",
           "wire_note": "Schematic view: boxes show where each visual sits on the page."},
    "es": {"manual": "Manual de usuario", "contents": "Contenido", "glossary": "Glosario", "page": "Página",
           "diagram": "Esquema de la página", "zones": "Qué encontrarás aquí", "term": "Término",
           "definition": "Definición", "drill": "página de detalle", "hidden": "página oculta",
           "use_it_when": "Úsala cuando", "source": "Fuente", "refresh": "Actualización",
           "granularity": "Granularidad", "main_kpi": "KPI principal", "comparison": "Comparación",
           "wire_note": "Vista esquemática: las cajas muestran dónde está cada visual en la página."},
    "it": {"manual": "Manuale d'uso", "contents": "Indice", "glossary": "Glossario", "page": "Pagina",
           "diagram": "Schema della pagina", "zones": "Cosa troverai qui", "term": "Termine",
           "definition": "Definizione", "drill": "pagina di dettaglio", "hidden": "pagina nascosta",
           "use_it_when": "Usala quando", "source": "Fonte", "refresh": "Aggiornamento",
           "granularity": "Granularità", "main_kpi": "KPI principale", "comparison": "Confronto",
           "wire_note": "Vista schematica: i riquadri mostrano dove si trova ogni visual nella pagina."},
    "fr": {"manual": "Manuel utilisateur", "contents": "Sommaire", "glossary": "Glossaire", "page": "Page",
           "diagram": "Schéma de la page", "zones": "Ce que vous y trouverez", "term": "Terme",
           "definition": "Définition", "drill": "page de détail", "hidden": "page masquée",
           "use_it_when": "À utiliser quand", "source": "Source", "refresh": "Actualisation",
           "granularity": "Granularité", "main_kpi": "KPI principal", "comparison": "Comparaison",
           "wire_note": "Vue schématique : les cases montrent où se trouve chaque visuel sur la page."},
}
FICHA_ORDER = ["use_it_when", "source", "refresh", "granularity", "main_kpi", "comparison"]

FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf"),
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
]


def register_fonts(regular: str | None, bold: str | None) -> tuple[str, str]:
    pairs = ([(regular, bold or regular)] if regular else []) + FONT_CANDIDATES
    for reg, bld in pairs:
        if reg and bld and os.path.exists(reg) and os.path.exists(bld):
            pdfmetrics.registerFont(TTFont("Body", reg))
            pdfmetrics.registerFont(TTFont("Body-Bold", bld))
            return "Body", "Body-Bold"
    return "Helvetica", "Helvetica-Bold"  # WinAnsi: covers EN/ES/IT/FR accents


def clean(text: str, font: str) -> str:
    if font.startswith("Helvetica"):
        for a, b in {"\u2192": "->", "\u2265": ">=", "\u2264": "<=", "\u2022": "-", "\u2011": "-"}.items():
            text = text.replace(a, b)
    return text


def fit(text, font, max_size, min_size, width, max_h, lead=1.22):
    size = max_size
    while True:
        lines = simpleSplit(text, font, size, width)
        if len(lines) * size * lead <= max_h or size <= min_size:
            return size, lines
        size -= 0.5


class Manual:
    def __init__(self, path, lang, extract, content, glossary, shots, fonts, report_name):
        self.c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
        self.lang, self.L = lang, LABELS[lang]
        self.extract, self.content, self.glossary = extract, content, glossary
        self.shots = shots
        self.F, self.FB = fonts
        self.report_name = report_name
        self.n = 0

    # -- helpers
    def t(self, x, y, text, size=10, bold=False, color=NAVY):
        font = self.FB if bold else self.F
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        self.c.drawString(x, y, clean(text, font))

    def para(self, x, y_top, width, text, size, max_h, bold=False, color=NAVY, min_size=7.5):
        font = self.FB if bold else self.F
        text = clean(text, font)
        size, lines = fit(text, font, size, min_size, width, max_h)
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        y = y_top - size
        for ln in lines:
            self.c.drawString(x, y, ln)
            y -= size * 1.22
        return len(lines) * size * 1.22

    def footer(self):
        self.n += 1
        self.c.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.c.line(MARGIN, 28, PAGE_W - MARGIN, 28)
        self.t(MARGIN, 14, f"{self.report_name} - {self.L['manual']}", 8, color=GREY)
        s = str(self.n)
        self.c.setFont(self.F, 8)
        self.c.setFillColor(GREY)
        self.c.drawRightString(PAGE_W - MARGIN, 14, s)

    def marker(self, x, y, n, r=9):
        self.c.setFillColor(ACCENT)
        self.c.setStrokeColor(colors.white)
        self.c.circle(x, y, r, stroke=1, fill=1)
        self.c.setFillColor(colors.white)
        self.c.setFont(self.FB, 9 if n < 10 else 7.5)
        self.c.drawCentredString(x, y - 3.2, str(n))

    # -- pages
    def cover(self):
        c = self.c
        c.setFillColor(NAVY)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        c.setFillColor(ACCENT)
        c.rect(MARGIN + 20, 345, 80, 6, stroke=0, fill=1)
        title = self.content["title"][self.lang]
        self.c.setFillColor(colors.white)
        size, lines = fit(clean(title, self.FB), self.FB, 44, 26, PAGE_W - 2 * MARGIN - 40, 150, 1.15)
        c.setFont(self.FB, size)
        y = 300
        for ln in lines:
            c.drawString(MARGIN + 20, y, ln)
            y -= size * 1.15
        sub = self.content.get("subtitle", {}).get(self.lang, self.L["manual"])
        c.setFont(self.F, 16)
        c.setFillColor(colors.HexColor("#CBD5E1"))
        c.drawString(MARGIN + 20, y - 10, clean(sub, self.F))
        c.setFont(self.F, 10)
        c.drawString(MARGIN + 20, 40, f"{datetime.date.today().isoformat()}  |  {self.lang.upper()}")
        c.showPage()
        self.n += 1

    def contents(self, pages):
        self.t(MARGIN, PAGE_H - 60, self.L["contents"], 26, True)
        y = PAGE_H - 100
        for i, p in enumerate(pages, 1):
            head = self.content["pages"][p["id"]]["text"][self.lang]["headline"]
            self.t(MARGIN, y, f"{i}.", 12, True, ACCENT)
            self.t(MARGIN + 28, y, p["name"], 12, True)
            self.para(MARGIN + 260, y + 11, PAGE_W - MARGIN * 2 - 260, head, 11, 16, color=GREY)
            y -= 26
            if y < 70:
                break
        self.t(MARGIN, y - 6, self.L["glossary"], 12, True, ACCENT)
        self.footer()
        self.c.showPage()

    def diagram(self, page, cpage, x, y_top, w, h):
        c = self.c
        pw, ph = page["width"], page["height"]
        shot = self.shots.get(page["id"])
        if shot:
            img = ImageReader(str(shot))
            iw, ih = img.getSize()
            s = min(w / iw, h / ih)
            dw, dh = iw * s, ih * s
            ox, oy = x, y_top - dh
            c.drawImage(img, ox, oy, dw, dh)
            c.setStrokeColor(colors.HexColor("#9CA3AF"))
            c.rect(ox, oy, dw, dh, stroke=1, fill=0)
            k = dw / pw
        else:
            k = min(w / pw, h / ph)
            dw, dh = pw * k, ph * k
            ox, oy = x, y_top - dh
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.HexColor("#9CA3AF"))
            c.rect(ox, oy, dw, dh, stroke=1, fill=1)
            for v in sorted(page["visuals"], key=lambda v: v["z"]):
                if v["hidden"] or v["type"] == "group" or v["w"] <= 0:
                    continue
                vx, vy = ox + v["x"] * k, oy + dh - (v["y"] + v["h"]) * k
                vw, vh = v["w"] * k, v["h"] * k
                c.setFillColor(FAMILY_FILL.get(v["family"], FAMILY_FILL["other"]))
                c.setStrokeColor(colors.HexColor("#94A3B8"))
                c.setLineWidth(0.6)
                c.rect(vx, vy, vw, vh, stroke=1, fill=1)
                label = v.get("title") or v["type"]
                if vw > 34 and vh > 11:
                    font = self.F
                    txt = clean(label, font)
                    size = 6.5
                    lines = simpleSplit(txt, font, size, vw - 4)
                    c.setFillColor(GREY)
                    c.setFont(font, size)
                    c.drawString(vx + 3, vy + 3, lines[0] if lines else "")
            c.setLineWidth(1)
        by_id = {v["id"]: v for v in page["visuals"]}
        for z in cpage["zones"]:
            if z.get("visuals"):
                vs = [by_id[i] for i in z["visuals"] if i in by_id]
                x0 = min(v["x"] for v in vs) - 4
                y0 = min(v["y"] for v in vs) - 4
                x1 = max(v["x"] + v["w"] for v in vs) + 4
                y1 = max(v["y"] + v["h"] for v in vs) + 4
                rx, ry, rw, rh = x0, y0, x1 - x0, y1 - y0
            else:
                rx, ry, rw, rh = z["rect"]
            zx, zy = ox + rx * k, oy + dh - (ry + rh) * k
            c.setStrokeColor(ACCENT)
            c.setLineWidth(1.6)
            c.setDash(4, 2)
            c.rect(zx, zy, rw * k, rh * k, stroke=1, fill=0)
            c.setDash()
            c.setLineWidth(1)
            self.marker(max(ox + 9, zx), min(oy + dh - 9, zy + rh * k), z["n"])
        return dh

    def ficha(self, idx, page):
        cpage = self.content["pages"][page["id"]]
        text = cpage["text"][self.lang]
        c = self.c
        c.setFillColor(NAVY)
        c.rect(0, PAGE_H - 62, PAGE_W, 62, stroke=0, fill=1)
        c.setFillColor(ACCENT)
        c.rect(0, PAGE_H - 62, 8, 62, stroke=0, fill=1)
        name = page["name"]
        tag = {"drillthrough": self.L["drill"], "hidden": self.L["hidden"]}.get(page["kind"])
        self.c.setFillColor(colors.white)
        c.setFont(self.FB, 20)
        c.drawString(MARGIN, PAGE_H - 30, clean(f"{idx}. {name}", self.FB))
        if tag:
            c.setFont(self.F, 9)
            c.drawRightString(PAGE_W - MARGIN, PAGE_H - 28, clean(tag, self.F))
        c.setFont(self.F, 11)
        c.setFillColor(colors.HexColor("#CBD5E1"))
        hs, hl = fit(clean(text["headline"], self.F), self.F, 11, 8, PAGE_W - 2 * MARGIN, 18)
        c.setFont(self.F, hs)
        c.drawString(MARGIN, PAGE_H - 50, hl[0] if hl else "")

        top = PAGE_H - 78
        dw, dh_max = 500, 281
        dh = self.diagram(page, cpage, MARGIN, top, dw, dh_max)
        self.t(MARGIN, top - dh - 11, self.L["wire_note"] if not self.shots.get(page["id"]) else "", 7, color=GREY)

        # zone list
        zx = MARGIN + dw + 28
        zw = PAGE_W - MARGIN - zx
        self.t(zx, top - 10, self.L["zones"], 11, True, ACCENT)
        zones = cpage["zones"]
        avail = dh_max - 24
        per = avail / max(len(zones), 1)
        size = 10
        y = top - 24
        for z in zones:
            self.marker(zx + 9, y - 8, z["n"])
            self.para(zx + 26, y - 1, zw - 26, z["text"][self.lang], size, per - 4, min_size=7.5)
            y -= per

        # ficha table (2 columns x 3 rows)
        ty_top = top - dh_max - 22
        row_h = 36
        colw = (PAGE_W - 2 * MARGIN - 16) / 2
        for i, key in enumerate(FICHA_ORDER):
            col, row = i % 2, i // 2
            bx = MARGIN + col * (colw + 16)
            by = ty_top - row * row_h
            c.setFillColor(LIGHT)
            c.rect(bx, by - row_h + 3, colw, row_h - 3, stroke=0, fill=1)
            c.setFillColor(ACCENT)
            c.rect(bx, by - row_h + 3, 3, row_h - 3, stroke=0, fill=1)
            self.t(bx + 10, by - 12, self.L[key], 8, True, GREY)
            self.para(bx + 112, by - 4, colw - 120, text[key], 9, row_h - 8, min_size=7)
        self.footer()
        c.showPage()

    def glossary_pages(self):
        terms = self.glossary.get("terms", [])
        if not terms:
            return
        rows = []
        for t in terms:
            term = t.get(self.lang) or t.get("en", "")
            definition = (t.get("definition", {}) or {}).get(self.lang) or ""
            en = t.get("en", "")
            if self.lang != "en" and en and en.lower() != term.lower():
                term_label = f"{term} ({en})"
            else:
                term_label = term
            rows.append((term_label, definition))
        rows.sort(key=lambda r: r[0].lower())
        i = 0
        while i < len(rows):
            self.t(MARGIN, PAGE_H - 55, self.L["glossary"], 24, True)
            self.t(MARGIN, PAGE_H - 85, self.L["term"], 9, True, GREY)
            self.t(MARGIN + 230, PAGE_H - 85, self.L["definition"], 9, True, GREY)
            y = PAGE_H - 100
            while i < len(rows):
                term, definition = rows[i]
                tl = simpleSplit(clean(term, self.FB), self.FB, 9.5, 215)
                dl = simpleSplit(clean(definition, self.F), self.F, 9.5, PAGE_W - 2 * MARGIN - 240)
                need = max(len(tl), len(dl), 1) * 12 + 6
                if y - need < 45:
                    break
                self.c.setFont(self.FB, 9.5)
                self.c.setFillColor(NAVY)
                for k, ln in enumerate(tl):
                    self.c.drawString(MARGIN, y - 10 - k * 12, ln)
                self.c.setFont(self.F, 9.5)
                for k, ln in enumerate(dl):
                    self.c.drawString(MARGIN + 230, y - 10 - k * 12, ln)
                self.c.setStrokeColor(colors.HexColor("#E5E7EB"))
                self.c.line(MARGIN, y - need + 3, PAGE_W - MARGIN, y - need + 3)
                y -= need
                i += 1
            self.footer()
            self.c.showPage()

    def build(self):
        pages = [p for p in self.extract["pages"] if p["kind"] != "tooltip" and p["id"] in self.content["pages"]]
        self.cover()
        self.contents(pages)
        for i, p in enumerate(pages, 1):
            self.ficha(i, p)
        self.glossary_pages()
        self.c.save()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("extract")
    ap.add_argument("content")
    ap.add_argument("--glossary")
    ap.add_argument("--out", default="out")
    ap.add_argument("--langs", default="en,es,it,fr")
    ap.add_argument("--screenshots")
    ap.add_argument("--font")
    ap.add_argument("--font-bold")
    a = ap.parse_args(argv)

    extract = json.loads(Path(a.extract).read_text(encoding="utf-8-sig"))
    content = json.loads(Path(a.content).read_text(encoding="utf-8-sig"))
    glossary = json.loads(Path(a.glossary).read_text(encoding="utf-8-sig")) if a.glossary else {"terms": []}
    shots = {}
    if a.screenshots and Path(a.screenshots).is_dir():
        for p in Path(a.screenshots).glob("*.png"):
            shots[p.stem] = p
    fonts = register_fonts(a.font, a.font_bold)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for lang in a.langs.split(","):
        if lang not in LABELS:
            print(f"unsupported language: {lang}", file=sys.stderr)
            return 2
        path = out / f"manual_{lang}.pdf"
        Manual(path, lang, extract, content, glossary, shots, fonts, extract["report"]).build()
        print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
