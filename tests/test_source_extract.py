#!/usr/bin/env python3
"""Tests for tools/source_extract.py - standard library only.

Run with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "source_extract.py"
sys.path.insert(0, str(ROOT / "tools"))

import source_extract as se  # noqa: E402


def write(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class MarkdownTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def test_sections_follow_headings(self) -> None:
        path = write(self.tmp, "brief.md", (
            "# Quarterly review\n\nOpening paragraph.\n\n"
            "## Revenue\n\nRevenue grew 18% to $4.2M.\n\n"
            "### Retention\n\nNet retention reached 112%.\n\n"
            "## Costs\n\nHeadcount flat at 42 people.\n"
        ))
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertTrue(entry["ok"])
        headings = [s["heading"] for s in entry["sections"]]
        self.assertEqual(headings, ["Quarterly review", "Revenue", "Retention", "Costs"])
        levels = [s["level"] for s in entry["sections"]]
        self.assertEqual(levels, [1, 2, 3, 2])

    def test_chunks_carry_id_path_and_section(self) -> None:
        body = "\n".join(f"Sentence number {i} about the market." for i in range(200))
        path = write(self.tmp, "long.md", f"# Market\n\n{body}\n")
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertGreater(len(entry["chunks"]), 1)
        first = entry["chunks"][0]
        self.assertEqual(first["section"], "Market")
        self.assertIn("long.md#1", first["id"])
        self.assertTrue(first["path"].endswith("long.md"))
        self.assertLessEqual(first["chars"], se.DEFAULT_CHUNK_CHARS)

    def test_chunk_ids_are_unique_across_sections(self) -> None:
        body = "\n".join(f"Sentence number {i} about the market." for i in range(200))
        path = write(self.tmp, "multi.md", f"# One\n\n{body}\n\n# Two\n\n{body}\n")
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertGreater(len(entry["sections"]), 1)
        ids = [c["id"] for c in entry["chunks"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(i.endswith("multi.md#1") for i in ids))
        self.assertTrue(any(i.endswith("multi.md#2") for i in ids))

    def test_max_chars_truncates_and_warns(self) -> None:
        path = write(self.tmp, "big.md", "# T\n\n" + ("word " * 5000))
        entry = se.read_source(path, 500)
        self.assertTrue(entry["truncated"])
        self.assertEqual(entry["chars"], 500)
        self.assertTrue(any("truncated" in w for w in entry["warnings"]))


class NumberTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def test_percent_currency_count_and_multiplier(self) -> None:
        path = write(self.tmp, "metrics.md", (
            "# Metrics\n\n"
            "Conversion rose 18% in Q3.\n"
            "Revenue reached $4.2M, up 3x year over year.\n"
            "We served 12,480 customers.\n"
        ))
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        values = {n["value"] for n in entry["numbers"]}
        kinds = {n["kind"] for n in entry["numbers"]}
        self.assertIn("18%", values)
        self.assertIn("$4.2M", values)
        self.assertIn("12,480", values)
        self.assertTrue({"percent", "currency", "count"} <= kinds)

    def test_context_is_a_sentence_and_deduped(self) -> None:
        path = write(self.tmp, "dup.md", (
            "# Dup\n\nChurn fell to 4%.\n\nChurn fell to 4%.\n"
        ))
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        percents = [n for n in entry["numbers"] if n["value"] == "4%"]
        self.assertEqual(len(percents), 1)
        self.assertIn("Churn", percents[0]["context"])

    def test_chinese_percent_and_units(self) -> None:
        path = write(self.tmp, "zh.md", "# 结论\n\n本季度毛利率提升 6.5%，营收达 2.4 亿元。\n")
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        values = {n["value"] for n in entry["numbers"]}
        self.assertIn("6.5%", values)

    def test_percent_without_space_after_cjk(self) -> None:
        path = write(self.tmp, "zh2.md", "# 结论\n\n毛利率提升6.5%，续费率92%。\n")
        values = {n["value"] for n in se.read_source(path, se.DEFAULT_MAX_CHARS)["numbers"]}
        self.assertEqual(values, {"6.5%", "92%"})

    def test_grouped_thousands_not_cut_at_the_comma(self) -> None:
        path = write(self.tmp, "counts.md",
                     "# Counts\n\nWe served 12,480 customers across 20,000 visits.\n")
        values = {n["value"] for n in se.read_source(path, se.DEFAULT_MAX_CHARS)["numbers"]}
        self.assertIn("12,480", values)
        self.assertIn("20,000", values)
        self.assertFalse([v for v in values if v.endswith(",")], values)

    def test_version_strings_do_not_leak_fragments(self) -> None:
        path = write(self.tmp, "ver.md", "# Ver\n\nUpgraded to v1.5.2 and v2.0.0 in Q3.\n")
        values = {n["value"] for n in se.read_source(path, se.DEFAULT_MAX_CHARS)["numbers"]}
        self.assertFalse(values, values)

    def test_magnitude_without_currency_symbol(self) -> None:
        path = write(self.tmp, "mag.md", "# 规模\n\n营收 2.4 亿元，客户 12 万家。\n")
        records = se.read_source(path, se.DEFAULT_MAX_CHARS)["numbers"]
        values = {n["value"] for n in records}
        self.assertIn("2.4 亿", values)
        self.assertTrue(all(n["kind"] == "magnitude" for n in records
                            if n["value"].endswith("亿")), records)

    def test_currency_symbol_is_not_double_counted(self) -> None:
        path = write(self.tmp, "cur.md", "# Cur\n\nRevenue reached $4.2M in Q3.\n")
        values = [n["value"] for n in se.read_source(path, se.DEFAULT_MAX_CHARS)["numbers"]]
        self.assertIn("$4.2M", values)
        self.assertNotIn("4.2M", values)

    def test_empty_binary_document_warns(self) -> None:
        try:
            import docx  # noqa: F401
        except ImportError:
            self.skipTest("python-docx not installed")
        tmp = Path(tempfile.mkdtemp())
        path = tmp / "empty.docx"
        import docx
        docx.Document().save(str(path))
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertTrue(entry["ok"])
        self.assertTrue(any("no extractable text" in w for w in entry["warnings"]))

    def test_evidence_wrapper_mirrors_numbers(self) -> None:
        path = write(self.tmp, "m.md", "# M\n\nGrowth was 9%.\n")
        brief = se.build_brief([path], se.DEFAULT_MAX_CHARS)
        self.assertTrue(brief["evidence"])
        record = brief["evidence"][0]
        self.assertEqual(record["kind"], "number")
        self.assertEqual(record["value"], "9%")
        self.assertTrue(record["source"]["path"].endswith("m.md"))


class TableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def test_csv_becomes_header_and_rows(self) -> None:
        path = write(self.tmp, "funnel.csv",
                     "stage,count,conversion\nvisit,12000,0.32\nsignup,3840,0.18\n")
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertEqual(len(entry["tables"]), 1)
        table = entry["tables"][0]
        self.assertEqual(table["header"], ["stage", "count", "conversion"])
        self.assertEqual(table["row_count"], 2)
        self.assertEqual(table["rows"][0][0], "visit")

    def test_tsv_is_supported(self) -> None:
        path = write(self.tmp, "t.tsv", "a\tb\n1\t2\n")
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertEqual(entry["tables"][0]["header"], ["a", "b"])


class HtmlTests(unittest.TestCase):
    def test_title_headings_and_text(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        path = write(tmp, "page.html", (
            "<html><head><title>Launch plan</title>"
            "<style>body{color:red}</style></head><body>"
            "<h1>Overview</h1><p>We ship in <b>Q4</b> with 30% margin.</p>"
            "<h2>Risks</h2><p>One vendor is single-sourced.</p>"
            "<script>var x = 1;</script></body></html>"
        ))
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        self.assertEqual(entry["title"], "Launch plan")
        headings = [s["heading"] for s in entry["sections"]]
        self.assertIn("Overview", headings)
        self.assertIn("Risks", headings)
        joined = " ".join(s["text"] for s in entry["sections"])
        self.assertIn("Q4", joined)
        self.assertNotIn("color:red", joined)
        self.assertNotIn("var x", joined)


class DegradationTests(unittest.TestCase):
    def test_missing_file_reports_instead_of_raising(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        entry = se.read_source(tmp / "nope.pdf", se.DEFAULT_MAX_CHARS)
        self.assertFalse(entry["ok"])
        self.assertEqual(entry["error"], "file not found")

    def test_optional_parser_missing_is_actionable(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        path = write(tmp, "fake.pdf", "%PDF-1.4 not really")
        entry = se.read_source(path, se.DEFAULT_MAX_CHARS)
        try:
            import pypdf  # noqa: F401
            has_pypdf = True
        except ImportError:
            try:
                import PyPDF2  # noqa: F401
                has_pypdf = True
            except ImportError:
                has_pypdf = False
        if not has_pypdf:
            self.assertFalse(entry["ok"])
            self.assertIn("pip install", entry["error"])

    def test_brief_survives_one_bad_input(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        good = write(tmp, "ok.md", "# OK\n\nFine.\n")
        brief = se.build_brief([good, tmp / "missing.docx"], se.DEFAULT_MAX_CHARS)
        self.assertEqual(brief["stats"]["documents"], 2)
        self.assertEqual(brief["stats"]["documents_ok"], 1)
        self.assertTrue(any("could not be read" in w for w in brief["warnings"]))

    def test_empty_brief_warns(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        brief = se.build_brief([tmp / "absent.md"], se.DEFAULT_MAX_CHARS)
        self.assertEqual(brief["stats"]["documents_ok"], 0)
        self.assertTrue(any("brief is empty" in w for w in brief["warnings"]))


class CollectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def test_directory_walk_is_sorted_and_deduped(self) -> None:
        write(self.tmp, "docs/b.md", "# B\n")
        write(self.tmp, "docs/a.md", "# A\n")
        write(self.tmp, "docs/.hidden.md", "# H\n")
        files, missing = se.collect_files([str(self.tmp / "docs")], recursive=False)
        self.assertEqual([f.name for f in files], ["a.md", "b.md"])
        self.assertEqual(missing, [])
        dupes, _ = se.collect_files(
            [str(self.tmp / "docs" / "a.md"), str(self.tmp / "docs" / "a.md")], False)
        self.assertEqual(len(dupes), 1)

    def test_recursive_picks_nested_files(self) -> None:
        write(self.tmp, "docs/deep/c.md", "# C\n")
        files, _ = se.collect_files([str(self.tmp / "docs")], recursive=True)
        self.assertTrue(any(f.name == "c.md" for f in files))


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOL), *args],
            capture_output=True, text=True, encoding="utf-8")

    def test_writes_brief_and_exit_zero(self) -> None:
        src = write(self.tmp, "deck.md", "# Deck\n\nMargin held at 30%.\n")
        out = self.tmp / "out" / "brief.json"
        result = self.run_cli(str(src), "--out", str(out), "--quiet")
        self.assertEqual(result.returncode, 0, result.stderr)
        brief = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(brief["schema"], se.SCHEMA)
        self.assertEqual(brief["stats"]["documents_ok"], 1)

    def test_print_mode_goes_to_stdout(self) -> None:
        src = write(self.tmp, "deck.md", "# Deck\n\nHello.\n")
        result = self.run_cli(str(src), "--print")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["schema"], se.SCHEMA)

    def test_all_inputs_missing_exits_nonzero(self) -> None:
        result = self.run_cli(str(self.tmp / "ghost.pdf"), "--print")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
