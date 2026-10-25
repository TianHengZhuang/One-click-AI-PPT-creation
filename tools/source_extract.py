#!/usr/bin/env python3
"""Extract a source brief from documents before a deck is drafted.

Reads PDF, DOCX, PPTX, XLSX, Markdown, HTML, CSV, TXT and produces one
``source-brief.json`` that the skill can quote from: sections, chunks,
table rows, and every number found together with the sentence around it.

Design rules
------------
* Standard library first. Every parser is optional: when a library is
  missing the file is reported with an actionable hint instead of taking
  the run down.
* Deterministic output. Inputs keep the order they were given; keys are
  sorted inside each record; nothing depends on wall-clock time except
  ``generated_at``.
* No network. Nothing is fetched, nothing is uploaded.
* The brief is an index, not a dump. Long documents are chunked so a model
  can pull the passages it needs instead of swallowing the whole file.

Usage
-----
    python tools/source_extract.py report.pdf notes.md --out brief.json
    python tools/source_extract.py deck.pptx --max-chars 30000 --print
    python tools/source_extract.py assets/ --recursive
"""

from __future__ import annotations

import argparse
import csv
import html as html_lib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "source-brief/v1"
DEFAULT_CHUNK_CHARS = 1200
CHUNK_OVERLAP = 120
DEFAULT_MAX_CHARS = 60000
MAX_TABLE_ROWS = 200

