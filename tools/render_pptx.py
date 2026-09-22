#!/usr/bin/env python3
"""render_pptx - render an output-contract deck payload to a .pptx file.

Optional handoff step for the One-Click AI PPT skill. Reads the structured
payload described in references/output-contract.md and writes one PowerPoint
slide per payload slide, into the bundled Office master or a corporate template
supplied with --template.

    python tools/render_pptx.py examples/status-report.json
    python tools/render_pptx.py deck.json --template acme.potx --master-map acme-master-map.json
    python tools/render_pptx.py deck.json --check
    python tools/render_pptx.py deck.json --out out/acme_deck_v1.0.0_20260922.pptx

Conventions:
    * layout + placeholder resolution - references/master-mapping.md
    * output file naming              - references/export-checklist.md
    * payload schema                  - references/output-contract.md

Requires python-pptx (pip install python-pptx); the deck checker
tools/deck_lint.py stays dependency-free. Exit codes: 0 ok, 1 hard failure,
2 missing dependency.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_MISSING_DEP = 2

SCHEMA_VERSION = "1.0"
ROLES = ("title", "content", "section", "closing")
DEFAULT_LAYOUT_INDEX = {"title": 0, "content": 1}
DEFAULT_VERSION = "v1.0.0"

SLUG_RE = re.compile(r"[^a-z0-9]+")


class RenderError(Exception):
    """Hard failure: bad payload, unreadable template or mapping."""


# ------------------------------------------------------------------- utilities


def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def slugify(text: str, fallback: str = "deck") -> str:
    slug = SLUG_RE.sub("-", text.strip().lower()).strip("-")
    return slug or fallback


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as err:
        raise RenderError(f"file not found: {path}") from err
    except json.JSONDecodeError as err:
        raise RenderError(f"invalid JSON in {path}: {err}") from err


def import_pptx():
    try:
        from pptx import Presentation
        from pptx.enum.shapes import PP_PLACEHOLDER
        from pptx.util import Inches
    except ImportError:
        print(
            "python-pptx is not installed; rendering skipped.\n"
            "    pip install python-pptx\n"
            "The no-dependency path is still available: hand over the Markdown "
            "deck and the JSON payload.",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_MISSING_DEP)
    return Presentation, PP_PLACEHOLDER, Inches


# -------------------------------------------------------------------- payload


def validate_payload(data: dict) -> list[str]:
    """Return hard errors; the payload must be clean before rendering."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["payload root must be an object"]

    meta = data.get("meta")
    slides = data.get("slides")
    if not isinstance(meta, dict):
        errors.append("meta object is missing")
        meta = {}
    if not isinstance(slides, list) or not slides:
        errors.append("slides array is missing or empty")
        slides = []

    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("meta.title is empty")

    declared = meta.get("slide_count")
    if declared is not None and declared != len(slides):
        errors.append(f"meta.slide_count ({declared}) != len(slides) ({len(slides)})")

    schema = data.get("schema_version")
    if schema is not None and str(schema) != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version {schema!r} (expected {SCHEMA_VERSION!r})")

    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            errors.append(f"slide {index} is not an object")
            continue
        headline = slide.get("title")
        if not isinstance(headline, str) or not headline.strip():
            errors.append(f"slide {index} has no title")
        bullets = slide.get("bullets")
        if not isinstance(bullets, list) or not bullets:
            errors.append(f"slide {index} has no bullets")
        elif not all(isinstance(item, str) and item.strip() for item in bullets):
            errors.append(f"slide {index} has an empty bullet")
    return errors


# ------------------------------------------------------------ master mapping


def resolve_layout_config(mapping: dict | None) -> dict:
    layouts = {}
    if isinstance(mapping, dict):
        raw = mapping.get("layouts")
        if isinstance(raw, dict):
            layouts = {role: cfg for role, cfg in raw.items() if isinstance(cfg, dict)}
    return layouts


def match_layout(prs, role: str, config: dict, report: list[dict]):
    """Resolve one role to a slide layout: name, keywords, index, then default."""
    names = [layout.name for layout in prs.slide_layouts]

    wanted_name = config.get("name")
    if isinstance(wanted_name, str) and wanted_name.strip():
        for layout in prs.slide_layouts:
            if layout.name.strip().lower() == wanted_name.strip().lower():
                report.append({"role": role, "layout": layout.name, "via": "name"})
                return layout

    keywords = config.get("keywords")
    if isinstance(keywords, list):
        for keyword in keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                continue
            needle = keyword.strip().lower()
            for layout in prs.slide_layouts:
                if needle in layout.name.lower():
                    report.append({"role": role, "layout": layout.name, "via": f"keyword:{keyword}"})
                    return layout

    index = config.get("index")
    if isinstance(index, int) and 0 <= index < len(prs.slide_layouts):
        layout = prs.slide_layouts[index]
        report.append({"role": role, "layout": layout.name, "via": "index"})
        return layout

    fallback = DEFAULT_LAYOUT_INDEX.get(role, 1)
    if fallback < len(prs.slide_layouts):
        layout = prs.slide_layouts[fallback]
        report.append({"role": role, "layout": layout.name, "via": "default"})
        return layout

    raise RenderError(f"no usable layout for role {role!r} (template has {len(names)} layouts)")


