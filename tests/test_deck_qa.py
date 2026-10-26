#!/usr/bin/env python3
"""Tests for tools/deck_qa.py - copy budgets, data slides, pace, variety, scoring.

Run with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import deck_qa as qa  # noqa: E402


def slide(slide_id: int = 2, title: str = "Cut-over time fell by three quarters", **extra) -> dict:
    body = {
        "id": slide_id,
        "title": title,
        "bullets": ["Median cut-over: 6 hours to 90 minutes", "Rollback exercised twice"],
        "visual": "bar chart of cut-over hours",
        "speaker_notes": "The runbook change is why we caught up.",
        "est_seconds": 40,
    }
    body.update(extra)
    return body


def deck(slides: list[dict]) -> dict:
    return {"schema_version": "1.1", "meta": {"title": "Deck", "slide_count": len(slides)}, "slides": slides}


def codes(report: dict) -> list[str]:
    return [issue["code"] for issue in report["issues"]]


class TextWeightTests(unittest.TestCase):
    def test_latin_words(self):
        self.assertEqual(qa.text_weight("four short words here"), 4.0)

    def test_cjk_counts_two_per_word(self):
        # 8 CJK characters weigh the same as 4 words
        self.assertEqual(qa.text_weight("这是一个测试句子"), 4.0)

    def test_mixed_script(self):
        # two CJK characters weigh one word, three Latin tokens weigh three
        self.assertEqual(qa.text_weight("Q3 收入 up 12%"), 4.0)

    def test_empty_and_whitespace(self):
        self.assertEqual(qa.text_weight(""), 0.0)
        self.assertEqual(qa.text_weight("   "), 0.0)

    def test_punctuation_only(self):
        self.assertEqual(qa.text_weight("— · —"), 3.0)


class NumberScanTests(unittest.TestCase):
    def test_two_digit_figures_found(self):
        found = qa.slide_numbers({"title": "Availability 99.97%", "bullets": ["15 of 20 services"]})
        self.assertIn("99.97%", found)
        self.assertIn("15", found)

    def test_single_digit_ignored(self):
        self.assertEqual(qa.slide_numbers({"title": "Three of 4 teams", "bullets": []}), [])

    def test_percentage_kept(self):
        self.assertEqual(qa.slide_numbers({"title": "Up 30%", "bullets": []}), ["30%"])

    def test_dates_are_not_figures(self):
        self.assertEqual(qa.slide_numbers({"title": "Billing ships on 15 October", "bullets": []}), [])
        self.assertEqual(qa.slide_numbers({"title": "October 15 depends on billing", "bullets": []}), [])

    def test_bare_year_is_ignored(self):
        self.assertEqual(qa.slide_numbers({"title": "Written in 2025", "bullets": []}), [])

    def test_dash_prefix_stripped(self):
        self.assertIn("-17", qa.slide_numbers({"title": "Latency -17 ms", "bullets": []}))


class LimitsTests(unittest.TestCase):
    def test_missing_library_falls_back(self):
        limits, library = qa.load_limits(ROOT / "assets" / "does-not-exist.json")
        self.assertIn("default", limits)
        self.assertEqual(library, {})

    def test_library_role_limits_are_widest_variant(self):
        limits, library = qa.load_limits(ROOT / "assets" / "layouts.json")
        self.assertTrue(library)
        self.assertEqual(len(limits), 14)
        # chart variants cap bullets at 3 and words at 10
        self.assertEqual(limits["chart"]["bullets"][1], 3)
        self.assertEqual(limits["chart"]["words_per_bullet"], 10)

    def test_library_without_roles_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layouts.json"
            path.write_text(json.dumps({"version": "1.0"}), encoding="utf-8")
            with self.assertRaises(qa.QAError):
                qa.load_limits(path)


class RoleInferenceTests(unittest.TestCase):
    def test_first_slide_is_title(self):
        self.assertEqual(qa.infer_role(0, 3, {}), "title")

    def test_last_slide_is_closing(self):
        self.assertEqual(qa.infer_role(2, 3, {}), "closing")

    def test_chart_beats_bullet_list(self):
        self.assertEqual(qa.infer_role(1, 3, {"chart": {"type": "bar"}}), "chart")

    def test_table_role(self):
        self.assertEqual(qa.infer_role(1, 3, {"table": {"columns": ["a"], "rows": [["1"]]}}), "table")

    def test_plain_body_is_bullet_list(self):
        self.assertEqual(qa.infer_role(1, 3, {"bullets": ["a", "b", "c"]}), "bullet-list")


class SlideRuleTests(unittest.TestCase):
    def setUp(self):
        self.limits, _ = qa.load_limits(ROOT / "assets" / "layouts.json")

    def run_slide(self, body: dict, index: int = 1, total: int = 3):
        return qa.check_slide(body, index, total, self.limits)

    def test_clean_slide_has_no_findings(self):
        findings = self.run_slide(slide())
        self.assertEqual([f for f in findings if f["severity"] != qa.SEVERITY_INFO], [])

    def test_long_headline_warns(self):
        body = slide(title="Services cut over ahead of schedule with no customer visible incidents at all this quarter")
        self.assertIn("QA101", codes({"issues": self.run_slide(body)}))

    def test_label_headline_warns(self):
        findings = self.run_slide(slide(title="Metrics"))
        self.assertIn("QA102", [f["code"] for f in findings])

    def test_no_bullets_on_body_is_error(self):
        findings = self.run_slide(slide(bullets=[]))
        self.assertIn("QA103", [f["code"] for f in findings])
        self.assertEqual([f["severity"] for f in findings if f["code"] == "QA103"], [qa.SEVERITY_ERROR])

    def test_six_bullets_is_error(self):
        findings = self.run_slide(slide(bullets=[f"Point {i}" for i in range(6)]))
        self.assertEqual([f["severity"] for f in findings if f["code"] == "QA103"], [qa.SEVERITY_ERROR])

    def test_long_bullet_warns(self):
        body = slide(bullets=["This bullet keeps going and going well past the twelve word budget we set here",
                              "Second point"])
        self.assertIn("QA104", [f["code"] for f in self.run_slide(body)])

    def test_figures_without_data_block_is_info_only(self):
        findings = [f for f in self.run_slide(slide()) if f["code"] == "QA105"]
        self.assertEqual([f["severity"] for f in findings], [qa.SEVERITY_INFO])

    def test_figures_with_chart_are_quiet(self):
        body = slide(chart={"type": "bar", "categories": ["a", "b"], "series": [{"values": [1, 2]}]})
        self.assertNotIn("QA105", [f["code"] for f in self.run_slide(body)])

    def test_four_bullets_beside_a_table_warns(self):
        body = slide(bullets=["a", "b", "c", "d"], table={"columns": ["x"], "rows": [["1"]]})
        self.assertIn("QA106", [f["code"] for f in self.run_slide(body)])

    def test_missing_notes_is_error(self):
        findings = self.run_slide(slide(speaker_notes="  "))
        self.assertEqual([f["severity"] for f in findings if f["code"] == "QA107"], [qa.SEVERITY_ERROR])

    def test_notes_too_fast_for_the_slot(self):
        body = slide(speaker_notes=" ".join(["word"] * 40), est_seconds=5)
        self.assertIn("QA108", [f["code"] for f in self.run_slide(body)])

    def test_notes_within_pace(self):
        body = slide(speaker_notes=" ".join(["word"] * 40), est_seconds=40)
        self.assertNotIn("QA108", [f["code"] for f in self.run_slide(body)])

    def test_missing_visual_is_error(self):
        findings = self.run_slide(slide(visual=""))
        self.assertEqual([f["severity"] for f in findings if f["code"] == "QA109"], [qa.SEVERITY_ERROR])

    def test_word_budget(self):
        body = slide(bullets=[" ".join(["word"] * 13) for _ in range(4)])
        self.assertIn("QA110", [f["code"] for f in self.run_slide(body)])

    def test_busy_chart_warns(self):
        body = slide(chart={"type": "line", "categories": list("abcdefghij"),
                            "series": [{"values": [1] * 9}] * 4})
        findings = [f["code"] for f in self.run_slide(body)]
        self.assertIn("QA111", findings)

    def test_pie_with_many_slices_warns(self):
        body = slide(chart={"type": "pie", "categories": list("abcdefg"),
                            "series": [{"values": [1] * 7}]})
        self.assertIn("QA111", [f["code"] for f in self.run_slide(body)])

    def test_dense_table_warns(self):
        body = slide(table={"columns": ["issue", "owner"], "rows": [[f"r{i}", "o"] for i in range(7)]})
        self.assertIn("QA112", [f["code"] for f in self.run_slide(body)])

    def test_sentence_in_cell_warns(self):
        body = slide(table={"columns": ["issue", "owner"],
                            "rows": [["Billing schema dependency blocks service 15 for two weeks", "ops"]]})
        self.assertIn("QA112", [f["code"] for f in self.run_slide(body)])


class VarietyTests(unittest.TestCase):
    def test_repeated_opener_warns_once(self):
        slides = [{"id": i + 1, "title": f"Revenue grew in segment {i}"} for i in range(3)]
        findings = qa.check_variety(slides)
        self.assertEqual([f["code"] for f in findings], ["QA113"])

    def test_varied_openers_are_quiet(self):
        slides = [{"id": i + 1, "title": t} for i, t in enumerate(
            ["Revenue grew", "Costs fell", "Churn spiked", "Hiring slowed"])]
        self.assertEqual(qa.check_variety(slides), [])

    def test_two_in_a_row_is_allowed(self):
        slides = [{"id": 1, "title": "Revenue grew"}, {"id": 2, "title": "Revenue held"}]
        self.assertEqual(qa.check_variety(slides), [])


class ThemeContrastTests(unittest.TestCase):
    def test_bundled_themes_pass(self):
        for name in ("consulting", "swiss", "editorial"):
            issues = qa.check_theme(name, ROOT / "assets" / "themes")
            self.assertEqual(issues, [], msg=name)

    def test_low_contrast_theme_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            theme = json.loads((ROOT / "assets" / "themes" / "swiss.json").read_text(encoding="utf-8"))
            theme["name"] = "washed"
            theme["palette"]["ink"] = "#CCCCCC"
            path = Path(tmp) / "washed.json"
            path.write_text(json.dumps(theme), encoding="utf-8")
            issues = qa.check_theme(str(path), None)
            self.assertTrue(issues)
            self.assertTrue(all(issue["severity"] == qa.SEVERITY_ERROR for issue in issues))


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.limits, _ = qa.load_limits(ROOT / "assets" / "layouts.json")

    def test_clean_deck_scores_100(self):
        report = qa.run_qa(deck([slide(1, "Cut-over finished a quarter early"), slide(2), slide(3, "Approve the October window")]),
                           self.limits, None, None)
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["grade"], "A")

    def test_info_does_not_cost_points(self):
        report = qa.run_qa(deck([slide(1, "Cut-over finished a quarter early"), slide(2), slide(3, "Approve the October window")]),
                           self.limits, None, None)
        self.assertGreaterEqual(report["infos"], 0)
        self.assertEqual(report["score"], 100)

    def test_errors_cost_more_than_warnings(self):
        clean = qa.run_qa(deck([slide(1, "Cut-over finished early"), slide(2), slide(3, "Approve October")]),
                          self.limits, None, None)
        broken = qa.run_qa(deck([slide(1, "Cut-over finished early"), slide(2, bullets=[]), slide(3, "Approve October")]),
                           self.limits, None, None)
        self.assertLess(broken["score"], clean["score"])
        self.assertEqual(clean["score"] - broken["score"], qa.PENALTY[qa.SEVERITY_ERROR])

    def test_grade_bands(self):
        self.assertEqual(qa.grade(100), "A")
        self.assertEqual(qa.grade(75), "B")
        self.assertEqual(qa.grade(60), "C")
        self.assertEqual(qa.grade(20), "D")

    def test_empty_payload_rejected(self):
        with self.assertRaises(qa.QAError):
            qa.run_qa({"meta": {}, "slides": []}, self.limits, None, None)

    def test_report_markdown_lists_findings(self):
        report = qa.run_qa(deck([slide(1, "Cut-over finished early"), slide(2, bullets=[]), slide(3, "Approve October")]),
                           self.limits, None, None)
        markdown = qa.render_report(report)
        self.assertIn("| Slide | Code | Severity | Finding |", markdown)
        self.assertIn("QA103", markdown)


class CliTests(unittest.TestCase):
    def write_deck(self, tmp: str) -> Path:
        path = Path(tmp) / "deck.json"
        path.write_text(json.dumps(deck([
            slide(1, "Cut-over finished a quarter early"),
            slide(2),
            slide(3, "Approve the October window"),
        ])), encoding="utf-8")
        return path

    def test_clean_deck_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(qa.main([str(self.write_deck(tmp)), "--theme", "swiss"]), 0)

    def test_error_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deck.json"
            path.write_text(json.dumps(deck([slide(1, "Cut-over finished"), slide(2, bullets=[]), slide(3, "Ask")])),
                            encoding="utf-8")
            self.assertEqual(qa.main([str(path)]), 1)

    def test_strict_promotes_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deck.json"
            path.write_text(json.dumps(deck([
                slide(1, "Cut-over finished"), slide(2, title="Metrics dashboard"), slide(3, "Ask"),
            ])), encoding="utf-8")
            self.assertEqual(qa.main([str(path)]), 0)
            self.assertEqual(qa.main([str(path), "--strict"]), 1)

    def test_missing_file_exits_one(self):
        self.assertEqual(qa.main([str(ROOT / "does-not-exist.json")]), 1)

    def test_unknown_theme_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(qa.main([str(self.write_deck(tmp)), "--theme", "nope"]), 1)

    def test_report_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_deck(tmp)
            report_path = Path(tmp) / "qa.md"
            qa.main([str(path), "--report", str(report_path)])
            self.assertIn("Deck QA", report_path.read_text(encoding="utf-8"))

    def test_clean_deck_scores_full_marks(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(qa.main([str(self.write_deck(tmp)), "--theme", "consulting", "--strict"]), 0)

    def test_bundled_status_report_is_presentable(self):
        self.assertEqual(qa.main([str(ROOT / "examples" / "status-report.json")]), 0)


if __name__ == "__main__":
    unittest.main()
