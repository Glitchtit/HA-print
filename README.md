<p align="center">
  <img src="https://raw.githubusercontent.com/Glitchtit/HA-print/main/print/logo.png" alt="Print" height="72">
</p>

<p align="center">
  <b>Prints shopping lists, recipes and your own designs on receipts</b><br>
  Part of Glitchtit's HA apps — the printer for Stock and Recipes, reading lists from the Storage add-on.
</p>

<p align="center">
  <a href="https://github.com/Glitchtit/HA-apps"><img alt="Home Assistant add-on" src="https://img.shields.io/badge/Home%20Assistant-add--on-0047AB?style=flat-square&logo=homeassistant&logoColor=white"></a>
  <img alt="Version" src="https://img.shields.io/badge/dynamic/json?style=flat-square&color=FF4F00&label=version&url=https%3A%2F%2Fraw.githubusercontent.com%2FGlitchtit%2FHA-print%2Fmain%2Fprint%2Fconfig.json&query=%24.version">
  <a href="https://hacs.xyz"><img alt="HACS custom" src="https://img.shields.io/badge/HACS-custom-1F2937?style=flat-square"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Glitchtit/HA-print/main/docs/screenshots/hero.png" alt="Print screenshot" width="100%">
</p>

## ✨ Features

- **Shopping list receipts** — prints the list grouped by Finnish grocery aisle, with quantities the way Storage shows them ("3,5 dl Kerma"). Done items can be struck through, skipped or printed as normal.
- **Recipe receipts** — the recipe name, servings, a dithered hero image, ingredients and numbered steps, ending with a QR code to the recipe's source page. To-taste ingredients print as "Suola (maun mukaan)".
- **🖨 buttons in Stock and Recipes** — the shopping-list overlay in HA-stock and the recipe view in HA-recipes find the Print add-on on their own and send jobs to it on port `8100`.
- **Print designer** — a drag-and-drop canvas at 80 mm paper width (576 px) with headings, text, images, dividers, blank feed, QR codes, barcodes and a drill guide. Blocks snap to the center and to each other (hold Ctrl or ⌘ to place freely), the canvas grows to fit, and what you see is what prints.
- **Saved templates** — store designs by name in the add-on and load or reprint them later.
- **SVG upload** — print an `.svg` directly; it is rasterized server-side to the paper width. Draw it 576 px wide, black on white, with text converted to paths.
- **Tuned for the XP-80T** — forces CP858 so å/ä/ö print correctly, turns off the printer's Kanji mode, and feeds only as far as the cutter needs before a partial cut. Any IP-connected 80 mm ESC/POS printer on port 9100 should work.

## 🚀 Installation

### Add-on

1. In Home Assistant open **Settings → Add-ons → Add-on Store → ⋮ → Repositories** and add `https://github.com/Glitchtit/HA-apps`
2. Install **Storage** first (the shopping-list action reads from it), then **Print**
3. In the **Configuration** tab set `printer_host` to the printer's IP address
4. Start it and open **Print** from the sidebar

### Integration (HACS)

1. In HACS open **⋮ → Custom repositories**, add `https://github.com/Glitchtit/HA-print` with category **Integration**
2. Download **Print** and restart Home Assistant
3. **Settings → Devices & services → Add integration → Print** (the add-on URL is found through the Supervisor and filled in; Storage and Recipes are found the same way)