def pick_placeholder(container, config: dict, kind: str, placeholder_types, warnings: list[str]):
    """Resolve a placeholder by explicit idx, then by type, then give up.

    ``container`` is the *slide* (layout placeholders are only the blueprint;
    add_slide clones them onto the slide and only the slide copies are visible).
    """
    wanted_idx = None
    placeholders_cfg = config.get("placeholders")
    if isinstance(placeholders_cfg, dict):
        candidate = placeholders_cfg.get(kind)
        if isinstance(candidate, int):
            wanted_idx = candidate

    if wanted_idx is not None:
        for placeholder in container.placeholders:
            if placeholder.placeholder_format.idx == wanted_idx:
                return placeholder
        warnings.append(f"placeholder idx {wanted_idx} for {kind!r} not found on the slide")

    for placeholder in container.placeholders:
        if placeholder.placeholder_format.type in placeholder_types:
            return placeholder
    return None


# ------------------------------------------------------------------- rendering


def assign_roles(count: int) -> list[str]:
    roles = ["content"] * count
    if count:
        roles[0] = "title"
    return roles


def write_bullets(text_frame, bullets: list[str]) -> None:
    text_frame.text = bullets[0]
    for bullet in bullets[1:]:
        paragraph = text_frame.add_paragraph()
        paragraph.text = bullet


def set_notes(slide, notes: str, visual: str | None, warnings: list[str]) -> None:
    body = notes.strip()
    if visual and visual.strip():
        body = f"{body}\n\nVisual: {visual.strip()}"
    try:
        slide.notes_slide.notes_text_frame.text = body
    except (AttributeError, ValueError) as err:  # pragma: no cover - template dependent
        warnings.append(f"could not write speaker notes: {err}")


def render_deck(payload: dict, template: Path | None, mapping: dict | None, check_only: bool,
                out_path: Path | None, force: bool) -> dict:
    meta = payload["meta"]
    slides = payload["slides"]
    assignment = assign_roles(len(slides))

    if check_only and template is None:
        layout_config = resolve_layout_config(mapping)
        return {
            "mode": "check",
            "payload_slides": len(slides),
            "template": None,
            "template_layouts": [],
            "layout_resolution": [
                {
                    "role": role,
                    "layout": f"built-in default index {DEFAULT_LAYOUT_INDEX.get(role, 1)}",
                    "via": "default",
                    "configured": bool(layout_config.get(role)),
                }
                for role in ROLES
            ],
            "per_slide": [{"slide": index, "role": role} for index, role in enumerate(assignment, start=1)],
            "mapping_applied": bool(mapping),
            "note": "payload validated; python-pptx is only needed with --template",
        }

    Presentation, PP_PLACEHOLDER, Inches = import_pptx()

    try:
        prs = Presentation(str(template)) if template else Presentation()
    except Exception as err:  # pragma: no cover - template dependent
        raise RenderError(f"cannot open template {template}: {err}") from err

    title_types = (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
    subtitle_types = (PP_PLACEHOLDER.SUBTITLE,)
    body_types = (PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT)

    layout_config = resolve_layout_config(mapping)
    layout_report: list[dict] = []
    resolved = {role: match_layout(prs, role, layout_config.get(role, {}), layout_report)
                for role in ROLES}

    if check_only:
        per_slide = []
        for index, role in enumerate(assignment, start=1):
            layout = resolved[role]
            per_slide.append({"slide": index, "role": role, "layout": layout.name})
        return {
            "mode": "check",
            "payload_slides": len(slides),
            "template": str(template) if template else None,
            "template_layouts": [layout.name for layout in prs.slide_layouts],
            "layout_resolution": layout_report,
            "per_slide": per_slide,
            "mapping_applied": bool(mapping),
        }

    warnings: list[str] = []
    if template is not None or mapping is not None:
        # Only meaningful when the caller asked for a specific master.
        warnings = [
            f"layout fallback for role {entry['role']!r} (template layout names did not match)"
            for entry in layout_report
            if entry["via"] == "default"
        ]

    built: list[dict] = []
    for index, (role, slide_data) in enumerate(zip(assignment, slides), start=1):
        layout = resolved[role]
        slide = prs.slides.add_slide(layout)
        config = layout_config.get(role, {})

        title_ph = pick_placeholder(slide, config, "title", title_types, warnings)
        if title_ph is not None:
            if role == "title":
                title_ph.text_frame.text = str(meta.get("title", "")).strip()
            else:
                title_ph.text_frame.text = str(slide_data.get("title", "")).strip()
        else:
            warnings.append(f"slide {index}: no title placeholder in layout {layout.name!r}")

        if role == "title":
            subtitle = f"{meta.get('audience', '')} · {meta.get('purpose', '')} · ~{meta.get('est_minutes', '')} min"
            subtitle_ph = pick_placeholder(slide, config, "subtitle", subtitle_types, warnings)
            if subtitle_ph is not None:
                subtitle_ph.text_frame.text = subtitle.strip(" ·")
        else:
            body_ph = pick_placeholder(slide, config, "body", body_types, warnings)
            bullets = [str(item) for item in slide_data.get("bullets", [])]
            if body_ph is not None:
                write_bullets(body_ph.text_frame, bullets)
            else:
                box = slide.shapes.add_textbox(
                    Inches(0.8), Inches(1.8),
                    prs.slide_width - Inches(1.6), prs.slide_height - Inches(2.6),
                )
                write_bullets(box.text_frame, bullets)
                warnings.append(f"slide {index}: no body placeholder, added a text box")

        set_notes(slide, str(slide_data.get("speaker_notes", "")), slide_data.get("visual"), warnings)
        built.append({"slide": index, "role": role, "layout": layout.name,
                      "bullets": len(slide_data.get("bullets", []))})

    if out_path is None:
        raise RenderError("output path missing")
    if out_path.exists() and not force:
        raise RenderError(f"{out_path} already exists; pass --force to overwrite")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))

    return {
        "mode": "render",
        "output": str(out_path),
        "payload_slides": len(slides),
        "template": str(template) if template else None,
        "mapping_applied": bool(mapping),
        "layout_resolution": layout_report,
        "slides": built,
        "warnings": warnings,
    }


