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
