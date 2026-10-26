#!/usr/bin/env python3
"""Apply a theme to a rendered .pptx: background, type, chart colours and table fills.

The renderer (`tools/render_pptx.py`) keeps the geometry honest and stays
theme-agnostic; this tool restyles an existing file. Split on purpose: you can
re-run the theme against a deck a designer has already touched, and you can
swap themes without re-emitting the payload.

    python tools/theme_apply.py deck.pptx --theme swiss
    python tools/theme_apply.py deck.pptx --theme assets/themes/editorial.json --out themed.pptx
    python tools/theme_apply.py --list
    python tools/theme_apply.py deck.pptx --theme swiss --check     # validate only

python-pptx is required (same optional dependency as the renderer). Without it
the tool exits 2 and prints the install line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_MISSING_DEP = 2

THEME_DIR = Path(__file__).resolve().parent.parent / "assets" / "themes"
REQUIRED_KEYS = ("name", "palette", "font", "size")
PALETTE_KEYS = ("bg", "ink", "muted", "accent", "band", "rule", "on_accent")
SIZE_KEYS = ("title", "section", "body", "footnote", "table")
# below these the deck is not readable in a room, whatever the brand book says
CONTRAST_FLOORS = {"ink": 7.0, "muted": 4.5, "accent": 3.0}
MIN_BODY_PT = 9.0


class ThemeError(Exception):
    pass


def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def import_pptx():
    try:
        from pptx import Presentation  # noqa: F401
        from pptx.dml.color import RGBColor  # noqa: F401
        from pptx.util import Pt  # noqa: F401
    except ImportError:
        return None
    import pptx
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Pt

    return {
        "available": True,
        "version": getattr(pptx, "__version__", "unknown"),
        "Presentation": Presentation,
        "RGBColor": RGBColor,
        "Pt": Pt,
    }


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as err:
        raise ThemeError(f"file not found: {path}") from err
    except json.JSONDecodeError as err:
        raise ThemeError(f"{path} is not valid JSON: {err}") from err


# ----------------------------------------------------------------- theme files


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"not a 6-digit hex colour: {value!r}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def relative_luminance(value: str) -> float:
    channels = []
    for raw in _hex_to_rgb(value):
        c = raw / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    high, low = sorted((relative_luminance(foreground), relative_luminance(background)), reverse=True)
    return round((high + 0.05) / (low + 0.05), 2)


def check_theme(theme: dict, where: str = "theme") -> list[str]:
    """Structural and legibility checks. Returns a list of error strings."""
    errors: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in theme:
            errors.append(f"{where}: missing '{key}'")

    palette = theme.get("palette") or {}
    for key in PALETTE_KEYS:
        value = palette.get(key)
        if not isinstance(value, str):
            errors.append(f"{where}: palette.{key} must be a hex string")
            continue
        try:
            _hex_to_rgb(value)
        except ValueError as err:
            errors.append(f"{where}: palette.{key} — {err}")

    if not errors:
        background = palette["bg"]
        for key, floor in CONTRAST_FLOORS.items():
            ratio = contrast_ratio(palette[key], background)
            if ratio < floor:
                errors.append(
                    f"{where}: palette.{key} on bg is {ratio}:1, below {floor}:1 — unreadable in a room"
                )
        on_accent = contrast_ratio(palette["on_accent"], palette["accent"])
        if on_accent < 3.0:
            errors.append(f"{where}: on_accent on accent is {on_accent}:1, below 3:1")

    size = theme.get("size") or {}
    for key in SIZE_KEYS:
        value = size.get(key)
        if not isinstance(value, (int, float)):
            errors.append(f"{where}: size.{key} must be a number")
        elif value < MIN_BODY_PT:
            errors.append(f"{where}: size.{key} is {value}pt, below the {MIN_BODY_PT}pt floor")
    if all(isinstance(size.get(k), (int, float)) for k in ("title", "body")) and size.get("title", 0) <= size.get("body", 0):
        errors.append(f"{where}: title size must exceed body size")

    font = theme.get("font") or {}
    for key in ("title", "body"):
        if not isinstance(font.get(key), str) or not font.get(key):
            errors.append(f"{where}: font.{key} must be a font name")

    series = theme.get("chart_series")
    if series is not None:
        if not isinstance(series, list) or not series:
            errors.append(f"{where}: chart_series must be a non-empty list")
        else:
            for index, colour in enumerate(series, start=1):
                try:
                    _hex_to_rgb(colour)
                except ValueError:
                    errors.append(f"{where}: chart_series[{index}] — {colour!r}")
    return errors


def available_themes() -> list[str]:
    if not THEME_DIR.is_dir():
        return []
    return sorted(path.stem for path in THEME_DIR.glob("*.json"))


def resolve_theme(spec: str, explicit_dir: Path | None = None) -> tuple[dict, str]:
    """`spec` is a bundled theme name or a path to a theme JSON."""
    candidate = Path(spec)
    if candidate.suffix.lower() == ".json" or candidate.exists():
        return load_json(candidate), str(candidate)
    theme_dir = explicit_dir or THEME_DIR
    path = theme_dir / f"{spec}.json"
    if not path.exists():
        names = ", ".join(available_themes()) or "none found"
        raise ThemeError(f"unknown theme '{spec}' (bundled: {names})")
    return load_json(path), str(path)


# ------------------------------------------------------------------ application


def _set_font(font, theme: dict, role: str, RGBColor, Pt) -> None:
    spec = theme["font"]
    font.name = spec.get("table") if role == "table" else spec.get("body")
    if role == "title":
        font.name = spec.get("title") or spec.get("body")
    size = theme["size"].get(role)
    if size:
        font.size = Pt(size)
    colour = theme["palette"]["muted"] if role == "footnote" else theme["palette"]["ink"]
    if role in ("title", "section"):
        colour = theme["palette"]["ink"]
    font.color.rgb = RGBColor(*_hex_to_rgb(colour))


def _paint_text_frame(text_frame, theme: dict, role: str, RGBColor, Pt) -> int:
    touched = 0
    for paragraph in text_frame.paragraphs:
        if role != "table" and role != "footnote":
            paragraph.line_spacing = 1.15
        for run in paragraph.runs:
            _set_font(run.font, theme, role, RGBColor, Pt)
            touched += 1
    return touched


def _paint_chart(chart, theme: dict, RGBColor) -> int:
    colours = theme.get("chart_series") or [theme["palette"]["accent"]]
    painted = 0
    for plot in chart.plots:
        is_pie = type(plot).__name__.lower().startswith(("pie", "doughnut"))
        for index, series in enumerate(plot.series):
            try:
                if is_pie:
                    for point_index, point in enumerate(series.points):
                        point.format.fill.solid()
                        point.format.fill.fore_color.rgb = RGBColor(
                            *_hex_to_rgb(colours[point_index % len(colours)])
                        )
                        painted += 1
                else:
                    series.format.fill.solid()
                    series.format.fill.fore_color.rgb = RGBColor(
                        *_hex_to_rgb(colours[index % len(colours)])
                    )
                    if getattr(series, "format", None) is not None:
                        series.format.line.color.rgb = RGBColor(*_hex_to_rgb(theme["palette"]["bg"]))
                    painted += 1
            except (AttributeError, ValueError, NotImplementedError):
                # chart XML that python-pptx cannot reach; the geometry still stands
                continue
    return painted


def _paint_table(table, theme: dict, RGBColor, Pt) -> int:
    painted = 0
    header_fill = theme.get("table_header_fill") or theme["palette"]["band"]
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(
                *_hex_to_rgb(header_fill if row_index == 0 else theme["palette"]["bg"])
            )
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    _set_font(run.font, theme, "table", RGBColor, Pt)
                    run.font.bold = row_index == 0
                    painted += 1
    return painted


def apply_theme(prs, theme: dict) -> dict:
    deps = import_pptx()
    if deps is None:  # pragma: no cover - guarded by caller
        raise ThemeError("python-pptx is not installed")
    RGBColor, Pt = deps["RGBColor"], deps["Pt"]

    warnings: list[str] = []
    slides_report: list[dict] = []
    background = RGBColor(*_hex_to_rgb(theme["palette"]["bg"]))

    for index, slide in enumerate(prs.slides, start=1):
        runs = charts = tables = 0
        try:
            fill = slide.background.fill
            fill.solid()
            fill.fore_color.rgb = background
        except (AttributeError, NotImplementedError, ValueError):
            warnings.append(f"slide {index}: background not settable on this master")

        title = slide.shapes.title
        for shape in slide.shapes:
            try:
                if shape.has_chart:
                    charts += _paint_chart(shape.chart, theme, RGBColor)
                    continue
                if shape.has_table:
                    tables += _paint_table(shape.table, theme, RGBColor, Pt)
                    continue
            except (AttributeError, ValueError):
                warnings.append(f"slide {index}: could not restyle {shape.shape_type}")
                continue

            if not shape.has_text_frame:
                continue
            is_title = title is not None and shape.shape_id == title.shape_id
            role = "title" if is_title else "body"
            frame_runs = _paint_text_frame(shape.text_frame, theme, role, RGBColor, Pt)
            runs += frame_runs
            if is_title and frame_runs == 0:
                # empty title placeholder on a template slide; nothing to restyle
                continue

        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame
            if notes is not None:
                _paint_text_frame(notes, theme, "footnote", RGBColor, Pt)

        slides_report.append({"slide": index, "runs": runs, "charts": charts, "tables": tables})

    return {
        "theme": theme.get("name"),
        "slides": slides_report,
        "restyled": {
            "runs": sum(entry["runs"] for entry in slides_report),
            "charts": sum(entry["charts"] for entry in slides_report),
            "tables": sum(entry["tables"] for entry in slides_report),
        },
        "warnings": warnings,
    }


# ------------------------------------------------------------------------ cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restyle a rendered .pptx with a bundled theme (references/themes.md).",
    )
    parser.add_argument("pptx", nargs="?", help="deck to restyle")
    parser.add_argument("--theme", help="bundled theme name (consulting / swiss / editorial) or a theme JSON path")
    parser.add_argument("--themes-dir", help="directory of theme JSON files (default: assets/themes)")
    parser.add_argument("--list", action="store_true", help="list bundled themes and exit")
    parser.add_argument("--out", help="output path (default: <deck>_<theme>.pptx)")
    parser.add_argument("--check", action="store_true", help="validate the theme only, write nothing")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output file")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdout()
    args = build_parser().parse_args(argv)
    themes_dir = Path(args.themes_dir) if args.themes_dir else None

    if args.list:
        themes = available_themes()
        if args.json:
            print(json.dumps({"themes": themes, "dir": str(themes_dir or THEME_DIR)}, indent=2))
        else:
            for name in themes:
                print(name)
        return EXIT_OK

    if not args.pptx or not args.theme:
        print("ERROR a deck and --theme are required (or use --list)", file=sys.stderr)
        return EXIT_FAIL

    try:
        theme, theme_source = resolve_theme(args.theme, themes_dir)
        errors = check_theme(theme, where=theme.get("name") or theme_source)
        if errors:
            raise ThemeError("theme invalid:\n  - " + "\n  - ".join(errors))
        if args.check:
            print(f"theme ok: {theme.get('name')} ({theme_source})")
            print(f"  ink on bg      {contrast_ratio(theme['palette']['ink'], theme['palette']['bg'])}:1")
            print(f"  muted on bg    {contrast_ratio(theme['palette']['muted'], theme['palette']['bg'])}:1")
            print(f"  accent on bg   {contrast_ratio(theme['palette']['accent'], theme['palette']['bg'])}:1")
            return EXIT_OK

        deps = import_pptx()
        if deps is None:
            print("python-pptx is not installed. Run: pip install python-pptx", file=sys.stderr)
            return EXIT_MISSING_DEP

        source = Path(args.pptx)
        if not source.exists():
            raise ThemeError(f"deck not found: {source}")
        out_path = Path(args.out) if args.out else source.with_name(f"{source.stem}_{theme['name']}.pptx")
        if out_path.exists() and not args.force and out_path != source:
            raise ThemeError(f"output exists: {out_path} (pass --force)")

        prs = deps["Presentation"](str(source))
        report = apply_theme(prs, theme)
        prs.save(str(out_path))
        report["output"] = str(out_path)
        report["source"] = str(source)
    except ThemeError as err:
        print(f"ERROR {err}", file=sys.stderr)
        return EXIT_FAIL

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        restyled = report["restyled"]
        print(f"themed {report['source']} -> {report['output']}  ({report['theme']})")
        print(f"  {restyled['runs']} runs, {restyled['charts']} chart series, {restyled['tables']} table cells restyled")
        for warning in report["warnings"]:
            print(f"  warning: {warning}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
