#!/usr/bin/env python3
"""Tests for tools/render_pptx.py - payload validation, layer planning, rendering.

Standard library only for the validation tests; the render smoke test is skipped
when python-pptx is not installed.

Run with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import render_pptx as rp  # noqa: E402

HAVE_PPTX = importlib.util.find_spec("pptx") is not None


def slide(title: str = "A headline", **extra) -> dict:
    body = {
        "id": 2,
        "title": title,
        "bullets": ["First point", "Second point"],
        "visual": "a chart",
        "speaker_notes": "Two cue lines that carry the point across the slide.",
        "est_seconds": 30,
    }
    body.update(extra)
    return body


def payload(slides: list[dict], schema: str = "1.1") -> dict:
    return {
        "schema_version": schema,
        "meta": {
            "title": "Deck",
            "audience": "leads",
            "purpose": "report",
            "language": "en",
            "target_minutes": 5,
            "slide_count": len(slides),
            "est_minutes": 4.0,
        },
        "slides": slides,
    }


def chart(**overrides) -> dict:
    spec = {
        "type": "column",
        "title": "Hours per week",
        "categories": ["A", "B", "C"],
        "series": [{"name": "Hours", "values": [1, 2, 3]}],
        "unit": "hours",
        "source": "Survey",
    }
    spec.update(overrides)
    return spec


def table(**overrides) -> dict:
    spec = {
        "columns": ["Item", "Owner"],
        "rows": [["A", "B"]],
        "source": "Tracker",
    }
    spec.update(overrides)
    return spec


class SchemaVersionTests(unittest.TestCase):
    def test_accepts_1_0_and_1_1(self) -> None:
        for version in ("1.0", "1.1"):
            with self.subTest(version=version):
                self.assertEqual(rp.validate_payload(payload([slide()], schema=version)), [])

    def test_rejects_unknown_version(self) -> None:
        errors = rp.validate_payload(payload([slide()], schema="2.0"))
        self.assertTrue(any("schema_version" in item for item in errors), errors)


class ChartValidationTests(unittest.TestCase):
    def test_minimal_chart_is_clean(self) -> None:
        data = payload([slide(title="Headline"), slide(chart=chart())])
        self.assertEqual(rp.validate_payload(data), [])

    def test_unknown_type_is_rejected(self) -> None:
        errors, _ = rp.check_chart(chart(type="radar"), "chart")
        self.assertTrue(any("type must be one of" in item for item in errors), errors)

    def test_category_count_is_bounded(self) -> None:
        errors, _ = rp.check_chart(chart(categories=["A"]), "chart")
        self.assertTrue(any("categories needs" in item for item in errors), errors)

    def test_series_must_match_category_count(self) -> None:
        errors, _ = rp.check_chart(chart(series=[{"name": "S", "values": [1, 2]}]), "chart")
        self.assertTrue(any("values must have 3" in item for item in errors), errors)

    def test_non_numeric_values_are_rejected(self) -> None:
        errors, _ = rp.check_chart(chart(series=[{"name": "S", "values": [1, "x", 3]}]), "chart")
        self.assertTrue(any("must be numeric" in item for item in errors), errors)

    def test_emphasis_outside_categories_is_rejected(self) -> None:
        errors, _ = rp.check_chart(chart(emphasis=[9]), "chart")
        self.assertTrue(any("outside the categories" in item for item in errors), errors)

    def test_pie_with_two_series_warns(self) -> None:
        spec = chart(type="pie", series=[{"name": "S", "values": [1, 2, 3]},
                                         {"name": "T", "values": [3, 2, 1]}])
        errors, warnings = rp.check_chart(spec, "chart")
        self.assertEqual(errors, [])
        self.assertTrue(any("extra series ignored" in item for item in warnings), warnings)


class TableValidationTests(unittest.TestCase):
    def test_minimal_table_is_clean(self) -> None:
        data = payload([slide(title="Headline"), slide(table=table())])
        self.assertEqual(rp.validate_payload(data), [])

    def test_column_count_is_bounded(self) -> None:
        errors, _ = rp.check_table(table(columns=["Only"]), "table")
        self.assertTrue(any("columns needs" in item for item in errors), errors)

    def test_row_width_must_match_columns(self) -> None:
        errors, _ = rp.check_table(table(rows=[["A", "B", "C"]]), "table")
        self.assertTrue(any("must have 2 cells" in item for item in errors), errors)

    def test_too_many_rows_is_rejected(self) -> None:
        errors, _ = rp.check_table(table(rows=[["A", "B"]] * 9), "table")
        self.assertTrue(any("rows needs" in item for item in errors), errors)


class SlideRuleTests(unittest.TestCase):
    def test_chart_and_table_on_one_slide_is_rejected(self) -> None:
        data = payload([slide(title="Headline"), slide(chart=chart(), table=table())])
        self.assertTrue(any("both chart and table" in item for item in rp.validate_payload(data)))

    def test_data_block_on_the_title_slide_is_rejected(self) -> None:
        first = slide(chart=chart())
        first["id"] = 1
        data = payload([first, slide()])
        self.assertTrue(any("title slide" in item for item in rp.validate_payload(data)))

    def test_bullets_are_still_required(self) -> None:
        data = payload([slide(title="Headline"), slide(chart=chart(), bullets=[])])
        self.assertTrue(any("no bullets" in item for item in rp.validate_payload(data)))


class LayerPlanTests(unittest.TestCase):
    def test_text_only_slide_keeps_the_full_body(self) -> None:
        zones = rp.plan_layers(13.333, 7.5, has_data=False)
        self.assertIsNone(zones["data"])
        x, _, width, _ = zones["copy"]
        self.assertAlmostEqual(x + width, 13.333 - rp.LEFT_GUTTER, places=3)

    def test_data_zone_sits_right_of_the_copy_zone_without_overlap(self) -> None:
        zones = rp.plan_layers(13.333, 7.5, has_data=True)
        copy_x, _, copy_w, _ = zones["copy"]
        data_x, _, data_w, _ = zones["data"]
        self.assertGreaterEqual(data_x, copy_x + copy_w)
        self.assertAlmostEqual(data_x - (copy_x + copy_w), rp.COLUMN_GAP, places=3)
        self.assertLessEqual(data_x + data_w, 13.333 - rp.LEFT_GUTTER)

    def test_data_zone_never_reaches_the_footnote_band(self) -> None:
        zones = rp.plan_layers(13.333, 7.5, has_data=True)
        _, copy_y, _, copy_h = zones["copy"]
        _, note_y, _, _ = zones["footnote"]
        self.assertLessEqual(copy_y + copy_h, note_y)

    def test_narrow_four_three_deck_stays_inside_the_slide(self) -> None:
        zones = rp.plan_layers(10.0, 7.5, has_data=True)
        data_x, _, data_w, _ = zones["data"]
        self.assertLessEqual(round(data_x + data_w, 3), 10.0 - rp.LEFT_GUTTER + 0.001)


@unittest.skipUnless(HAVE_PPTX, "python-pptx is not installed")
class RenderSmokeTests(unittest.TestCase):
    def render(self, data: dict) -> tuple[Path, dict]:
        directory = Path(tempfile.mkdtemp(prefix="render-pptx-"))
        payload_path = directory / "deck.json"
        payload_path.write_text(json.dumps(data), encoding="utf-8")
        out_path = directory / "deck.pptx"
        report = rp.render_deck(data, None, None, False, out_path, force=True)
        return out_path, report

    def test_chart_and_table_become_native_objects(self) -> None:
        from pptx import Presentation

        data = payload([
            slide(title="Headline"),
            slide(title="Chart slide", chart=chart()),
            slide(title="Table slide", table=table()),
        ])
        out_path, report = self.render(data)
        prs = Presentation(str(out_path))
        self.assertEqual(len(prs.slides), 3)
        seen = {"chart": 0, "table": 0}
        for shape in prs.slides[1].shapes:
            seen["chart"] += int(shape.has_chart)
        for shape in prs.slides[2].shapes:
            seen["table"] += int(shape.has_table)
        self.assertEqual(seen, {"chart": 1, "table": 1})
        self.assertEqual(report["slides"][1]["layers"]["data"], "chart:column")
        self.assertEqual(report["slides"][2]["layers"]["data"], "table:2x1")
        self.assertEqual(report["warnings"], [])

    def test_chart_keeps_its_source_as_a_footnote(self) -> None:
        from pptx import Presentation

        out_path, report = self.render(payload([slide(title="H"), slide(chart=chart())]))
        texts = [shape.text_frame.text for shape in Presentation(str(out_path)).slides[1].shapes
                 if shape.has_text_frame]
        self.assertTrue(any("Source: Survey" in text for text in texts), texts)
        self.assertEqual(report["slides"][1]["layers"]["footnote"], "Survey")

    def test_long_bullet_lists_are_trimmed_beside_a_data_block(self) -> None:
        data = payload([slide(title="H"),
                        slide(chart=chart(), bullets=[f"Point {i}" for i in range(5)])])
        _, report = self.render(data)
        self.assertEqual(report["slides"][1]["layers"]["copy"], 3)
        self.assertTrue(any("kept 3" in item for item in report["warnings"]), report["warnings"])

    def test_example_payload_renders(self) -> None:
        example = ROOT / "examples" / "data-layer.example.json"
        data = json.loads(example.read_text(encoding="utf-8"))
        self.assertEqual(rp.validate_payload(data), [])
        _, report = self.render(data)
        data_layers = [entry["layers"]["data"] for entry in report["slides"]
                       if entry["layers"]["data"]]
        self.assertEqual(len(data_layers), 4, data_layers)


if __name__ == "__main__":
    unittest.main()
