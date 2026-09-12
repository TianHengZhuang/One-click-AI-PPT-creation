# Single-file HTML deck convention

Use this when the user wants a presentable deck without PowerPoint.

One self-contained `.html` file. No CDN. No network. Opens offline in any modern browser.

---

## Structure

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Deck title</title>
  <style>/* tokens + layout */</style>
</head>
<body>
  <main class="deck">
    <section class="slide" data-notes="...">...</section>
  </main>
  <script>/* keyboard nav only */</script>
</body>
</html>
```

---

## Slide rules

- One `<section class="slide">` per slide
- `h1` or `h2` is the message headline
- Body is short lists, not paragraphs
- Optional `.visual` block for a simple SVG chart or KPI tiles
- `data-notes` holds speaker notes for the N key / notes panel

---

## Layout tokens

```css
:root {
  --bg: #f7f7f5;
  --ink: #1a1a1a;
  --muted: #5c5c5c;
  --accent: #1f6feb;
  --slide-max: 1100px;
  --pad: 48px;
}
.slide {
  min-height: 100vh;
  max-width: var(--slide-max);
  margin: 0 auto;
  padding: var(--pad);
  box-sizing: border-box;
}
```

Print: `@media print` forces one slide per page (`page-break-after: always`).

---

## Keyboard

- `→` / `Space` — next
- `←` — previous
- `n` — toggle notes
- `Home` / `End` — first / last

Keep the script under ~40 lines. No framework.

---

## Charts in HTML

Prefer inline SVG bar/line charts with labeled axes.

Do not embed remote images.

Do not use canvas unless the chart is interactive and necessary.

---

## Accessibility

- Semantic headings in order
- `lang` on `<html>`
- Body text contrast ≥ 4.5:1
- Do not rely on color alone for meaning

---

## When not to use HTML

- Corporate template mandates PowerPoint
- Reviewers need tracked comments in pptx
- Heavy animation / Morph transitions

In those cases emit Markdown or JSON and let a pptx tool render.