HTML_SUFFIXES = {".html", ".htm"}
CSV_SUFFIXES = {".csv", ".tsv"}
JSON_SUFFIXES = {".json"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

NUMBER_PATTERNS = (
    # A figure only counts when it stands on its own: the lookarounds reject
    # digits, dots and commas on either side, so "1.5" inside "v1.5.2" or the
    # tail of "12,480" is not picked up again. Whitespace and CJK are fine.
    ("percent", re.compile(r"(?<![\d.,])[-+]?\d+(?:\.\d+)?\s?%(?!\d)(?!\.\d)")),
    ("currency", re.compile(
        r"(?:[¥$€£]|RMB|USD|CNY|EUR)\s?\d[\d,]*(?:\.\d+)?"
        r"(?:\s?(?:[KMB]|万|亿|千|百万|十亿|千万))?")),
    ("multiplier", re.compile(
        r"(?<![\d.,])\d+(?:\.\d+)?\s?(?:x|X|倍)(?!\d)(?!\.\d)")),
    ("count", re.compile(
        r"(?<![\d.,])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{3,}(?:\.\d+)?)(?![\d,])(?!\.\d)")),
    # "2.4亿", "12万" - magnitude written without a currency symbol. Tagged as
    # magnitude rather than count because the scale word is the whole point.
    ("magnitude", re.compile(
        r"(?<![\d.,¥$€£])\d+(?:\.\d+)?\s?(?:亿|万|千|百万|十亿|千万|K|M|B)"
        r"(?![\d.A-Za-z_])")),
)

WARN_NO_LIB = {
    "pdf": "install pypdf to read PDFs: python -m pip install pypdf",
    "docx": "install python-docx to read DOCX: python -m pip install python-docx",
    "pptx": "install python-pptx to read PPTX: python -m pip install python-pptx",
    "xlsx": "install openpyxl to read XLSX: python -m pip install openpyxl",
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def norm_ws(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sentence_around(text: str, start: int, end: int, width: int = 160) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    window = text[left:right]
    for sep in ("。", "！", "？", ". ", "! ", "? ", "\n"):
        cut = window.rfind(sep, 0, len(window) // 2)
        if cut > 0:
            window = window[cut + len(sep):]
            break
    for sep in ("。", "！", "？", ". ", "! ", "? ", "\n"):
        cut = window.find(sep, len(window) // 2)
        if cut > 0:
            window = window[: cut + len(sep)]
            break
    return norm_ws(window)


def split_chunks(text: str, path: str, section: str,
                 size: int = DEFAULT_CHUNK_CHARS) -> list[dict]:
    chunks: list[dict] = []
    clean = norm_ws(text)
    if not clean:
        return chunks
    step = max(1, size - CHUNK_OVERLAP)
    index = 0
    for start in range(0, len(clean), step):
        piece = clean[start:start + size]
        if not piece.strip():
            continue
        index += 1
        chunks.append({
            "id": f"{path}#{index}",
            "path": path,
            "section": section,
            "chars": len(piece),
            "text": piece,
        })
        if start + size >= len(clean):
            break
    return chunks


def extract_sections_from_markdown(text: str) -> list[dict]:
    sections: list[dict] = []
    current = {"heading": "", "level": 0, "text": ""}
    for line in text.split("\n"):
        match = HEADING_RE.match(line.strip())
        if match:
            if current["text"].strip() or current["heading"]:
                sections.append(current)
            current = {"heading": match.group(2).strip(),
                       "level": len(match.group(1)),
                       "text": ""}
        else:
            current["text"] += line + "\n"
    if current["text"].strip() or current["heading"]:
        sections.append(current)
    for section in sections:
        section["text"] = norm_ws(section["text"])
    return [s for s in sections if s["text"] or s["heading"]]


def table_record(name: str, header: list[str], rows: list[list[str]],
                 locator: str) -> dict:
    return {
        "name": name,
        "locator": locator,
        "header": [str(c).strip() for c in header][:20],
        "rows": [[str(c).strip() for c in row][:20] for row in rows[:MAX_TABLE_ROWS]],
        "row_count": len(rows),
        "truncated": len(rows) > MAX_TABLE_ROWS,
    }


# --------------------------------------------------------------------------
# per-format readers -> {"text", "sections", "tables", "pages", "title"}
# --------------------------------------------------------------------------

def read_plain(path: Path, raw: str) -> dict:
    text = norm_ws(raw)
    if path.suffix.lower() in {".md", ".markdown"}:
        sections = extract_sections_from_markdown(text)
    else:
        sections = [{"heading": "", "level": 0, "text": text}]
    return {"text": text, "sections": sections, "tables": [],
            "pages": None, "title": path.stem}


def read_html(path: Path, raw: str) -> dict:
    body = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
    title = norm_ws(html_lib.unescape(title_match.group(1))) if title_match else path.stem
    sections: list[dict] = []
    for match in re.finditer(r"(?is)<h([1-6])[^>]*>(.*?)</h\1>", body):
        sections.append({"heading": norm_ws(html_lib.unescape(
            re.sub(r"(?s)<[^>]+>", " ", match.group(2)))),
            "level": int(match.group(1)), "text": ""})
    body = re.sub(r"(?is)<(h[1-6]|p|div|br|li|tr|section|article)[^>]*>", "\n", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    text = norm_ws(html_lib.unescape(body).replace("\xa0", " "))
    if not sections:
        sections = [{"heading": title, "level": 1, "text": text}]
    else:
        blocks = [b.strip() for b in re.split(r"\n{2,}", text) if b.strip()]
        for index, block in enumerate(blocks):
            if index < len(sections):
                sections[index]["text"] = block
        if not any(s["text"] for s in sections):
            sections[0]["text"] = text
    return {"text": text, "sections": sections, "tables": [],
            "pages": None, "title": title}


def read_csv(path: Path, raw: str) -> dict:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    rows = list(csv.reader(io.StringIO(raw), delimiter=delimiter))
    rows = [r for r in rows if any(str(c).strip() for c in r)]
    if not rows:
        return {"text": "", "sections": [], "tables": [], "pages": None,
                "title": path.stem}
    header, body = rows[0], rows[1:]
    table = table_record(path.stem, header, body, "table 1")
    lines = [" | ".join(str(c) for c in header)]
    lines += [" | ".join(str(c) for c in row) for row in body[:MAX_TABLE_ROWS]]
    text = norm_ws("\n".join(lines))
    return {"text": text, "sections": [{"heading": path.stem, "level": 1, "text": text}],
            "tables": [table], "pages": None, "title": path.stem}


def read_json(path: Path, raw: str) -> dict:
    try:
        data = json.loads(raw)
        text = json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as error:
        return {"text": norm_ws(raw),
                "sections": [{"heading": path.stem, "level": 1, "text": norm_ws(raw)}],
                "tables": [], "pages": None, "title": path.stem,
                "warning": f"invalid JSON, treated as text: {error.msg}"}
    return {"text": norm_ws(text),
            "sections": [{"heading": path.stem, "level": 1, "text": norm_ws(text)}],
            "tables": [], "pages": None, "title": path.stem}


def read_pdf(path: Path) -> dict:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return {"error": WARN_NO_LIB["pdf"], "lib": "pypdf"}
    reader = PdfReader(str(path))
    pages = []
    sections = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as error:  # pragma: no cover - parser specific
            page_text = ""
            sections.append({"heading": f"page {number}", "level": 2,
                             "text": "", "locator": f"p.{number}"})
            pages.append(f"[page {number}: extraction failed: {error}]")
            continue
        page_text = norm_ws(page_text)
        pages.append(page_text)
        if page_text:
            sections.append({"heading": f"page {number}", "level": 2,
                             "text": page_text, "locator": f"p.{number}"})
    return {"text": norm_ws("\n\n".join(pages)), "sections": sections,
            "tables": [], "pages": len(reader.pages), "title": path.stem}


def read_docx(path: Path) -> dict:
    try:
        import docx  # type: ignore
    except ImportError:
        return {"error": WARN_NO_LIB["docx"], "lib": "python-docx"}
    document = docx.Document(str(path))
    sections: list[dict] = []
    current = {"heading": "", "level": 0, "text": ""}
    for paragraph in document.paragraphs:
        text = norm_ws(paragraph.text)
        if not text:
            continue
        style = (paragraph.style.name or "").lower() if paragraph.style else ""
        level = 0
        if style.startswith("heading"):
            digits = re.findall(r"\d+", style)
            level = int(digits[0]) if digits else 1
        elif style == "title":
            level = 1
        if level:
            if current["text"].strip() or current["heading"]:
                sections.append(current)
            current = {"heading": text, "level": level, "text": ""}
        else:
            current["text"] += text + "\n"
    if current["text"].strip() or current["heading"]:
        sections.append(current)
    tables = []
    for index, table in enumerate(document.tables, start=1):
        rows = [[cell.text for cell in row.cells] for row in table.rows]
        if not rows:
            continue
        tables.append(table_record(f"table {index}", rows[0], rows[1:],
                                   f"table {index}"))
    body = "\n\n".join(s["text"] for s in sections if s["text"])
    for table in tables:
        body += "\n\n" + "\n".join(" | ".join(r) for r in [table["header"]] + table["rows"][:20])
    return {"text": norm_ws(body),
            "sections": [s for s in sections if s["text"] or s["heading"]],
            "tables": tables, "pages": None,
            "title": sections[0]["heading"] if sections and sections[0]["heading"] else path.stem}


def read_pptx(path: Path) -> dict:
    try:
        from pptx import Presentation  # type: ignore
    except ImportError:
        return {"error": WARN_NO_LIB["pptx"], "lib": "python-pptx"}
    presentation = Presentation(str(path))
    sections: list[dict] = []
    for number, slide in enumerate(presentation.slides, start=1):
        blocks: list[str] = []
        title = ""
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            text = norm_ws(shape.text_frame.text)
            if not text:
                continue
            if getattr(shape, "is_placeholder", False):
                try:
                    if shape.placeholder_format.type is not None and shape.placeholder_format.idx == 0:
                        title = text
                except (AttributeError, ValueError):
                    pass
            blocks.append(text)
        notes = ""
        try:
            if slide.has_notes_slide:
                notes = norm_ws(slide.notes_slide.notes_text_frame.text)
        except (AttributeError, ValueError):
            notes = ""
        heading = title or f"slide {number}"
        body = "\n".join(b for b in blocks if b != title)
        if notes:
            body = (body + "\n\n[notes] " + notes).strip()
        sections.append({"heading": heading, "level": 2, "text": body,
                         "locator": f"slide {number}"})
    text = "\n\n".join(f"## {s['heading']}\n{s['text']}" for s in sections)
    return {"text": norm_ws(text), "sections": sections, "tables": [],
            "pages": len(presentation.slides), "title": path.stem}


def read_xlsx(path: Path) -> dict:
    try:
        import openpyxl  # type: ignore
    except ImportError:
        return {"error": WARN_NO_LIB["xlsx"], "lib": "openpyxl"}
    workbook = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
    sections: list[dict] = []
    tables: list[dict] = []
    try:
        for sheet in workbook.worksheets:
            rows: list[list[str]] = []
            for row in sheet.iter_rows(values_only=True):
                values = ["" if cell is None else str(cell) for cell in row]
                if any(v.strip() for v in values):
                    rows.append(values)
                if len(rows) >= MAX_TABLE_ROWS + 1:
                    break
            if not rows:
                continue
            header, body = rows[0], rows[1:]
            tables.append(table_record(sheet.title, header, body, f"sheet {sheet.title}"))
            lines = [" | ".join(header)]
            lines += [" | ".join(r) for r in body[:40]]
            text = norm_ws("\n".join(lines))
            sections.append({"heading": sheet.title, "level": 2, "text": text,
                             "locator": f"sheet {sheet.title}"})
    finally:
        workbook.close()
    body = "\n\n".join(s["text"] for s in sections)
    return {"text": body, "sections": sections, "tables": tables,
            "pages": None, "title": path.stem}


def read_image(path: Path) -> dict:
    return {"text": "", "sections": [], "tables": [], "pages": None,
            "title": path.stem,
            "asset_only": True,
            "warning": ("image is indexed as an asset only; describe it in chat "
                        "or run OCR before drafting")}


READERS = {
    ".pdf": read_pdf,
    ".docx": read_docx,
    ".pptx": read_pptx,
    ".xlsx": read_xlsx,
}


# --------------------------------------------------------------------------
# numbers
# --------------------------------------------------------------------------

def collect_numbers(text: str, path: str, locator: str | None) -> list[dict]:
    found: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for kind, pattern in NUMBER_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            context = sentence_around(text, match.start(), match.end())
            key = (value.replace(" ", ""), context[:60])
            if key in seen:
                continue
            seen.add(key)
            record = {"value": value, "kind": kind, "context": context,
                      "source": {"path": path}}
            if locator:
                record["source"]["locator"] = locator
            found.append(record)
    return found


# --------------------------------------------------------------------------
# brief assembly
# --------------------------------------------------------------------------

def read_source(path: Path, max_chars: int) -> dict:
    entry = {
        "path": str(path).replace(os.sep, "/"),
        "type": path.suffix.lower().lstrip(".") or "unknown",
        "bytes": path.stat().st_size if path.exists() else 0,
        "ok": True,
        "warnings": [],
        "sections": [],
        "chunks": [],
        "tables": [],
        "numbers": [],
        "pages": None,
        "title": path.stem,
    }
    if not path.exists():
        entry["ok"] = False
        entry["error"] = "file not found"
        return entry
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        result = read_image(path)
    elif suffix in READERS:
        try:
            result = READERS[suffix](path)
        except Exception as error:  # keep the run alive, report the file
            entry["ok"] = False
            entry["error"] = f"{type(error).__name__}: {error}"
            entry["warnings"].append("parser failed; document skipped")
            return entry
    else:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if suffix in HTML_SUFFIXES:
            result = read_html(path, raw)
        elif suffix in CSV_SUFFIXES:
            result = read_csv(path, raw)
        elif suffix in JSON_SUFFIXES:
            result = read_json(path, raw)
        else:
            result = read_plain(path, raw)

    if result.get("error"):
        entry["ok"] = False
        entry["error"] = result["error"]
        entry["warnings"].append(
            f"optional dependency missing for {entry['type']}: {result.get('lib', '')}")
        return entry
    if result.get("warning"):
        entry["warnings"].append(result["warning"])

    text = result.get("text", "")
    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True
        entry["warnings"].append(
            f"text truncated to {max_chars} chars; chunks still index the head of the file")
    if not text.strip() and not result.get("asset_only"):
        entry["warnings"].append(
            "no extractable text; the file may be scanned, image-only or empty")

    sections = result.get("sections") or []
    if truncated:
        sections = _truncate_sections(sections, max_chars)

    entry["title"] = result.get("title") or path.stem
    entry["pages"] = result.get("pages")
    entry["chars"] = len(text)
    entry["truncated"] = truncated
    entry["sections"] = [
        {"heading": s.get("heading", ""), "level": s.get("level", 0),
         "chars": len(s.get("text", "")), "text": s.get("text", ""),
         **({"locator": s["locator"]} if s.get("locator") else {})}
        for s in sections
    ]
    for section in sections:
        entry["chunks"].extend(split_chunks(
            section.get("text", ""), entry["path"],
            section.get("heading", "") or "(untitled)"))
    entry["tables"] = result.get("tables", [])
    # Numbers are collected per section so a figure keeps its page or sheet
    # locator; a document without sections falls back to the whole body.
    if entry["sections"]:
        for section in entry["sections"]:
            entry["numbers"].extend(collect_numbers(
                section["text"], entry["path"], section.get("locator")))
    else:
        entry["numbers"] = collect_numbers(text, entry["path"], None)
    return entry


def _truncate_sections(sections: list[dict], budget: int) -> list[dict]:
    kept: list[dict] = []
    used = 0
    for section in sections:
        text = section.get("text", "")
        if used >= budget:
            break
        if used + len(text) > budget:
            section = dict(section)
            section["text"] = text[: budget - used]
        used += len(section.get("text", ""))
        kept.append(section)
    return kept


def collect_files(inputs: list[str], recursive: bool) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing: list[str] = []
    for item in inputs:
        path = Path(item).expanduser()
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            for child in sorted(path.glob(pattern)):
                if child.is_file() and not child.name.startswith("."):
                    files.append(child)
        elif path.exists():
            files.append(path)
        else:
            missing.append(item)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in files:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique, missing


def build_brief(paths: list[Path], max_chars: int, name: str | None = None,
                missing: list[str] | None = None) -> dict:
    documents = [read_source(path, max_chars) for path in paths]
    numbers: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    chunks = 0
    tables = 0
    for document in documents:
        chunks += len(document.get("chunks", []))
        tables += len(document.get("tables", []))
        for record in document.get("numbers", []):
            key = (record["value"].replace(" ", ""), record["context"][:60],
                   record["source"]["path"])
            if key in seen:
                continue
            seen.add(key)
            numbers.append(record)
    ok_documents = [d for d in documents if d.get("ok")]
    brief = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "name": name or "source-brief",
        "inputs": documents,
        "evidence": [
            {
                "kind": "number",
                "value": record["value"],
                "kind_detail": record["kind"],
                "context": record["context"],
                "source": record["source"],
            }
            for record in numbers[:400]
        ],
        "stats": {
            "documents": len(documents),
            "documents_ok": len(ok_documents),
            "chunks": chunks,
            "tables": tables,
            "numbers": len(numbers),
            "chars": sum(d.get("chars", 0) for d in ok_documents),
        },
        "warnings": [],
        "missing_inputs": missing or [],
    }
    if missing:
        brief["warnings"].append(
            f"{len(missing)} input path(s) not found: {', '.join(missing)}")
    failed = [d for d in documents if not d.get("ok")]
    if failed:
        brief["warnings"].append(
            f"{len(failed)} document(s) could not be read: "
            + ", ".join(f"{d['path']} ({d.get('error', 'unknown')})" for d in failed))
    if not ok_documents:
        brief["warnings"].append("no readable document; the brief is empty")
    return brief


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source_extract.py",
        description="Extract a source brief (sections, chunks, tables, numbers) "
                    "from documents before drafting a deck.")
    parser.add_argument("inputs", nargs="+", help="files or directories to read")
    parser.add_argument("--out", help="write the brief to this JSON path")
    parser.add_argument("--print", dest="print_only", action="store_true",
                        help="print the brief to stdout instead of writing a file")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                        help=f"per-document text cap (default {DEFAULT_MAX_CHARS})")
    parser.add_argument("--recursive", action="store_true",
                        help="walk directories recursively")
    parser.add_argument("--name", help="brief name, defaults to source-brief")
    parser.add_argument("--quiet", action="store_true", help="print nothing on success")
    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdout()
    args = build_parser().parse_args(argv)
    paths, missing = collect_files(args.inputs, args.recursive)
    if not paths and not missing:
        print("error: no input files", file=sys.stderr)
        return 2
    brief = build_brief(paths, args.max_chars, args.name, missing)
    payload = json.dumps(brief, ensure_ascii=False, indent=2)

    if args.print_only or not args.out:
        if not args.quiet:
            print(payload)
        return 0 if brief["stats"]["documents_ok"] else 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload + "\n", encoding="utf-8")
    if not args.quiet:
        stats = brief["stats"]
        print(f"wrote {out_path} — {stats['documents_ok']}/{stats['documents']} documents, "
              f"{stats['chunks']} chunks, {stats['tables']} tables, {stats['numbers']} numbers")
        for warning in brief["warnings"]:
            print(f"warning: {warning}", file=sys.stderr)
    return 0 if brief["stats"]["documents_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