## ⚙️ Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `printer_host` | _(empty)_ | Printer IP or hostname. Required. |
| `printer_port` | `9100` | Printer TCP port. |
| `printer_profile` | `default` | python-escpos printer profile. |
| `codepage` | `CP858` | Codepage forced at connect time. Try `CP1252` if accented letters still print wrong. |
| `image_impl` | `bitImageRaster` | How images are sent. Switch to `bitImageColumn` if images print garbled. |
| `enable_cut` | `true` | Partial cut after each receipt. |
| `cut_feed_lines` | `0` | Extra blank lines before the cut (0–20). |
| `column_width` | `48` | Characters per line (16–80). The XP-80T fits 48 in Font A. |
| `title_style` | `a1x2-bold` | Style of the title ("Shopping list" or the recipe name). |
| `header_style` | `a-bold-underline` | Style of aisle and section headers ("Ainekset", "Ohjeet"). |
| `item_style` | `b` | Style of list items, ingredients and steps. |
| `note_style` | `b` | Style of item notes, the source URL and header/footer text. |
| `header_text` / `footer_text` | _(empty)_ | Optional text printed above the title / below the body. |
| `print_density` | `5` | Darkness from 0 (lightest) to 8 (darkest). |
| `beep_after_print` | `false` | Beep when a receipt finishes. |
| `beep_count` / `beep_duration_ms` | `2` / `200` | Number of beeps (1–9) and length of each (50–1000 ms). |
| `full_width_px` | `576` | Printable width in dots for designer and SVG prints. |
| `svg_default_dither` | `false` | Dither SVG prints instead of a hard threshold (keeps QR codes and barcodes sharp when off). |
| `print_scale_v` | `1.0` | Vertical scale for designer and SVG prints (0.5–1.5). Set to intended ÷ measured length to calibrate. |
| `debug` | `false` | Verbose logging. |

Styles are written `<font>[<scale>]-<modifier>…`: font `a` or `b` (Font B is smaller), an optional scale like `2` or `1x2` (width × height), and `bold` / `underline`. Examples: `a`, `b-bold`, `a1x2-bold`, `a2`.

## 🏠 In Home Assistant

The integration adds two actions. Each fetches its data, then sends it to the Print add-on.

| Action | What it does |
|--------|--------------|
| `ha_print.shopping_list` | Fetches the shopping list from Storage, groups it by aisle and prints it. `done_filter`: `strike` (default), `skip` or `include`. |
| `ha_print.recipe` | Fetches the recipe with `recipe_id` from Recipes and prints it, with its image from Storage if it has one. |

## 🧩 The family

<p align="center">
  <a href="https://github.com/Glitchtit/HA-storage"><img src="https://raw.githubusercontent.com/Glitchtit/HA-storage/main/storage/icon.png" width="56" alt="Storage"></a>&nbsp;
  <a href="https://github.com/Glitchtit/HA-scraper"><img src="https://raw.githubusercontent.com/Glitchtit/HA-scraper/main/addon/icon.png" width="56" alt="Scraper"></a>&nbsp;
  <a href="https://github.com/Glitchtit/HA-stock"><img src="https://raw.githubusercontent.com/Glitchtit/HA-stock/main/stock/icon.png" width="56" alt="Stock"></a>&nbsp;
  <a href="https://github.com/Glitchtit/HA-recipes"><img src="https://raw.githubusercontent.com/Glitchtit/HA-recipes/main/recipes/icon.png" width="56" alt="Recipes"></a>&nbsp;
  <a href="https://github.com/Glitchtit/HA-chores"><img src="https://raw.githubusercontent.com/Glitchtit/HA-chores/main/chores/icon.png" width="56" alt="Chores"></a>&nbsp;
  <a href="https://github.com/Glitchtit/HA-lists"><img src="https://raw.githubusercontent.com/Glitchtit/HA-lists/main/lists/icon.png" width="56" alt="Lists"></a>&nbsp;
  <a href="https://github.com/Glitchtit/HA-print"><img src="https://raw.githubusercontent.com/Glitchtit/HA-print/main/print/icon.png" width="56" alt="Print"></a>
</p>

<p align="center"><sub>Print stores nothing about your food: Stock and Recipes send it lists and recipes to print, and its actions read them from Storage and Recipes.</sub></p>

## 🛠️ Development

```bash
# Add-on API (tests use python-escpos's Dummy printer; no hardware needed)
cd print
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx
python -m pytest app/tests/ -v

# Designer frontend (proxies /api to localhost:8100)
cd print/frontend && npm install && npm run dev
```
