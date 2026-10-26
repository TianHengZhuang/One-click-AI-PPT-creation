# Source brief

`tools/source_extract.py` turns whatever the user hands over — a PDF, a Word
file, a spreadsheet, a folder of notes — into one `source-brief.json`. The deck
is then drafted **from the brief**, not from a half-remembered skim of the
source. Every number that lands on a slide should be traceable to a record in
here.

Run it before Step 1 whenever the request comes with material attached.

```bash
python tools/source_extract.py report.pdf notes.md data.xlsx \
    --out source-brief.json
```

| Flag | Meaning |
| --- | --- |
| `--out PATH` | write the brief to `PATH` (default: stdout) |
| `--print` | print to stdout even when `--out` is not given |
| `--max-chars N` | per-document text cap, default 60000 |
| `--recursive` | walk directories |
| `--name NAME` | label recorded in `name`, default `source-brief` |
| `--quiet` | no output on success |

Exit status is `0` when at least one document was read, `2` when nothing could
be read. A single unreadable file never stops the run.

## What it reads

| Format | Parser | Notes |
| --- | --- | --- |
| `.md` `.markdown` `.txt` `.rst` `.log` | built in | Markdown headings become sections |
| `.html` `.htm` | built in | script / style dropped, `<title>` becomes the title |
| `.csv` `.tsv` | built in | first row is the header |
| `.json` | built in | pretty-printed, invalid JSON falls back to raw text |
| `.pdf` | `pypdf` or `PyPDF2` | one section per page, `pages` recorded |
| `.docx` | `python-docx` | Heading styles become sections, tables captured |
| `.pptx` | `python-pptx` | one section per slide, speaker notes appended |
| `.xlsx` | `openpyxl` | one section per sheet, first 200 rows per sheet |
| images | none | indexed as an asset only — describe or OCR them in chat |

A missing optional parser is not an error: the document is reported with
`ok: false` and an install hint (`pip install pypdf`, etc.), and the rest of the
brief is still produced. Do not install anything on the user's behalf without
asking.

## Shape of the brief

```json
{
  "schema": "source-brief/v1",
  "generated_at": "2026-10-25T09:00:00+00:00",
  "name": "source-brief",
  "inputs": [
    {
      "path": "report.pdf",
      "type": "pdf",
      "bytes": 482113,
      "ok": true,
      "pages": 12,
      "chars": 21400,
      "truncated": false,
      "title": "report",
      "warnings": [],
      "sections": [
        {"heading": "page 1", "level": 2, "chars": 1810, "text": "...", "locator": "p.1"}
      ],
      "chunks": [
        {"id": "report.pdf#1", "path": "report.pdf", "section": "page 1",
         "chars": 1180, "text": "..."}
      ],
      "tables": [
        {"name": "table 1", "locator": "table 1", "header": ["a", "b"],
         "rows": [["1", "2"]], "row_count": 1, "truncated": false}
      ],
      "numbers": [
        {"value": "18%", "kind": "percent",
         "context": "Revenue grew 18% year over year.",
         "source": {"path": "report.pdf", "locator": "p.3"}}
      ]
    }
  ],
  "evidence": [
    {"kind": "number", "value": "18%", "kind_detail": "percent",
     "context": "Revenue grew 18% year over year.",
     "source": {"path": "report.pdf", "locator": "p.3"}}
  ],
  "stats": {"documents": 1, "documents_ok": 1, "chunks": 18,
            "tables": 2, "numbers": 41, "chars": 21400},
  "warnings": [],
  "missing_inputs": []
}
```

Field rules worth knowing:

- `chunks[].id` is `<path>#<n>` and stable for a given input order — cite it in
  the draft's source notes so a claim can be walked back to a passage. Numbering
  runs across the whole document, so ids are unique even when a file has many
  sections: `report.pdf#1` appears once, and citing it always resolves to the
  same passage.
- `chunks[].section` repeats the heading so a retrieved chunk is never orphaned.
- `numbers[]` keeps the sentence around the figure, because `18%` means nothing
  without the noun next to it. Duplicates are collapsed on
  `(value, first 60 chars of context, path)`.
- `numbers[].kind` is one of `percent`, `currency`, `multiplier`, `count`.
  It is a hint for how to render the figure, not a correctness check.
- `evidence[]` flattens the numbers across documents, capped at 400 records —
  this is the list the evidence lint (v2.0 PR3) checks slide figures against.
- `warnings[]` is user-facing prose: truncated files, missing parsers, paths that
  did not exist. Surface them in the delivery note; never silently drop a
  document.

## How the brief is used

| Step | Use |
| --- | --- |
| Step 1 (intake) | list `inputs`; confirm with the user which ones are in scope |
| Step 2 (structure) | `sections[].heading` suggests an existing narrative spine |
| Step 3 (draft) | pull `chunks[]` per slide; never invent a figure absent from `evidence[]` |
| Step 5 (review) | `tools/deck_lint.py` / `deck_review.py` check slide numbers against `evidence[]` |
| delivery note | copy `warnings[]` and `stats` so coverage is stated, not implied |

## Limits

- Text only. Charts, diagrams and scanned pages come through as nothing or as
  noise; say so instead of guessing what a picture showed.
- `.xls`, `.ppt`, `.doc` (legacy binary), `.pages`, `.key` and password-protected
  files are not parsed — convert or ask.
- `--max-chars` truncates the head of a long document. When `truncated` is true,
  ask the user for the relevant chapter rather than pretending to have read it.
- The brief is an index, not a transcript: it will not contain every sentence of
  a 200-page PDF, and it should not be quoted as if it did.
