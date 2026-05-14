# HA-print

Thermal receipt printing for Home Assistant. Stateless HTTP service that renders
shopping lists and recipes onto an IP-connected 80mm ESC/POS thermal printer
(tested against **Xprinter XP-80T**).

Ships as a twin-pack: an HA add-on (`print/`) and a HACS integration
(`custom_components/ha_print/`).

## What it does

- `POST /api/print/shopping-list` — render an aisle-grouped shopping list and print it.
- `POST /api/print/recipe` — render a recipe (with hero image, ingredients, numbered instructions) and print it.
- `GET /api/health` — probe printer reachability.

Two HA services are also exposed via the integration:

- `ha_print.shopping_list` — fetches the current list from **HA-storage**, groups by Finnish grocery aisle, prints.
- `ha_print.recipe` — `{recipe_id}` — fetches the recipe from **HA-recipes**, prints with image.

## Integration with the umbrella

- **HA-stock** — adds a 🖨 button in the shopping-list overlay header.
- **HA-recipes** — adds a 🖨 button in the recipe-detail action row.

Both apps auto-discover the HA-print add-on at startup and proxy `/api/print/`
to it through nginx.

## Configuration

Add-on options:

| Option            | Default              | Description |
|-------------------|----------------------|-------------|
| `printer_host`    | _(empty)_            | Printer IP or hostname. Required. |
| `printer_port`    | `9100`               | TCP port (ESC/POS default). |
| `printer_profile` | `default`            | python-escpos profile. Controls assumed paper width for image sizing/centering. The XP-80T's actual width is 576 dots — the `default` profile assumes 384, which is fine for our text-mostly templates but may downscale images. |
| `codepage`        | `CP858`              | Forced codepage. CP858 is at slot 19 on XP-80T. Use `CP1252` (slot 16) if Western chars still misrender. |
| `image_impl`      | `bitImageRaster`     | Pillow → ESC/POS bridge. Switch to `bitImageColumn` if images print mangled. |
| `enable_cut`      | `true`               | Partial-cut after each receipt. |
| `column_width`    | `48`                 | Characters per line in Font A. The XP-80T's selftest reports 48 chars at Font A and 64 at Font B at the 72mm printing width. |
| `title_style`     | `a1x2-bold`          | Style of the "Ostoslista" / recipe-name banner. |
| `header_style`    | `a-bold-underline`   | Style of aisle / section headers ("Ainekset", "Ohjeet"). |
| `item_style`      | `b`                  | Style of list items, ingredients, instruction steps. Font B is ~33% denser than A. |
| `note_style`      | `b`                  | Style of per-item notes and the recipe source URL. |

### Style spec format

`<font>[<scale>]-<modifier>...` where:

- **font** is `a` (Font A, ~12 dots wide) or `b` (Font B, ~9 dots wide).
- **scale** is optional and can be either a single digit (1–4, applied to both dimensions) or `<W>x<H>` for independent width × height (e.g. `1x2` = double-height, not wide).
- **modifiers** are dash-separated: `bold`, `underline`. Order doesn't matter.

Examples:

| Spec                  | Meaning |
|-----------------------|---------|
| `a`                   | Font A, normal |
| `b`                   | Font B, smaller |
| `a2`                  | Font A, 2× width AND 2× height |
| `a1x2`                | Font A, 1× width, 2× height (the classic tall receipt banner) |
| `a2x1`                | Font A, 2× width, 1× height |
| `a-bold`              | Font A, normal, bold |
| `b-bold-underline`    | Font B, normal, bold + underlined |
| `a3-bold`             | Font A, 3× scale, bold (uses `custom_size` — only on firmwares that support it) |

## Local testing

```bash
cd print
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx
pytest app/tests/ -v
```

The tests use python-escpos's `Dummy` printer; no hardware needed.
