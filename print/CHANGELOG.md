## 0.1.8
- **Printer sidebar icon.** The Home Assistant sidebar entry now shows a printer icon (`mdi:printer`) instead of the default puzzle piece.

## 0.1.7
- **Much less blank paper before the cut.** The driver was feeding ~35mm before every cut: it called both a manual 6-line feed *and* python-escpos's `cut()`, which feeds 6 more lines by default. Now it uses the printer's "feed to cutter and partial-cut" command (`GS V B`), which advances the paper only as far as the cutter needs. New `cut_feed_lines` option (0–20, default 0) adds extra trailing margin if you want it.
- **Accurate cut line in the designer.** The print and the on-canvas cut line are now trimmed to the last actually-printed pixel instead of to the blocks' bounding boxes, so an oversized box around a QR/barcode or a tall/empty block no longer leaves a gap before the cut.

## 0.1.6
- **Delete key removes the selected block.** Click a block in the designer and press Delete (or Backspace) to remove it. Ignored while typing in a text field.

## 0.1.5
- **Receipt designer (new ingress web UI).** The add-on now ships a real web UI (not just the health page). A free 2D drag-and-drop canvas at 80mm proportions (576px printable width) lets you place styled text/headings, uploaded PNG/JPG images, dividers/blank feed, and QR codes & barcodes, then print the composed layout. The browser rasterizes the canvas to a bitmap, so what you see is what prints.
- **Alignment snapping.** Dragging a block snaps it to the canvas center lines and to nearby blocks' edges/centers, with on-canvas guidelines. The canvas redraws live while dragging. Hold Ctrl (or ⌘) to bypass snapping for free placement.
- **Save & reuse designs.** Layouts can be saved as named templates (stored in the add-on's `/data`) and re-loaded/re-printed later.
- **Direct SVG printing.** A separate tab accepts an uploaded `.svg`, rasterizes it server-side via librsvg to 576px-wide, and prints it. Design to 576px wide (72mm @ 203dpi), any height, pure black on white, convert text to paths.
- **New print endpoints:** `POST /api/print/image` (base64 PNG) and `POST /api/print/svg` (base64 SVG), plus templates CRUD under `/api/templates`.
- **Crisp QR/barcodes.** Line-art (designer composites, SVG) prints with a hard threshold by default instead of Floyd-Steinberg dithering, which keeps QR finder patterns and barcode bars scannable. Photographic content can still opt into dithering. The recipe hero image is unchanged (still dithered).
- New options: `full_width_px` (default `576`) and `svg_default_dither` (default `false`).

## 0.1.4
- **Beep after print** — new options to make the printer chirp when a receipt finishes:
  - `beep_after_print` (default `false`)
  - `beep_count` (1–9, default `2`)
  - `beep_duration_ms` (default `200`)
- **Print density** — `print_density` (0–8, default `5`, matching the XP-80T factory setting). Sent via `GS | n` at connect time. Bump up for more contrast on faded paper, down to save thermal head life.
- **Custom header / footer text** — `header_text` and `footer_text` options. Printed centered in `note_style` above the title and below the cut respectively. Empty by default. Useful for a household name or a "tervetuloa kauppaan" tagline.

## 0.1.3
- Driven by the XP-80T selftest, which revealed the printer can do **48 chars/line at Font A** (we'd been assuming 32) and that it ships with **Chinese character mode enabled** (which is why å/ä/ö rendered as CJK glyphs):
  - Default `column_width` raised to **48** (matches Font A at the printer's actual 576-dot width).
  - Driver now sends **`FS .`** (cancel Kanji mode) at connect time so the selected codepage (CP858 by default) is actually honored. Should fix the garbled Finnish/Swedish chars.

## 0.1.2
- **Granular font sizes per section.** Four new add-on options let you tune each region independently:
  - `title_style` (default `a1x2-bold` — Font A, double height, bold): the "Ostoslista" / recipe name banner.
  - `header_style` (default `a-bold-underline` — Font A, bold, underlined): aisle labels and "Ainekset"/"Ohjeet".
  - `item_style` (default `b` — Font B, smaller): list items, ingredients, instructions.
  - `note_style` (default `b`): per-item notes and the recipe source URL.
- Style spec syntax: `<font>[<WxH>|<scale>]-<modifier>...`. Examples: `a`, `b`, `a2` (Font A 2x both dims), `a1x2` (tall not wide), `a2x1` (wide not tall), `b-bold`, `a-bold-underline`, `a3-bold` (3x scale via `custom_size`).
- `printer_profile` and `column_width` explainer in README.

## 0.1.1
- Fix layout on XP-80T (and any printer running the python-escpos `default` profile at 384 dot width):
  - Default `column_width` lowered to **32** (matches Font A at default profile).
  - Compact item prefix: `[ ] 1 Banaani` instead of `[ ] 1       Banaani` — no more chasm between amount and name.
  - Long names word-wrap in Python with indented continuation lines instead of getting truncated and mid-word-wrapped by the printer.
  - Dropped the `…` ellipsis (not in CP858; was printing as `?` on the receipt).
- **Recipes**:
  - Body text now uses **Font B** (smaller, ~33% denser) — a recipe fits on far less paper.
  - Title drops `double_width` (keeps `double_height` + bold) — no wasted horizontal space.
  - Skip ingredient notes that duplicate the product name. HA-recipes commonly stores the original ingredient text in `note` AND in `product_name`, which made every ingredient print twice.
  - Same compact prefix + word-wrap treatment as shopping list.

## 0.1.0
- Initial release. Stateless HTTP service that renders + prints to an IP-connected 80mm ESC/POS thermal printer (Xprinter XP-80T compatible).
- Endpoints: `GET /api/health`, `POST /api/print/shopping-list`, `POST /api/print/recipe`.
- Forces `CP858` codepage for correct å/ä/ö rendering; partial cut with 6-line feed.
- Sibling-accessible on port `8100` for HA-stock / HA-recipes / HA service-call integrations.
