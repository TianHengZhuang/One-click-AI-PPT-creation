#!/usr/bin/env python3
"""deck_review - audit an existing deck against this skill's rules.

A deck that already exists gets reviewed, not rewritten. deck_review reads a
Markdown deck (or an output-contract JSON payload) and runs the mechanical
passes from references/deck-review.md:

    * hard gates  - the deck cannot be handed over as it stands
    * warnings    - worth a human look, but they do not block the hand-off
    * a score     - 0-100 across structure / copy / evidence / delivery
    * a verdict   - READY, REVISE or REWRITE

The rules come from references/copywriting-guide.md (claims, short active
bullets), references/design-guide.md (one message per slide, one visual per
slide), references/export-checklist.md (gates before a hand-off) and the
timing model in references/output-contract.md.

Chinese decks get the same review in their own units: 240 characters per minute
for timing, character counts for bullet and notes lengths, and the Chinese
label and joiner lists instead of the English ones.

Usage:
    python tools/deck_review.py examples/status-report.md
    python tools/deck_review.py examples/status-report.json --json
    python tools/deck_review.py deck.md --slot 5 --min-score 85 --out review.md

Exit status is 1 when a hard gate fails or the score is below --min-score
(with --strict, warnings fail the run too). Standard library only - no
dependencies. Finding labels stay ASCII; quoted slide text keeps its script.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1

SCHEMA_VERSION = "1.0"

# ------------------------------------------------------------ scoring model

WEIGHTS = {"structure": 0.30, "copy": 0.30, "evidence": 0.20, "delivery": 0.20}
DEDUCTIONS = {"error": 25, "warning": 6}

VERDICT_READY = "READY"
VERDICT_REVISE = "REVISE"
VERDICT_REWRITE = "REWRITE"
READY_SCORE = 85
REVISE_SCORE = 70

# --------------------------------------------------------------- thresholds

BULLET_MAX = 5                  # references/design-guide.md: 3-5 bullets per slide
BULLET_WORD_LIMIT = 12          # copywriting-guide.md: under ~12 words per bullet
BULLET_PARAGRAPH_WORDS = 20     # a sentence, not a fragment - move it to the notes
BULLET_CHAR_LIMIT = 24          # the same bullet rule for zh-CN, measured in characters
BULLET_PARAGRAPH_CHARS = 40     # the zh-CN paragraph threshold
NOTES_MIN_SECONDS = 4.0         # a note the presenter cannot say aloud is not a note
NOTES_MAX_SECONDS = 40.0        # one slide's worth of speaking
AVG_CHARS_PER_WORD = 5.5        # turns the English word rate into a character rate
SPEAKING_RATE = {"en": 130.0, "zh": 240.0}   # words/min (en) or chars/min (zh-CN)
SLIDE_OVERHEAD_SECONDS = 8      # speaking rate + one on-screen beat
SLOT_DRIFT_WARN = 0.15          # output-contract.md: >15% drift from the slot
MIN_METRIC_SLIDES = 0.5         # half the body slides should carry a number
ZH_LABEL_MAX_CHARS = 6          # "决策" / "概览" / "下一步" - shorter than this is a label

LABEL_HEADLINES = {
    "overview", "summary", "agenda", "introduction", "intro", "background",
    "metrics", "metrics dashboard", "results", "next steps", "questions",
    "q&a", "thank you", "thanks", "conclusion", "wins", "issues", "risks",
    "timeline", "roadmap", "status", "key takeaways", "call to action",
}

ZH_LABELS = {
    "概览", "总览", "摘要", "总结", "议程", "背景", "指标", "数据看板", "结果",
    "下一步", "问题", "问答", "致谢", "谢谢", "结论", "要点", "关键要点", "状态",
    "时间线", "路线图", "风险", "行动项", "待办", "回顾", "现状", "进展", "计划",
}

CLICHES = (
    "leverage", "leveraging", "synergy", "synergies", "best-in-class",
    "world-class", "cutting-edge", "state-of-the-art", "seamless", "seamlessly",
    "robust", "innovative", "innovation", "game-chang", "next-generation",
    "holistic", "utilize", "utiliz", "facilitate", "impactful", "revolutionary",
    "empower", "paradigm", "turnkey", "mission-critical", "value-add",
)

PASSIVE_RE = re.compile(r"\b(?:was|were|been)\s+\w+(?:ed|en)\b", re.I)
ZH_PASSIVE_RE = re.compile(r"被(?!动)")
ZH_TWO_IDEA_RE = re.compile(r"并且|而且|以及|同时|；|;")
ZH_FILLER_RE = re.compile(r"(?:[\u4e00-\u9fff]{4}[、，])+[\u4e00-\u9fff]{4}")
ZH_CLOSING_RE = re.compile(r"问题|决策|下一步|行动|谢谢|结论|提议|确认|提问|选择|拍板|签字")
GENERIC_VISUAL = {
    "", "none", "no visual", "n/a", "image", "photo", "picture", "graphic",
    "visual", "stock photo", "clipart", "illustration",
}
CLOSING_RE = re.compile(
    r"question|next step|ask|thank|decision|appendix|close|recap|summary|call to action",
    re.I,
)
SOURCE_MARKERS = ("source", "internal", "as of", "footer", "footnote", "data:")

SLIDE_HEADING_RE = re.compile(r"^##\s+Slide\s+(\d+)\s*[\u2014\u2013-]\s*(.+?)\s*$", re.M)
BULLET_RE = re.compile(r"^([ \t]*)[-*]\s+(.*)$", re.M)
VISUAL_RE = re.compile(r"^Visual:\s*(.+?)\s*$", re.M | re.I)
NOTES_RE = re.compile(r"^Notes:\s*(.+?)\s*$", re.M | re.I)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
DIGIT_RE = re.compile(r"\d")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z0-9$%\u00a3\u20ac.,/+-]+")

FIX_HINTS = {
    "no-slides": "Point deck_review at a Markdown deck or an output-contract JSON payload.",
    "headline-missing": "Give the slide a claim-style headline (references/copywriting-guide.md).",
    "headline-duplicate": "Two slides carry the same message - merge them or retitle one.",
    "headline-label": "Rewrite the headline as a claim the audience could argue with.",
    "bullets-empty": "Add 3-5 bullets, or fold the slide into its neighbour.",
    "bullets-too-many": "Keep five bullets, move the rest into the speaker notes.",
    "bullet-long": "Cut the bullet to twelve words or fewer.",
    "bullet-paragraph": "Move the sentence into the notes; leave a fragment on the slide.",
    "bullet-nested": "Flatten nested bullets - one level only.",
    "bullet-two-ideas": "Split the bullet; an 'and' usually hides a second idea.",
    "passive-voice": "Rewrite the sentence in active voice.",
    "cliche": "Replace the stock phrase with a number or a concrete noun.",
    "no-metric": "Add the number that makes the slide worth showing.",
    "notes-missing": "Write the two or three sentences the presenter will say.",
    "notes-short": "Add the supporting number or the bridge to the next slide.",
    "notes-long": "Trim the notes to the slide slot.",
    "slot-drift": "Cut slides or trim notes to fit the slot.",
    "visual-missing": "Add one visual suggestion, or state 'Visual: none' on purpose.",
    "visual-generic": "Name the chart or the evidence, not the medium.",
    "metric-source": "Add a source or an 'internal' label before hand-off.",
    "no-closing": "End with the ask, the decisions needed, or a question slide.",
}


class Finding:
    __slots__ = ("level", "code", "slide", "message", "dimension")

    def __init__(self, level: str, code: str, slide: int | None, message: str, dimension: str) -> None:
        self.level = level          # "error" | "warning"
        self.code = code
        self.slide = slide          # 1-based slide number, None for deck-level
        self.message = message
        self.dimension = dimension  # structure | copy | evidence | delivery

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "slide": self.slide,
            "dimension": self.dimension,
            "message": self.message,
            "fix": FIX_HINTS.get(self.code, ""),
        }


class Slide:
    __slots__ = ("number", "headline", "bullets", "visual", "notes", "nested")

    def __init__(self, number, headline, bullets=None, visual=None, notes=None,
                 nested=False) -> None:
        self.number = number
        self.headline = headline
        self.bullets = bullets or []
        self.visual = visual
        self.notes = notes
        self.nested = nested


class Deck:
    __slots__ = ("base", "source", "title", "language", "purpose", "target_minutes",
                 "est_minutes", "slides")

    def __init__(self, base: str, source: str) -> None:
        self.base = base
        self.source = source        # "markdown" | "json"
        self.title = base
        self.language = None
        self.purpose = None
        self.target_minutes = None
        self.est_minutes = None
        self.slides: list[Slide] = []


class Review:
    def __init__(self, deck: Deck) -> None:
        self.deck = deck
        self.findings: list[Finding] = []
        self.scores: dict[str, int] = {}
        self.score = 0
        self.verdict = VERDICT_REWRITE
        self.estimated_minutes = 0.0
        self.notes_minutes = 0.0
        self.slot_minutes = None

    def error(self, code, slide, message, dimension) -> None:
        self.findings.append(Finding("error", code, slide, message, dimension))

    def warn(self, code, slide, message, dimension) -> None:
        self.findings.append(Finding("warning", code, slide, message, dimension))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors


# ------------------------------------------------------------------ parsing


def word_count(text: str, language: str) -> int:
    if language == "zh":
        return len(CJK_RE.findall(text))
    return len(WORD_RE.findall(text))


def slide_seconds(headline: str, notes: str, language: str) -> int:
    body = f"{headline} {notes or ''}".strip()
    rate = SPEAKING_RATE["zh" if language == "zh" else "en"] / 60.0
    spoken = math.ceil(word_count(body, language) / rate) if body else 0
    return spoken + SLIDE_OVERHEAD_SECONDS


def detect_language(text: str) -> str:
    cjk = len(CJK_RE.findall(text))
    return "zh" if cjk and cjk * 4 > len(text) else "en"


def parse_markdown(text: str, base: str) -> Deck:
    deck = Deck(base, "markdown")
    title = TITLE_RE.search(text)
    if title:
        deck.title = title.group(1).strip()
    deck.language = detect_language(text)

    headings = list(SLIDE_HEADING_RE.finditer(text))
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[match.end():end]

        bullets: list[str] = []
        nested = False
        for bullet in BULLET_RE.finditer(body):
            if len(bullet.group(1)) >= 2:
                nested = True
            bullets.append(bullet.group(2).strip())

        visual = VISUAL_RE.search(body)
        notes = NOTES_RE.search(body)
        deck.slides.append(
            Slide(
                number=int(match.group(1)),
                headline=match.group(2).strip(),
                bullets=bullets,
                visual=visual.group(1).strip() if visual else None,
                notes=notes.group(1).strip().strip('"').strip() if notes else None,
                nested=nested,
            )
        )
    return deck


def parse_json(text: str, base: str) -> Deck:
    deck = Deck(base, "json")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f'schema_version must be "{SCHEMA_VERSION}"')

    meta = payload.get("meta") or {}
    deck.title = str(meta.get("title") or base)
    language = str(meta.get("language") or "")
    deck.language = "zh" if language.lower().startswith("zh") else "en"
    deck.purpose = meta.get("purpose")
    try:
        deck.target_minutes = float(meta["target_minutes"])
    except (KeyError, TypeError, ValueError):
        deck.target_minutes = None
    try:
        deck.est_minutes = float(meta["est_minutes"])
    except (KeyError, TypeError, ValueError):
        deck.est_minutes = None

    for raw in payload.get("slides") or []:
        if not isinstance(raw, dict):
            continue
        bullets = [str(b) for b in raw.get("bullets") or []]
        deck.slides.append(
            Slide(
                number=int(raw.get("id") or len(deck.slides) + 1),
                headline=str(raw.get("title") or "").strip(),
                bullets=bullets,
                visual=str(raw.get("visual") or "").strip() or None,
                notes=str(raw.get("speaker_notes") or "").strip() or None,
            )
        )
    return deck


def read_deck(path: Path) -> Deck:
    base = path.stem if path.suffix else path.name
    if path.suffix.lower() == ".json":
        return parse_json(path.read_text(encoding="utf-8"), base)
    target = path
    if not target.is_file() and path.with_suffix(".md").is_file():
        target = path.with_suffix(".md")
    return parse_markdown(target.read_text(encoding="utf-8"), base)


# ------------------------------------------------------------------- checks


def check_headline(review: Review, slide: Slide, seen: dict[str, int]) -> None:
    headline = slide.headline.strip()
    if not headline:
        review.error("headline-missing", slide.number, "slide has no headline", "structure")
        return
    key = headline.lower()
    if key in seen:
        review.error(
            "headline-duplicate",
            slide.number,
            f'headline repeats slide {seen[key]}: "{headline}"',
            "structure",
        )
    else:
        seen[key] = slide.number

    words = headline.split()
    stripped = key.strip(" .:。，,、")
    if CJK_RE.search(headline):
        # Chinese headlines have no spaces, so length is counted in characters.
        is_label = stripped in ZH_LABELS or (
            len(stripped) <= ZH_LABEL_MAX_CHARS and not DIGIT_RE.search(headline)
        )
    else:
        is_label = stripped in LABEL_HEADLINES or (len(words) < 4 and not DIGIT_RE.search(headline))
    if is_label:
        review.warn(
            "headline-label",
            slide.number,
            f'headline reads as a label, not a claim: "{headline}"',
            "structure",
        )
    if headline.endswith(":"):
        review.warn(
            "headline-label",
            slide.number,
            f'headline ends with a colon, so the point arrives later: "{headline}"',
            "structure",
        )


def check_bullets(review: Review, slide: Slide, is_closing: bool) -> None:
    bullets = [b for b in slide.bullets if b.strip()]
    if not bullets and not is_closing:
        review.error("bullets-empty", slide.number, "slide carries no bullets", "structure")
        return
    if len(bullets) > BULLET_MAX:
        review.warn(
            "bullets-too-many",
            slide.number,
            f"{len(bullets)} bullets on one slide (cap is {BULLET_MAX})",
            "structure",
        )
    if slide.nested:
        review.warn("bullet-nested", slide.number, "nested bullets on the slide", "copy")

    for bullet in bullets:
        if CJK_RE.search(bullet):
            # Chinese bullets are counted in characters, not in space-separated words.
            chars = len(re.sub(r"\s", "", bullet))
            if chars > BULLET_CHAR_LIMIT:
                review.warn(
                    "bullet-long" if chars <= BULLET_PARAGRAPH_CHARS else "bullet-paragraph",
                    slide.number,
                    f'{chars}-character bullet: "{trim(bullet)}"',
                    "copy",
                )
            joiner = ZH_TWO_IDEA_RE.search(bullet)
            if joiner:
                review.warn(
                    "bullet-two-ideas",
                    slide.number,
                    f'bullet joins two ideas with "{joiner.group(0)}": "{trim(bullet)}"',
                    "copy",
                )
            filler = ZH_FILLER_RE.search(bullet)
            if filler:
                review.warn(
                    "cliche",
                    slide.number,
                    f'four-character stacking "{filler.group(0)}" - check it carries information',
                    "copy",
                )
            if ZH_PASSIVE_RE.search(bullet):
                review.warn(
                    "passive-voice",
                    slide.number,
                    f'passive voice: "{trim(bullet)}"',
                    "copy",
                )
            continue
        words = len(bullet.split())
        if words > BULLET_WORD_LIMIT:
            review.warn(
                "bullet-long" if words <= BULLET_PARAGRAPH_WORDS else "bullet-paragraph",
                slide.number,
                f"{words}-word bullet: \"{trim(bullet)}\"",
                "copy",
            )
        if re.search(r"\sand\s", bullet, re.I):
            review.warn(
                "bullet-two-ideas",
                slide.number,
                f"bullet joins two ideas with 'and': \"{trim(bullet)}\"",
                "copy",
            )
        if PASSIVE_RE.search(bullet):
            review.warn(
                "passive-voice",
                slide.number,
                f"passive voice: \"{trim(bullet)}\"",
                "copy",
            )
        lowered = bullet.lower()
        for cliche in CLICHES:
            if cliche in lowered:
                review.warn(
                    "cliche",
                    slide.number,
                    f'stock phrase "{cliche}" in: "{trim(bullet)}"',
                    "copy",
                )
                break


def check_visual(review: Review, slide: Slide) -> None:
    visual = (slide.visual or "").strip()
    if not visual:
        review.warn("visual-missing", slide.number, "no visual suggestion on the slide", "evidence")
        return
    if visual.lower().strip(".") in GENERIC_VISUAL and visual.lower().strip(".") != "none":
        review.warn(
            "visual-generic",
            slide.number,
            f'visual "{visual}" names the medium, not the evidence',
            "evidence",
        )


def notes_char_bounds(language: str) -> tuple[int, int]:
    """Notes length floor and ceiling, in characters, for the deck's language.

    English is counted in words per minute, Chinese in characters per minute
    (references/output-contract.md), so the same speaking budget becomes a
    different character count in each language.
    """
    rate = SPEAKING_RATE.get(language, SPEAKING_RATE["en"])
    chars_per_second = rate / 60.0 if language == "zh" else rate / 60.0 * AVG_CHARS_PER_WORD
    return int(NOTES_MIN_SECONDS * chars_per_second), int(NOTES_MAX_SECONDS * chars_per_second)


def check_notes(review: Review, slide: Slide, language: str) -> int:
    notes = (slide.notes or "").strip()
    if not notes:
        review.error("notes-missing", slide.number, "slide has no speaker notes", "delivery")
        return 0
    min_chars, max_chars = notes_char_bounds(language)
    length = len(notes)
    if length < min_chars:
        review.warn(
            "notes-short",
            slide.number,
            f"notes are {length} characters - too short to speak",
            "delivery",
        )
    if length > max_chars:
        review.warn(
            "notes-long",
            slide.number,
            f"notes are {length} characters - over the slide budget",
            "delivery",
        )

    seconds = slide_seconds(slide.headline, notes, language)
    return seconds


def check_timing(review: Review, deck: Deck, notes_seconds: dict[int, int]) -> None:
    """Compare the deck's own estimate against the slot it has to fill.

    The declared `meta.est_minutes` is authoritative when the deck ships as an
    output-contract payload; a Markdown-only deck has nothing but the notes, so
    the notes estimate stands in for it. Per-slide `est_seconds` is deck_lint's
    job (it checks the notes pack line by line).
    """
    review.notes_minutes = round(sum(notes_seconds.values()) / 60.0, 1)
    review.estimated_minutes = deck.est_minutes if deck.est_minutes is not None else review.notes_minutes

    slot = deck.target_minutes or review.slot_minutes
    if not slot:
        return
    if abs(review.estimated_minutes - slot) / slot > SLOT_DRIFT_WARN:
        review.warn(
            "slot-drift",
            None,
            f"deck estimates {review.estimated_minutes} min against a {slot:g} min slot "
            f"(notes alone carry {review.notes_minutes} min)",
            "delivery",
        )


def check_deck_level(review: Review, deck: Deck) -> None:
    slides = deck.slides
    body = slides[1:-1] if len(slides) > 2 else slides

    with_numbers = [s for s in body if DIGIT_RE.search(" ".join([s.headline] + s.bullets))]
    if body and len(with_numbers) < math.ceil(len(body) * MIN_METRIC_SLIDES):
        review.warn(
            "no-metric",
            None,
            f"only {len(with_numbers)} of {len(body)} body slides carry a number",
            "copy",
        )

    source_text = " ".join((s.notes or "") + " " + (s.visual or "") for s in slides).lower()
    if with_numbers and not any(marker in source_text for marker in SOURCE_MARKERS):
        review.warn(
            "metric-source",
            None,
            "metric claims carry no source or 'internal' label anywhere in the deck",
            "evidence",
        )

    last = slides[-1] if slides else None
    if last:
        closing_text = f"{last.headline} {' '.join(last.bullets)}"
        closing_re = ZH_CLOSING_RE if CJK_RE.search(closing_text) else CLOSING_RE
        if not closing_re.search(closing_text):
            review.warn(
                "no-closing",
                last.number,
                f'last slide "{last.headline}" is not an ask, a decision or a question slide',
                "structure",
            )


def trim(text: str, limit: int = 60) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


# ------------------------------------------------------------------ verdict


def score_review(review: Review) -> None:
    deductions = {name: 0 for name in WEIGHTS}
    for finding in review.findings:
        deductions[finding.dimension] += DEDUCTIONS[finding.level]
    review.scores = {name: max(0, 100 - deductions[name]) for name in WEIGHTS}
    review.score = round(sum(review.scores[name] * weight for name, weight in WEIGHTS.items()))

    if review.errors:
        review.verdict = VERDICT_REVISE if review.score >= REVISE_SCORE else VERDICT_REWRITE
    elif review.score >= READY_SCORE:
        review.verdict = VERDICT_READY
    elif review.score >= REVISE_SCORE:
        review.verdict = VERDICT_REVISE
    else:
        review.verdict = VERDICT_REWRITE


def review_deck(path: Path, slot_minutes: float | None = None) -> Review:
    deck = read_deck(path)
    review = Review(deck)
    review.slot_minutes = slot_minutes

    if not deck.slides:
        review.error("no-slides", None, "no slides found in the deck", "structure")
        score_review(review)
        return review

    seen: dict[str, int] = {}
    notes_seconds: dict[int, int] = {}
    last_number = deck.slides[-1].number

    for slide in deck.slides:
        is_closing = slide.number == last_number
        check_headline(review, slide, seen)
        check_bullets(review, slide, is_closing)
        check_visual(review, slide)
        notes_seconds[slide.number] = check_notes(review, slide, deck.language)

    check_timing(review, deck, notes_seconds)
    check_deck_level(review, deck)
    score_review(review)
    return review


# ------------------------------------------------------------------ reports


def render_text(review: Review, quiet: bool) -> str:
    deck = review.deck
    lines = [f"deck_review  {deck.base}  ({deck.source}, {len(deck.slides)} slides)"]
    lines.append(
        f"  verdict: {review.verdict}   score: {review.score}/100   "
        f"est: {review.estimated_minutes} min (notes {review.notes_minutes} min)   hard gates: "
        f"{'PASS' if review.passed else str(len(review.errors)) + ' FAILED'}"
    )
    lines.append(
        "  dimensions: "
        + "  ".join(f"{name} {review.scores[name]}" for name in WEIGHTS)
    )

    if not review.findings and not quiet:
        lines.append("  no findings - the deck holds up against the rules")
        return "\n".join(lines)

    for label, items in (("ERROR", review.errors), ("WARNING", review.warnings)):
        if quiet and label == "WARNING":
            continue
        if not items:
            continue
        lines.append(f"  {label}S ({len(items)})")
        for finding in items:
            where = f"slide {finding.slide}" if finding.slide else "deck"
            lines.append(f"    [{finding.code}] {where}: {finding.message}")
    return "\n".join(lines)


def render_markdown(review: Review) -> str:
    deck = review.deck
    slot = f"{deck.target_minutes:g} min" if deck.target_minutes else (
        f"{review.slot_minutes:g} min" if review.slot_minutes else "not given"
    )
    lines = [
        f"# Deck review - {deck.title}",
        "",
        f"- Source: `{deck.source}` deck, {len(deck.slides)} slides",
        f"- Estimated talk time: {review.estimated_minutes} min (notes alone carry {review.notes_minutes} min)",
        f"- Slot: {slot}",
        f"- Verdict: **{review.verdict}** - score {review.score}/100",
        f"- Hard gates: {'pass' if review.passed else f'{len(review.errors)} failed'}",
        "",
        "## Dimension scores",
        "",
        "| Dimension | Score |",
        "|-----------|-------|",
    ]
    for name, weight in WEIGHTS.items():
        lines.append(f"| {name} ({int(weight * 100)}%) | {review.scores[name]} |")

    if review.errors:
        lines += ["", "## Blocking issues", "", "| Slide | Finding | Fix |", "|-------|---------|-----|"]
        for finding in review.errors:
            where = f"{finding.slide}" if finding.slide else "deck"
            lines.append(f"| {where} | {finding.message} | {FIX_HINTS.get(finding.code, '')} |")

    if review.warnings:
        lines += ["", "## Warnings", "", "| Slide | Finding | Fix |", "|-------|---------|-----|"]
        for finding in review.warnings:
            where = f"{finding.slide}" if finding.slide else "deck"
            lines.append(f"| {where} | {finding.message} | {FIX_HINTS.get(finding.code, '')} |")

    strong = [name for name in WEIGHTS if review.scores[name] >= READY_SCORE]
    if strong:
        lines += ["", "## Holding up", "", *[f"- {name}: {review.scores[name]}/100" for name in strong]]

    next_step = {
        VERDICT_READY: "Hand over as is; fix the warnings only if there is time.",
        VERDICT_REVISE: "Fix the blocking issues and the warnings, then re-run the review.",
        VERDICT_REWRITE: "Rebuild the deck from the structure stage; the copy pass alone will not save it.",
    }[review.verdict]
    lines += [
        "",
        "## Next step",
        "",
        next_step,
        "",
        "Fixes follow `references/copywriting-guide.md` and `references/design-guide.md`. Keep the author's content; change what the rules require.",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deck_review",
        description="Audit an existing deck against the copies of the skill's rules.",
    )
    parser.add_argument("deck", help="deck path, e.g. examples/status-report.md")
    parser.add_argument("--slot", type=float, default=None,
                        help="talk slot in minutes, e.g. 5 (defaults to meta.target_minutes)")
    parser.add_argument("--min-score", type=int, default=None,
                        help="fail when the score is below this value")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable report")
    parser.add_argument("--out", default=None, help="write the Markdown review report to this path")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--quiet", action="store_true", help="hide warnings in the text report")
    return parser


def ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ensure_utf8_stdout()

    path = Path(args.deck)
    if not path.is_file() and path.with_suffix(".md").is_file():
        path = path.with_suffix(".md")
    if not path.is_file():
        print(f"deck_review: {args.deck} not found")
        return EXIT_FAIL

    try:
        review = review_deck(path, args.slot)
    except (ValueError, OSError) as exc:
        print(f"deck_review: {exc}")
        return EXIT_FAIL

    if args.out:
        Path(args.out).write_text(render_markdown(review), encoding="utf-8")

    if args.as_json:
        print(
            json.dumps(
                {
                    "deck": review.deck.base,
                    "source": review.deck.source,
                    "slides": len(review.deck.slides),
                    "verdict": review.verdict,
                    "score": review.score,
                    "scores": review.scores,
                    "estimated_minutes": review.estimated_minutes,
                    "hard_gates_passed": review.passed,
                    "findings": [f.as_dict() for f in review.findings],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(render_text(review, args.quiet))

    if review.errors:
        return EXIT_FAIL
    if args.strict and review.warnings:
        return EXIT_FAIL
    if args.min_score is not None and review.score < args.min_score:
        return EXIT_FAIL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
