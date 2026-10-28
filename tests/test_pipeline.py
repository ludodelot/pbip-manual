import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_manual  # noqa: E402
import check_glossary  # noqa: E402
import extract_report  # noqa: E402
import validate_content  # noqa: E402

FIXTURE = ROOT / "tests" / "fixture"
CONTENT = json.loads((ROOT / "assets" / "content.example.json").read_text(encoding="utf-8"))
GLOSSARY = json.loads((ROOT / "assets" / "glossary.json").read_text(encoding="utf-8"))


class ExtractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = extract_report.build(FIXTURE)

    def test_pages_order_and_kinds(self):
        ids = [p["id"] for p in self.data["pages"]]
        self.assertEqual(ids, ["overview", "detail", "tip"])
        kinds = {p["id"]: p["kind"] for p in self.data["pages"]}
        self.assertEqual(kinds["detail"], "drillthrough")
        self.assertEqual(kinds["tip"], "tooltip")

    def test_visuals(self):
        ov = self.data["pages"][0]
        by_id = {v["id"]: v for v in ov["visuals"]}
        self.assertEqual(by_id["v_kpi1"]["title"], "Total Sales")
        self.assertEqual(by_id["v_trend"]["family"], "chart")
        self.assertTrue(by_id["v_hidden"]["hidden"])
        self.assertEqual((by_id["v_trend"]["x"], by_id["v_trend"]["w"]), (20, 800))

    def test_measures(self):
        m = self.data["measures_used"]
        self.assertEqual(m["Sales.Total Sales"]["description"], "Net invoiced sales amount in EUR")
        self.assertEqual(m["Sales.Total Sales"]["format"], "#,0")
        self.assertIn("DIVIDE(", m["Sales.Margin %"]["expression"])
        self.assertTrue(m["Sales.Sales PY"]["expression"].startswith("CALCULATE("))
        self.assertNotIn("```", m["Sales.Sales PY"]["expression"])
        self.assertTrue(all(v["found"] for v in m.values()))

    def test_model_hints(self):
        sales = next(t for t in self.data["model"]["tables"] if t["name"] == "Sales")
        self.assertEqual(sales["mode"], "import")
        self.assertEqual(sales["source_hint"], "Sql.Database")

    def test_legacy_report_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Old.Report" / "definition").mkdir(parents=True)
            with self.assertRaises(SystemExit):
                extract_report.build(Path(d))


class ContentTests(unittest.TestCase):
    def test_example_content_valid(self):
        data = extract_report.build(FIXTURE)
        errors, _ = validate_content.validate(data, CONTENT, ["en", "es", "it", "fr"])
        self.assertEqual(errors, [])

    def test_missing_language_detected(self):
        data = extract_report.build(FIXTURE)
        bad = json.loads(json.dumps(CONTENT))
        del bad["pages"]["overview"]["text"]["it"]
        errors, _ = validate_content.validate(data, bad, ["en", "es", "it", "fr"])
        self.assertTrue(any("missing text for 'it'" in e for e in errors))

    def test_unknown_visual_id_detected(self):
        data = extract_report.build(FIXTURE)
        bad = json.loads(json.dumps(CONTENT))
        bad["pages"]["overview"]["zones"][0]["visuals"] = ["nope"]
        errors, _ = validate_content.validate(data, bad, ["en"])
        self.assertTrue(any("unknown visual id" in e for e in errors))

    def test_glossary_forbidden_term(self):
        bad = json.loads(json.dumps(CONTENT))
        bad["pages"]["overview"]["zones"][0]["text"]["es"] = "Usa el tablero de ventas."
        errors, _ = check_glossary.check(GLOSSARY, bad, ["en", "es", "it", "fr"])
        self.assertTrue(any("tablero" in e for e in errors))

    def test_glossary_clean(self):
        errors, _ = check_glossary.check(GLOSSARY, CONTENT, ["en", "es", "it", "fr"])
        self.assertEqual(errors, [])


class BuildTests(unittest.TestCase):
    def test_pdfs_created(self):
        data = extract_report.build(FIXTURE)
        with tempfile.TemporaryDirectory() as d:
            for lang in ["en", "es", "it", "fr"]:
                p = Path(d) / f"m_{lang}.pdf"
                build_manual.Manual(p, lang, data, CONTENT, GLOSSARY, {}, build_manual.register_fonts(None, None),
                                    data["report"]).build()
                raw = p.read_bytes()
                self.assertTrue(raw.startswith(b"%PDF"))
                self.assertGreater(len(raw), 4000)


if __name__ == "__main__":
    unittest.main()
