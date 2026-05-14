# Copilot Instructions for HA-print

## Build, test, and lint

### Add-on (FastAPI + python-escpos)

```bash
cd print
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx
pytest app/tests/ -v
```

Tests use `escpos.printer.Dummy` to capture output bytes — no real printer needed.

No linter or formatter is configured.

### HACS integration

No standalone test suite. The integration is exercised live in Home Assistant.

## Architecture

- **Add-on** (`print/`): Docker container with FastAPI (port 8100) + nginx (port 8099, ingress).
  Stateless — callers POST the data to print; HA-print just renders + prints.
- **HACS integration** (`custom_components/ha_print/`): Two service handlers
  (`ha_print.shopping_list`, `ha_print.recipe`) that fetch data from HA-storage /
  HA-recipes via httpx, then POST to the add-on. Auto-discovers sibling URLs
  through Supervisor API.

## Key conventions

- Version bumps + CHANGELOG on every change (`## X.Y.Z` headers only)
- `config.json`: `hassio_api: true`, `ingress: true`, sibling-accessible port `8100/tcp`
- nginx is minimal: serves a tiny status page on `/` and proxies `/api/` to FastAPI on 127.0.0.1:8100
- s6-overlay `longrun` services (`print-api`, `print`) with `with-contenv bashio` shebang
- All Finnish text and product names are codepage-CP858 (forced at connection time)
- Printer driver lives in `app/escpos_driver.py` as a `thermal_printer()` context
  manager. Rendering modules (`app/templating/*.py`) operate on **any escpos
  printer-like object** — Network in production, Dummy in tests.

## Aisle ordering

`custom_components/ha_print/aisles.py` mirrors `FI_AISLE_ORDER` from
`HA-stock/stock/frontend/src/App.jsx:112-155`. **KEEP IN SYNC** if the JS list
changes. The add-on itself never groups items — only the integration's
`ha_print.shopping_list` service handler does (frontends pre-group before POSTing).

## Recipe shape

The recipe POST body matches **HA-recipes**'s `_get_recipe_detail` schema
(`backend.py:1942-1950`): `name`, `servings`, `source_url`, `picture_filename`,
`ingredients[{product_name, amount_needed, unit_abbrev, parent_name, note}]`,
`instructions[str]`. HA-print's Pydantic model accepts BOTH this shape and a
generic `{name, amount, unit, note}` shape — easier for HA-stock to send.

## Codepage gotchas

- Xprinter clones ship a reduced codepage table. **Force CP858** (or CP1252) at
  connection time; do not rely on `charcode('AUTO')`.
- Do NOT use box-drawing chars (U+2500–U+257F) in templates — ASCII `-` instead.
- Partial cut + 6-line feed clears the tear bar reliably; full cut is unreliable
  on the XP-80T even when `GS V 0` is sent.
