#!/usr/bin/env python3
"""Visual QA for a deck payload: density, data slides, pace and colour legibility.

`tools/deck_lint.py` checks that the copies of a deck agree with each other.
This tool asks a different question: will the slides work in a room? It reads
the payload, the layout library (`assets/layouts.json`) for per-role copy limits
and, optionally, a theme for colour contrast.

    python tools/deck_qa.py deck.json
    python tools/deck_qa.py deck.json --theme swiss --report qa.md
    python tools/deck_qa.py deck.json --strict        # warnings fail too
    python tools/deck_qa.py deck.json --json

Standard library only. Exit 1 on any error (or on a warning with --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LAYOUTS = ROOT / "assets" / "layouts.json"
DEFAULT_THEME_DIR = ROOT / "assets" / "themes"

# copy budgets when no layout library is supplied
FALLBACK_LIMITS = {
    "default": {"bullets": [1, 5], "words_per_bullet": 12, "headline_words": 14},
}
SPEAKING_WORDS_PER_SECOND = 3.2   # above this the notes cannot be said in the slot
SLIDE_WORD_BUDGET = 45            # on-screen copy above this stops being read
CONSECUTIVE_OPENERS = 3           # same first word on N slides in a row reads as a template
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

SEVERITY_ERROR = "error"
SEVERITY_WARN = "warn"
SEVERITY_INFO = "info"          # opportunities, not defects — never cost a point
PENALTY = {SEVERITY_ERROR: 15, SEVERITY_WARN: 5, SEVERITY_INFO: 0}


class QAError(Exception):
    pass


def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as err:
        raise QAError(f"file not found: {path}") from err
    except json.JSONDecodeError as err:
        raise QAError(f"{path} is not valid JSON: {err}") from err


# ------------------------------------------------------------------ measuring


def text_weight(text: str) -> float:
    """Reading load of a line: Latin words plus CJK characters (two per word)."""
    if not isinstance(text, str) or not text.strip():
        return 0.0
    cjk = len(CJK_RE.findall(text))
    latin = len(CJK_RE.sub(" ", text).split())
    return round(latin + cjk / 2.0, 1)


MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
)


def _is_date(text: str, token: str, start: int, end: int) -> bool:
    """`15 October`, `October 15` and a bare year are dates, not figures to compare."""
    digits = re.sub(r"[^\d]", "", token)
    if len(digits) == 4 and 1900 <= int(digits) <= 2099:
        return True
    following = text[end:end + 12].strip().split()
    if following and following[0].strip(".,;:").lower() in MONTHS:
        return True
    before = text[:start].strip().split()
    if before and before[-1].strip(".,;:").lower() in MONTHS:
        return True
    return False


def slide_numbers(slide: dict) -> list[str]:
    """Digit-bearing tokens on the slide, used to spot a data slide drawn as prose."""
    found: list[str] = []
    texts = [slide.get("title", "")]
    texts.extend(slide.get("bullets") or [])
    for text in texts:
        if not isinstance(text, str):
            continue
        for match in re.finditer(r"[+-]?\d[\d,.]*\s?%?", text):
            token = match.group(0).strip()
            if len(re.sub(r"[^\d]", "", token)) < 2:
                continue
            if _is_date(text, token, match.start(), match.end()):
                continue
            found.append(token)
    return found


# -------------------------------------------------------------------- library


def load_limits(path: Path | None) -> tuple[dict, dict]:
    """Return (limits-by-role, raw library). Missing file falls back to defaults."""
    if path is None or not path.exists():
        return dict(FALLBACK_LIMITS), {}
    library = load_json(path)
    roles = library.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise QAError(f"{path} has no 'roles' object")
    limits: dict[str, dict] = {}
    for role_id, spec in roles.items():
        variants = spec.get("variants") or []
        bullets = [tuple(v.get("limits", {}).get("bullets", [1, 5])) for v in variants]
        words = [v.get("limits", {}).get("words_per_bullet", 12) for v in variants]
        heads = [v.get("limits", {}).get("headline_words", 14) for v in variants]
        limits[role_id] = {
            "bullets": [min(b[0] for b in bullets), max(b[1] for b in bullets)],
            "words_per_bullet": max(words),
            "headline_words": max(heads),
        }
    return limits, library


def infer_role(index: int, total: int, slide: dict) -> str:
    if index == 0:
        return "title"
    if index == total - 1:
        return "closing"
    if isinstance(slide.get("chart"), dict):
        return "chart"
    if isinstance(slide.get("table"), dict):
        return "table"
    return "bullet-list"


# ----------------------------------------------------------------------- rules


def finding(code: str, severity: str, slide_no: int | None, message: str) -> dict:
    return {"code": code, "severity": severity, "slide": slide_no, "message": message}


def check_slide(slide: dict, index: int, total: int, limits: dict) -> list[dict]:
    issues: list[dict] = []
    number = slide.get("id", index + 1)
    role = infer_role(index, total, slide)
    budget = limits.get(role) or limits.get("bullet-list") or FALLBACK_LIMITS["default"]
    title = slide.get("title") or ""
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str) and b.strip()]
    notes = slide.get("speaker_notes") or ""
    has_data = isinstance(slide.get("chart"), dict) or isinstance(slide.get("table"), dict)

    headline_weight = text_weight(title)
    if headline_weight > budget["headline_words"]:
        issues.append(finding(
            "QA101", SEVERITY_WARN, number,
            f"headline is {headline_weight:g} words of reading load; the room reads about "
            f"{budget['headline_words']} before the slide stops being a headline",
        ))
    elif 0 < headline_weight <= 2 and role != "title":
        issues.append(finding(
            "QA102", SEVERITY_WARN, number,
            f"headline '{title}' is a label, not a claim — say what changed",
        ))

    low, high = budget["bullets"]
    if not bullets and role not in ("title", "closing") and not has_data:
        issues.append(finding("QA103", SEVERITY_ERROR, number, "no bullets on a body slide"))
    elif len(bullets) > 5:
        issues.append(finding(
            "QA103", SEVERITY_ERROR, number,
            f"{len(bullets)} bullets; five is the ceiling before the slide becomes a document",
        ))
    elif len(bullets) > high:
        issues.append(finding(
            "QA103", SEVERITY_WARN, number,
            f"{len(bullets)} bullets; the inferred '{role}' layout takes {high}",
        ))
    elif len(bullets) < low and role not in ("title", "closing"):
        issues.append(finding(
            "QA103", SEVERITY_WARN, number,
            f"{len(bullets)} bullets; the inferred '{role}' layout expects at least {low}",
        ))

    for bullet_index, bullet in enumerate(bullets, start=1):
        weight = text_weight(bullet)
        if weight > budget["words_per_bullet"]:
            issues.append(finding(
                "QA104", SEVERITY_WARN, number,
                f"bullet {bullet_index} is {weight:g} words; trim to {budget['words_per_bullet']}",
            ))

    numbers = slide_numbers(slide)
    if numbers and not has_data and role not in ("title", "closing"):
        issues.append(finding(
            "QA105", SEVERITY_INFO, number,
            f"carries figures ({', '.join(numbers[:3])}) but no chart/table — the audience has to "
            "imagine the comparison",
        ))

    if has_data and len(bullets) > 3:
        issues.append(finding(
            "QA106", SEVERITY_WARN, number,
            f"{len(bullets)} bullets beside a data block; keep 3 and move the rest to the notes",
        ))

    if not notes.strip():
        issues.append(finding("QA107", SEVERITY_ERROR, number, "no speaker notes"))
    else:
        seconds = slide.get("est_seconds")
        if isinstance(seconds, (int, float)) and seconds > 0:
            pace = text_weight(notes) / float(seconds)
            if pace > SPEAKING_WORDS_PER_SECOND:
                issues.append(finding(
                    "QA108", SEVERITY_WARN, number,
                    f"notes read at {pace:.1f} words/s over {seconds}s — either lengthen est_seconds "
                    "or cut a sentence",
                ))

    if not (slide.get("visual") or "").strip():
        issues.append(finding("QA109", SEVERITY_ERROR, number, "no visual suggestion"))

    body_weight = text_weight(title) + sum(text_weight(b) for b in bullets)
    if body_weight > SLIDE_WORD_BUDGET:
        issues.append(finding(
            "QA110", SEVERITY_WARN, number,
            f"{body_weight:g} words on screen; above {SLIDE_WORD_BUDGET} the slide competes with the speaker",
        ))

    chart = slide.get("chart")
    if isinstance(chart, dict):
        categories = chart.get("categories") or []
        series = chart.get("series") or []
        if len(series) > 3:
            issues.append(finding("QA111", SEVERITY_WARN, number, f"{len(series)} series in one chart; three is the limit for a projected slide"))
        if len(categories) > 8:
            issues.append(finding("QA111", SEVERITY_WARN, number, f"{len(categories)} categories; group the tail"))
        if str(chart.get("type", "")).lower() in ("pie", "doughnut") and len(categories) > 6:
            issues.append(finding("QA111", SEVERITY_WARN, number, f"{len(categories)} slices in a pie; use a bar chart"))

    table = slide.get("table")
    if isinstance(table, dict):
        rows = table.get("rows") or []
        if len(rows) > 6:
            issues.append(finding("QA112", SEVERITY_WARN, number, f"{len(rows)} rows; six is what a projected table can carry"))
        for row_index, row in enumerate(rows, start=1):
            for cell in row if isinstance(row, list) else []:
                if text_weight(str(cell)) > 6:
                    issues.append(finding(
                        "QA112", SEVERITY_WARN, number,
                        f"table cell r{row_index} reads as a sentence; cells are labels",
                    ))
                    break
    return issues


def check_variety(slides: list[dict]) -> list[dict]:
    issues: list[dict] = []
    openers: list[str] = []
    for slide in slides:
        words = str(slide.get("title") or "").split()
        openers.append(words[0].strip(".,:;!?").lower() if words else "")
    run = 1
    for index in range(1, len(openers)):
        if openers[index] and openers[index] == openers[index - 1]:
            run += 1
            if run == CONSECUTIVE_OPENERS:
                slide_no = slides[index].get("id", index + 1)
                issues.append(finding(
                    "QA113", SEVERITY_WARN, slide_no,
                    f"three headlines in a row open with '{openers[index]}' — it reads as a template",
                ))
        else:
            run = 1
    return issues


def check_theme(spec: str, theme_dir: Path | None) -> list[dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from theme_apply import ThemeError, check_theme, resolve_theme  # type: ignore
    except ImportError as err:  # pragma: no cover
        raise QAError(f"theme_apply.py is required for --theme: {err}") from err
    try:
        theme, source = resolve_theme(spec, theme_dir)
    except ThemeError as err:
        raise QAError(str(err)) from err
    issues = [
        finding("QA114", SEVERITY_ERROR, None, message)
        for message in check_theme(theme, where=theme.get("name") or source)
    ]
    return issues


def grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def run_qa(payload: dict, limits: dict, theme_spec: str | None, theme_dir: Path | None) -> dict:
    slides = payload.get("slides")
    if not isinstance(slides, list) or not slides:
        raise QAError("payload has no slides")
    issues: list[dict] = []
    for index, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        issues.extend(check_slide(slide, index, len(slides), limits))
    issues.extend(check_variety([s for s in slides if isinstance(s, dict)]))
    if theme_spec:
        issues.extend(check_theme(theme_spec, theme_dir))

    errors = sum(1 for issue in issues if issue["severity"] == SEVERITY_ERROR)
    warnings = sum(1 for issue in issues if issue["severity"] == SEVERITY_WARN)
    infos = sum(1 for issue in issues if issue["severity"] == SEVERITY_INFO)
    score = max(0, 100 - errors * PENALTY[SEVERITY_ERROR] - warnings * PENALTY[SEVERITY_WARN])
    return {
        "slides": len(slides),
        "score": score,
        "grade": grade(score),
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "issues": issues,
    }


def render_report(report: dict) -> str:
    lines = [
        f"# Deck QA — {report['score']} / 100 ({report['grade']})",
        "",
        f"{report['slides']} slides · {report['errors']} errors · {report['warnings']} warnings "
        f"· {report['infos']} notes",
        "",
    ]
    if not report["issues"]:
        lines.append("No findings. The deck passes the visual checks.")
        return "\n".join(lines) + "\n"
    lines.extend(["| Slide | Code | Severity | Finding |", "|-------|------|----------|---------|"])
    for issue in report["issues"]:
        slide = "deck" if issue["slide"] is None else str(issue["slide"])
        lines.append(f"| {slide} | {issue['code']} | {issue['severity']} | {issue['message']} |")
    lines.extend(["", "Codes are documented in `references/visual-qa.md`."])
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------ cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visual QA for a deck payload (density, data slides, pace, contrast).",
    )
    parser.add_argument("payload", help="deck payload JSON (see references/output-contract.md)")
    parser.add_argument("--layouts", help=f"layout library (default: {DEFAULT_LAYOUTS.name})")
    parser.add_argument("--theme", help="bundled theme name or theme JSON path; adds the contrast check")
    parser.add_argument("--themes-dir", help="directory of theme JSON files (default: assets/themes)")
    parser.add_argument("--strict", action="store_true", help="warnings fail the run too")
    parser.add_argument("--report", help="write the findings as Markdown to this path")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdout()
    args = build_parser().parse_args(argv)

    try:
        payload = load_json(Path(args.payload))
        limits_path = Path(args.layouts) if args.layouts else DEFAULT_LAYOUTS
        limits, _library = load_limits(limits_path)
        theme_dir = Path(args.themes_dir) if args.themes_dir else DEFAULT_THEME_DIR
        report = run_qa(payload, limits, args.theme, theme_dir)
    except QAError as err:
        print(f"ERROR {err}", file=sys.stderr)
        return EXIT_FAIL

    if args.report:
        Path(args.report).write_text(render_report(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"deck qa: {report['slides']} slides, score {report['score']} ({report['grade']})")
        for issue in report["issues"]:
            slide = "-" if issue["slide"] is None else str(issue["slide"])
            print(f"  slide {slide:>3}  {issue['code']}  {issue['severity']:<5} {issue['message']}")
        print(f"  {report['errors']} errors, {report['warnings']} warnings, {report['infos']} notes")

    if report["errors"] or (args.strict and report["warnings"]):
        return EXIT_FAIL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
