"""Render a recipe onto an escpos printer-like object.

Includes optional hero image rendering via Pillow (downscale → 1-bit dither).
Text styles for title / header / item / note come from the caller — defaults
target a dense layout where the body text is in Font B (small) and the title
is bold double-height.
"""
from __future__ import annotations

import io
import logging
import textwrap
from typing import Any

from PIL import Image

from .common import divider, fmt_amount, safe_text
from .style import TextStyle

logger = logging.getLogger(__name__)


def render(
    printer,
    *,
    recipe: dict[str, Any],
    image_bytes: bytes | None = None,
    column_width: int = 32,
    image_impl: str = "bitImageRaster",
    image_width_px: int = 384,
    title_style: TextStyle | None = None,
    header_style: TextStyle | None = None,
    item_style: TextStyle | None = None,
    note_style: TextStyle | None = None,
) -> dict[str, int]:
    """Render a recipe. Returns a small summary dict."""
    name = safe_text(recipe.get("name") or "Recipe")
    servings = recipe.get("servings")
    ingredients = recipe.get("ingredients") or []
    instructions = recipe.get("instructions") or []

    title_style = title_style or TextStyle.parse("a1x2-bold")
    header_style = header_style or TextStyle.parse("a-bold-underline")
    item_style = item_style or TextStyle.parse("b")
    note_style = note_style or TextStyle.parse("b")

    # ── Hero image (optional) ──────────────────────────────────────────────
    if image_bytes:
        try:
            img = _prepare_image(image_bytes, target_width=image_width_px)
            printer.set(align="center")
            printer.image(img, impl=image_impl, center=False)
            printer.set(align="left")
            printer.text("\n")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to render hero image: %s", exc)

    # ── Title block ────────────────────────────────────────────────────────
    printer.set(align="center")
    title_style.apply(printer)
    printer.text(name + "\n")
    TextStyle().apply(printer)  # reset
    printer.set(align="center")
    if servings is not None:
        printer.text(f"Annokset: {fmt_amount(servings)}\n")
    printer.set(align="left")

    # The body is laid out in `item_style` (Font B by default). Compute the
    # effective body wrap width once.
    body_width = item_style.width_chars(column_width)

    item_style.apply(printer)
    printer.text(divider(body_width) + "\n")
    TextStyle().apply(printer)

    # ── Ingredients ────────────────────────────────────────────────────────
    header_style.apply(printer)
    printer.text("Ainekset\n")
    TextStyle().apply(printer)

    for ing in ingredients:
        _render_ingredient(
            printer, ing,
            column_width=column_width,
            item_style=item_style, note_style=note_style,
        )

    item_style.apply(printer)
    printer.text(divider(body_width) + "\n")
    TextStyle().apply(printer)

    # ── Instructions ───────────────────────────────────────────────────────
    header_style.apply(printer)
    printer.text("Ohjeet\n")
    TextStyle().apply(printer)

    item_style.apply(printer)
    for i, step in enumerate(instructions, start=1):
        body = safe_text(step)
        if not body:
            continue
        prefix = f"{i}. "
        wrapped = textwrap.wrap(body, width=body_width - len(prefix)) or [""]
        first, *rest = wrapped
        printer.text(prefix + first + "\n")
        indent = " " * len(prefix)
        for cont in rest:
            printer.text(indent + cont + "\n")
        printer.text("\n")

    # Source line (kept in note style — typically smallest)
    src = safe_text(recipe.get("source_url") or "")
    if src:
        note_style.apply(printer)
        note_width = note_style.width_chars(column_width)
        for line in textwrap.wrap(src, width=note_width) or [""]:
            printer.text(line + "\n")

    TextStyle().apply(printer)  # reset for cut/feed
    return {
        "ingredients_printed": len(ingredients),
        "steps_printed": len(instructions),
        "image_printed": 1 if image_bytes else 0,
    }


def _render_ingredient(
    printer,
    ing: dict[str, Any],
    *,
    column_width: int,
    item_style: TextStyle,
    note_style: TextStyle,
) -> None:
    amount = ing.get("amount") if "amount" in ing else ing.get("amount_needed")
    unit = ing.get("unit") if "unit" in ing else ing.get("unit_abbrev")
    name = safe_text(ing.get("name") or ing.get("product_name") or "")
    parent = safe_text(ing.get("parent_name") or "")
    note = safe_text(ing.get("note") or "")

    qty = ""
    a = fmt_amount(amount)
    u = (unit or "").strip()
    if a and u:
        qty = f"{a} {u}"
    elif a:
        qty = a

    item_style.apply(printer)
    body_width = item_style.width_chars(column_width)

    prefix = f"- {qty} " if qty else "- "
    suffix = f" ({parent})" if parent else ""
    body = name + suffix
    body_budget = max(8, body_width - len(prefix))

    lines = textwrap.wrap(body, width=body_budget, break_long_words=True) or [""]
    printer.text(prefix + lines[0] + "\n")
    indent = " " * len(prefix)
    for cont in lines[1:]:
        printer.text(indent + cont + "\n")

    # HA-recipes often stores the original ingredient text in `note` and the
    # matched product in `product_name`; suppress the duplicate.
    if note and not _note_is_duplicate(note, name, parent):
        note_style.apply(printer)
        note_width = note_style.width_chars(column_width)
        for nl in textwrap.wrap(note, width=note_width - 4) or [""]:
            printer.text("    " + nl + "\n")
        item_style.apply(printer)


def _note_is_duplicate(note: str, name: str, parent: str) -> bool:
    n = note.strip().lower()
    if not n:
        return True
    name_l = (name or "").strip().lower()
    parent_l = (parent or "").strip().lower()
    if not name_l and not parent_l:
        return False
    return n == name_l or n == parent_l or n in name_l or name_l in n


def _prepare_image(raw: bytes, target_width: int = 384) -> Image.Image:
    """Decode → resize → grayscale → Floyd-Steinberg dither → 1-bit mode."""
    img = Image.open(io.BytesIO(raw))
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    if w != target_width:
        new_h = max(1, int(h * (target_width / w)))
        img = img.resize((target_width, new_h), Image.LANCZOS)
    img = img.convert("L").convert("1", dither=Image.FLOYDSTEINBERG)
    return img