def default_out_path(payload_path: Path, meta: dict, version: str, slot: int | None) -> Path:
    slug = slugify(str(meta.get("title", payload_path.stem)))
    stamp = date.today().strftime("%Y%m%d")
    name = f"{slug}_{version}_{slot}min_{stamp}.pptx" if slot else f"{slug}_{version}_{stamp}.pptx"
    return payload_path.parent / name


# ------------------------------------------------------------------------ cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render an output-contract deck payload (.json) to a .pptx file.",
    )
    parser.add_argument("payload", help="deck payload JSON (see references/output-contract.md)")
    parser.add_argument("--template", help="corporate .pptx/.potx template supplying the masters")
    parser.add_argument("--master-map", help="layout + placeholder mapping JSON (references/master-mapping.md)")
    parser.add_argument("--out", help="output .pptx path (default: naming convention in export-checklist.md)")
    parser.add_argument("--version", default=DEFAULT_VERSION, help=f"version token for the file name (default: {DEFAULT_VERSION})")
    parser.add_argument("--slot", type=int, help="duration slot in minutes for scaled packs (3 / 8 / 15)")
    parser.add_argument("--check", action="store_true", help="validate payload and layout mapping, write nothing")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output file")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdout()
    args = build_parser().parse_args(argv)

    try:
        payload_path = Path(args.payload)
        payload = load_json(payload_path)
        errors = validate_payload(payload)
        if errors:
            raise RenderError("payload invalid:\n  - " + "\n  - ".join(errors))

        mapping = None
        if args.master_map:
            mapping = load_json(Path(args.master_map))
            if not isinstance(mapping, dict) or not isinstance(mapping.get("layouts"), dict):
                raise RenderError(f"master map {args.master_map} must contain a 'layouts' object")
        elif args.template is None and not args.check:
            mapping = None

        template = Path(args.template) if args.template else None
        if template is not None and not template.exists():
            raise RenderError(f"template not found: {template}")
        if args.master_map and template is None:
            print("note: --master-map without --template; the bundled master and its defaults are used",
                  file=sys.stderr)

        out_path = Path(args.out) if args.out else None
        if out_path is None and not args.check:
            out_path = default_out_path(payload_path, payload.get("meta", {}), args.version, args.slot)

        report = render_deck(payload, template, mapping, args.check, out_path, args.force)
    except RenderError as err:
        print(f"ERROR {err}", file=sys.stderr)
        return EXIT_FAIL

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        if report["mode"] == "check":
            print(f"check ok: {report['payload_slides']} slides, template={report['template'] or 'bundled'}")
            for entry in report["layout_resolution"]:
                print(f"  {entry['role']:<8} -> {entry['layout']}  ({entry['via']})")
        else:
            print(f"rendered {report['payload_slides']} slides -> {report['output']}")
            for entry in report["layout_resolution"]:
                print(f"  {entry['role']:<8} -> {entry['layout']}  ({entry['via']})")
            for warning in report["warnings"]:
                print(f"  warning: {warning}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
