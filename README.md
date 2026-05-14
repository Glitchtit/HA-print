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

| Option            | Default          | Description |
|-------------------|------------------|-------------|
| `printer_host`    | _(empty)_        | Printer IP or hostname. Required. |
| `printer_port`    | `9100`           | TCP port (ESC/POS default). |
| `printer_profile` | `default`        | python-escpos profile. `default` works for XP-80T. |
| `codepage`        | `CP858`          | Forced codepage. Use `CP1252` if å/ä/ö are garbled. |
| `image_impl`      | `bitImageRaster` | Pillow → ESC/POS bridge. Switch to `bitImageColumn` if images print mangled. |
| `enable_cut`      | `true`           | Partial-cut after each receipt. |
| `column_width`    | `48`             | Characters per line (Font A at 80mm). |

## Local testing

```bash
cd print
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx
pytest app/tests/ -v
```

The tests use python-escpos's `Dummy` printer; no hardware needed.
