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
