#!/usr/bin/env python3
"""deck_lint - cross-check the artifacts that make up one deck pack.

A deck commonly ships as several files that are supposed to stay in sync:

    <slug>.md          Markdown deck            headline + bullets + short notes
    <slug>.json        output-contract payload  machine-readable twin
    <slug>-notes.md    rehearsal talk track     speaker-only notes
    <slug>.html        single-file HTML deck    presentable twin

The copies drift the moment one of them is edited alone - a renamed headline,
a slide added to the Markdown but not the HTML, a metric that reads 70% in one
file and 72% in another. deck_lint reads the pack and checks every artifact
against the JSON payload (the canonical structured form) and against the rules
in references/output-contract.md:

    * hard-gate errors - the pack is internally inconsistent and must be fixed
    * soft warnings    - worth a human look, but do not block the hand-off

Usage:
    python tools/deck_lint.py examples/status-report
    python tools/deck_lint.py examples/status-report --strict
    python tools/deck_lint.py examples/status-report --json

Exit status is 1 when a hard gate fails, 0 otherwise (with --strict, warnings
also fail the run). Standard library only - no dependencies.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
OK_MARK = "\u2713"
BAD_MARK = "\u2717"

# ---------------------------------------------------------------- conventions

REQUIRED_META = {
    "title": str,
    "audience": str,
    "purpose": str,
    "language": str,
    "target_minutes": (int, float),
    "slide_count": int,
    "est_minutes": (int, float),
}
REQUIRED_SLIDE = {
    "id": int,
    "title": str,
    "bullets": list,
    "visual": str,
    "speaker_notes": str,
    "est_seconds": int,
}
VALID_PURPOSE = {"inform", "persuade", "pitch", "report", "train"}

SCHEMA_VERSION = "1.0"
META_TIME_TOLERANCE = 0.11      # |est_minutes - round(sum(est_seconds)/60, 1)|
SLOT_DRIFT_WARN = 0.15          # contract: >15% drift between estimate and slot
BULLET_MAX = 5                  # over the cap is worth a warning
                                # (short decision / Q&A slides legitimately carry fewer)
NOTES_MIN_CHARS = 40            # speaker_notes talk-track floor
NOTES_MAX_CHARS = 480           # keep notes speakable in the slide slot
NOTES_MIN_LINES = 2             # prefer 2–3 cue lines per slide
NOTES_MIN_SECONDS = 20          # a real slide rarely speaks for <20s
SAY_SECONDS_TOLERANCE = 1
# Three-slot scale (minutes): same outline family may be rendered at these lengths.
DURATION_SLOTS = (3, 8, 15)

SLIDE_HEADING_RE = re.compile(r"^##\s+Slide\s+(\d+)\s*[\u2014\u2013-]\s*(.+?)\s*$", re.M)
NOTES_HEADER_RE = re.compile(
    r"^Slot:\s*(\d+(?:\.\d+)?)\s*min\s*\u00b7\s*Slides:\s*(\d+)\s*\u00b7\s*Language:\s*(\S+)\s*$",
    re.M,
)
SAY_RE = re.compile(r"^\*\*Say\s*\(~(\d+)s\):\*\*", re.M)
HTML_SECTION_RE = re.compile(
    r'<section class="slide"[^>]*?data-notes="([^"]*)"[^>]*?>(.*?)</section>', re.S
)
HTML_H1_RE = re.compile(r"<h1>(.*?)</h1>", re.S)
PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
RATIO_RE = re.compile(r"(\d+)\s*(?:of|/)\s*(\d+)", re.I)


class Finding:
    __slots__ = ("level", "code", "artifact", "message")

    def __init__(self, level: str, code: str, artifact: str, message: str) -> None:
        self.level = level          # "error" | "warning"
        self.code = code
        self.artifact = artifact
        self.message = message

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "artifact": self.artifact,
            "message": self.message,
        }


class Report:
    def __init__(self, base: str) -> None:
        self.base = base
        self.findings: list[Finding] = []
        self.artifacts: dict[str, bool] = {}

    def error(self, code: str, artifact: str, message: str) -> None:
        self.findings.append(Finding("error", code, artifact, message))

    def warn(self, code: str, artifact: str, message: str) -> None:
        self.findings.append(Finding("warning", code, artifact, message))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warning"]


# ------------------------------------------------------------------- parsing


def strip_markup(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return html_lib.unescape(text)


def parse_markdown(text: str) -> list[tuple[int, str]]:
    return [(int(n), title.strip()) for n, title in SLIDE_HEADING_RE.findall(text)]


def markdown_body_lines(text: str) -> str:
    """Markdown content that should carry the same numbers as the JSON payload.

    The trailing `Visual:` / `Notes:` lines are prose summaries and are excluded:
    the JSON payload is the numeric source of truth for those.
    """
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("Visual:", "Notes:")):
            continue
        if stripped.startswith("## Slide"):
            kept.append(stripped)
        elif stripped.startswith("- "):
            kept.append(stripped)
    return "\n".join(kept)


def parse_notes(text: str) -> dict:
    header = NOTES_HEADER_RE.search(text)
    entries = []
    parts = re.split(r"^##\s+Slide\s+", text, flags=re.M)[1:]
    for part in parts:
        first = part.splitlines()[0]
        m = re.match(r"(\d+)\s*[\u2014\u2013-]\s*(.+?)\s*$", first)
        say = SAY_RE.search(part)
        entries.append(
            {
                "num": int(m.group(1)) if m else None,
                "title": m.group(2).strip() if m else None,
                "say_seconds": int(say.group(1)) if say else None,
            }
        )
    return {
        "slot_minutes": float(header.group(1)) if header else None,
        "slide_count": int(header.group(2)) if header else None,
        "language": header.group(3) if header else None,
        "entries": entries,
    }


def parse_html(text: str) -> list[dict]:
    sections = []
    for notes_attr, body in HTML_SECTION_RE.findall(text):
        h1 = HTML_H1_RE.search(body)
        sections.append(
            {
                "title": strip_markup(h1.group(1)).strip() if h1 else None,
                "data_notes": html_lib.unescape(notes_attr).strip(),
                "text": strip_markup(body),
            }
        )
    return sections


# -------------------------------------------------------------- number drift


def number_tokens(text: str) -> set[str]:
    """Numeric claims that must agree wherever they appear in the pack."""
    tokens = {f"{v}%" for v in PERCENT_RE.findall(text)}
    tokens |= {f"{a}/{b}" for a, b in RATIO_RE.findall(text)}
    return tokens


# ------------------------------------------------------------------- checks


def check_json_payload(payload, report: Report) -> dict | None:
    art = "json"
    if not isinstance(payload, dict):
        report.error("json-root", art, "top level must be an object")
        return None

    for key in ("schema_version", "meta", "slides"):
        if key not in payload:
            report.error("json-missing-key", art, f"missing top-level key `{key}`")
    if any(k not in payload for k in ("meta", "slides")):
        return None

    if payload.get("schema_version") != SCHEMA_VERSION:
        report.error(
            "json-schema-version",
            art,
            f"schema_version must be \"{SCHEMA_VERSION}\", got {payload.get('schema_version')!r}",
        )

    meta = payload.get("meta")
    slides = payload.get("slides")
    if not isinstance(meta, dict) or not isinstance(slides, list):
        report.error("json-types", art, "`meta` must be an object and `slides` an array")
        return None

    for field, kind in REQUIRED_META.items():
        if field not in meta:
            report.error("json-meta-missing", art, f"meta.{field} is required")
        elif not isinstance(meta[field], kind) or isinstance(meta[field], bool):
            report.error("json-meta-type", art, f"meta.{field} has the wrong type")

    if isinstance(meta.get("purpose"), str) and meta["purpose"] not in VALID_PURPOSE:
        report.error(
            "json-meta-purpose",
            art,
            f"meta.purpose must be one of {sorted(VALID_PURPOSE)}, got {meta['purpose']!r}",
        )

    if isinstance(meta.get("slide_count"), int) and meta["slide_count"] != len(slides):
        report.error(
            "json-slide-count",
            art,
            f"meta.slide_count is {meta['slide_count']} but slides has {len(slides)} entries",
        )

    seconds = []
    for index, slide in enumerate(slides, start=1):
        where = f"slides[{index - 1}]"
        if not isinstance(slide, dict):
            report.error("json-slide-type", art, f"{where} must be an object")
            continue
        for field, kind in REQUIRED_SLIDE.items():
            if field not in slide:
                report.error("json-slide-missing", art, f"{where}.{field} is required")
            elif not isinstance(slide[field], kind) or isinstance(slide[field], bool):
                report.error("json-slide-type", art, f"{where}.{field} has the wrong type")
        if slide.get("id") != index:
            report.error(
                "json-slide-id",
                art,
                f"{where}.id is {slide.get('id')!r}, expected {index} (1-based, in order)",
            )
        bullets = slide.get("bullets")
        if isinstance(bullets, list) and len(bullets) > BULLET_MAX:
            report.warn(
                "json-bullet-count",
                art,
                f"{where}.bullets has {len(bullets)} items, the cap is {BULLET_MAX}",
            )
        notes = slide.get("speaker_notes")
        if isinstance(notes, str):
            stripped_notes = notes.strip()
            if not stripped_notes:
                report.error(
                    "json-notes-empty",
                    art,
                    f"{where}.speaker_notes is empty — every slide needs talk-track notes",
                )
            else:
                n_chars = len(stripped_notes)
                n_bullets = len(stripped_notes.splitlines())
                if n_chars < NOTES_MIN_CHARS:
                    report.warn(
                        "json-notes-short",
                        art,
                        f"{where}.speaker_notes has {n_chars} chars (< {NOTES_MIN_CHARS}); add cue points",
                    )
                if n_chars > NOTES_MAX_CHARS:
                    report.warn(
                        "json-notes-long",
                        art,
                        f"{where}.speaker_notes has {n_chars} chars (> {NOTES_MAX_CHARS}); trim for the slot",
                    )
                if n_bullets < NOTES_MIN_LINES:
                    report.warn(
                        "json-notes-few-lines",
                        art,
                        f"{where}.speaker_notes has {n_bullets} line(s); prefer 2–3 cue lines",
                    )
        elif "speaker_notes" in slide:
            report.error("json-slide-type", art, f"{where}.speaker_notes must be a string")
        if slide.get("est_seconds") is not None and not isinstance(slide.get("est_seconds"), int):
            report.error("json-slide-type", art, f"{where}.est_seconds must be an integer")
        elif isinstance(slide.get("est_seconds"), int):
            seconds.append(slide["est_seconds"])
            if slide["est_seconds"] < NOTES_MIN_SECONDS:
                report.warn(
                    "json-est-seconds-low",
                    art,
                    f"{where}.est_seconds is {slide['est_seconds']} (< {NOTES_MIN_SECONDS})",
                )

    if seconds and isinstance(meta.get("est_minutes"), (int, float)):
        derived = round(sum(seconds) / 60, 1)
        if abs(meta["est_minutes"] - derived) > META_TIME_TOLERANCE:
            report.error(
                "json-timing",
                art,
                f"meta.est_minutes is {meta['est_minutes']} but sum(est_seconds)/60 = {derived}",
            )
        slot = meta.get("target_minutes")
        if isinstance(slot, (int, float)) and slot:
            drift = abs(derived - slot) / slot
            if drift > SLOT_DRIFT_WARN:
                report.warn(
                    "json-slot-drift",
                    art,
                    f"estimated {derived} min against a {slot} min slot ({drift:.0%} drift > 15%)",
                )
            if slot not in DURATION_SLOTS and slot not in (2, 4, 5, 10, 20, 30, 45, 60):
                report.warn(
                    "json-slot-uncommon",
                    art,
                    f"meta.target_minutes is {slot}; common teaching slots are {list(DURATION_SLOTS)}",
                )

    return {"meta": meta, "slides": slides}


def check_markdown(md_slides: list[tuple[int, str]], canonical: list[tuple[int, str]], report: Report) -> None:
    art = "md"
    if len(md_slides) != len(canonical):
        report.error(
            "md-slide-count",
            art,
            f"Markdown has {len(md_slides)} slides, the JSON payload has {len(canonical)}",
        )
    for (mn, mt), (cn, ct) in zip(md_slides, canonical):
        if mn != cn:
            report.error("md-slide-number", art, f"Markdown slide {mn} is numbered {cn} in the JSON payload")
        if mt != ct:
            report.error("md-slide-title", art, f"slide {cn}: Markdown says {mt!r}, JSON says {ct!r}")


def check_notes(notes: dict, canonical: list[dict], report: Report) -> None:
    art = "notes"
    if notes["slide_count"] is None:
        report.error("notes-header", art, "missing `Slot: N min · Slides: N · Language: xx` header")
        return
    if notes["slide_count"] != len(canonical):
        report.error(
            "notes-slide-count",
            art,
            f"header says {notes['slide_count']} slides, the JSON payload has {len(canonical)}",
        )
    if len(notes["entries"]) != notes["slide_count"]:
        report.error(
            "notes-section-count",
            art,
            f"header says {notes['slide_count']} slides but {len(notes['entries'])} slide sections were found",
        )

    canonical_seconds = {
        s["id"]: s["est_seconds"] for s in canonical if isinstance(s.get("est_seconds"), int)
    }
    for entry in notes["entries"]:
        if entry["num"] is None:
            continue
        expected = canonical[entry["num"] - 1] if entry["num"] - 1 < len(canonical) else None
        if expected is not None and entry["title"] != expected.get("title"):
            report.error(
                "notes-slide-title",
                art,
                f"slide {entry['num']}: notes say {entry['title']!r}, JSON says {expected.get('title')!r}",
            )
        if entry["num"] in canonical_seconds and entry["say_seconds"] is not None:
            delta = abs(entry["say_seconds"] - canonical_seconds[entry["num"]])
            if delta > SAY_SECONDS_TOLERANCE:
                report.warn(
                    "notes-say-seconds",
                    art,
                    f"slide {entry['num']}: notes budget {entry['say_seconds']}s, JSON est_seconds "
                    f"{canonical_seconds[entry['num']]}s",
                )

    slot = canonical[0].get("_slot_minutes") if canonical else None
    if isinstance(slot, (int, float)) and notes["slot_minutes"] is not None:
        if abs(slot - notes["slot_minutes"]) > 0.01:
            report.warn(
                "notes-slot-minutes",
                art,
                f"header says {notes['slot_minutes']} min, meta.target_minutes is {slot}",
            )


def check_html(sections: list[dict], canonical: list[dict], report: Report) -> None:
    art = "html"
    if len(sections) != len(canonical):
        report.error(
            "html-slide-count",
            art,
            f"HTML has {len(sections)} <section class=\"slide\"> blocks, the JSON payload has {len(canonical)}",
        )
    for index, (section, slide) in enumerate(zip(sections, canonical), start=1):
        if section["title"] != slide.get("title"):
            report.error(
                "html-slide-title",
                art,
                f"slide {index}: HTML says {section['title']!r}, JSON says {slide.get('title')!r}",
            )
        if not section["data_notes"]:
            report.warn("html-missing-notes", art, f"slide {index} has an empty data-notes attribute")


def check_number_drift(md_numbers: set[str], json_numbers: set[str], html_numbers: set[str], report: Report) -> None:
    pairs = [("md", md_numbers, "json", json_numbers), ("html", html_numbers, "json", json_numbers)]
    for left_name, left, right_name, right in pairs:
        missing = left - right
        if missing:
            report.warn(
                "number-drift",
                left_name,
                f"numeric claims not present in the {right_name} payload: {', '.join(sorted(missing))}",
            )


def check_broken_links(text: str, report: Report, artifact: str) -> None:
    for line in text.splitlines():
        for target in re.findall(r"\]\(([^)\s]+)\)", line):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not re.match(r"^[\w./-]+$", target):
                report.warn("link-suspect", artifact, f"relative link looks malformed: {target}")


# ---------------------------------------------------------------------- main


def resolve_pack(target: Path) -> tuple[Path, dict[str, Path]]:
    if target.is_dir():
        json_files = sorted(target.glob("*.json"))
        if len(json_files) != 1:
            raise SystemExit(
                f"deck_lint: {target} is a directory; expected exactly one .json payload, found {len(json_files)}"
            )
        base = json_files[0].with_suffix("")
    else:
        base = target.with_suffix("") if target.suffix else target
    slug = base.name
    files = {
        "md": base.with_suffix(".md"),
        "json": base.with_suffix(".json"),
        "notes": base.parent / f"{slug}-notes.md",
        "html": base.with_suffix(".html"),
    }
    return base, files


def run(target: Path, allow_missing: bool) -> Report:
    base, files = resolve_pack(target)
    report = Report(str(base))

    texts: dict[str, str] = {}
    for name, path in files.items():
        exists = path.is_file()
        report.artifacts[name] = exists
        if exists:
            texts[name] = path.read_text(encoding="utf-8")
        elif not allow_missing:
            report.error("artifact-missing", name, f"{path} not found")

    if "json" not in texts:
        return report

    try:
        payload = json.loads(texts["json"])
    except json.JSONDecodeError as exc:
        report.error("json-parse", "json", f"{exc}")
        return report

    checked = check_json_payload(payload, report)
    if checked is None:
        return report

    meta, slides = checked["meta"], checked["slides"]
    canonical = [(s.get("id"), s.get("title")) for s in slides if isinstance(s, dict)]
    titles = [t for _, t in canonical]

    for slide in slides:
        if isinstance(slide, dict):
            slide["_slot_minutes"] = meta.get("target_minutes")

    json_text = json.dumps(
        [{"title": s.get("title"), "bullets": s.get("bullets"), "visual": s.get("visual")} for s in slides],
        ensure_ascii=False,
    )
    json_numbers = number_tokens(json_text)

    if "md" in texts:
        md_slides = parse_markdown(texts["md"])
        check_markdown(md_slides, canonical, report)
        check_broken_links(texts["md"], report, "md")
    else:
        md_slides = []

    if "notes" in texts:
        check_notes(parse_notes(texts["notes"]), slides, report)

    html_numbers: set[str] = set()
    if "html" in texts:
        sections = parse_html(texts["html"])
        check_html(sections, slides, report)
        html_numbers = number_tokens(" ".join(s["text"] for s in sections))

    md_numbers = number_tokens(markdown_body_lines(texts["md"])) if "md" in texts else set()
    check_number_drift(md_numbers, json_numbers, html_numbers, report)

    return report


def render_text(report: Report, quiet: bool) -> str:
    lines = [f"deck_lint  {report.base}"]
    marks = "  ".join(f"{name}{OK_MARK if ok else BAD_MARK}" for name, ok in report.artifacts.items())
    lines.append(f"  artifacts: {marks}")

    if not report.errors and not report.warnings and not quiet:
        lines.append("  pack is consistent - no hard-gate failures, no warnings")
        return "\n".join(lines)

    for label, items in (("ERROR", report.errors), ("WARNING", report.warnings)):
        if quiet and label == "WARNING":
            continue
        if not items:
            continue
        lines.append(f"  {label}S ({len(items)})")
        for finding in items:
            lines.append(f"    [{finding.code}] {finding.artifact}: {finding.message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="deck_lint",
        description="Cross-check the Markdown, JSON, notes and HTML copies of one deck pack.",
    )
    parser.add_argument("deck", help="deck base path or directory, e.g. examples/status-report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable report")
    parser.add_argument("--quiet", action="store_true", help="hide warnings in the text report")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="do not fail when an optional artifact (notes/HTML) is absent",
    )
    args = parser.parse_args(argv)

    report = run(Path(args.deck), args.allow_missing)

    if args.as_json:
        print(
            json.dumps(
                {
                    "deck": report.base,
                    "artifacts": report.artifacts,
                    "errors": [f.as_dict() for f in report.errors],
                    "warnings": [f.as_dict() for f in report.warnings],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(render_text(report, args.quiet))

    if report.errors:
        return EXIT_FAIL
    if args.strict and report.warnings:
        return EXIT_FAIL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
