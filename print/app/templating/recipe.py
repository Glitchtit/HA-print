"""Render a recipe onto an escpos printer-like object.

Includes optional hero image rendering via Pillow (downscale → 1-bit dither).
"""
from __future__ import annotations

import io
import logging
from typing import Any

from PIL import Image

from .common import divider, fmt_amount, safe_text, wrap

logger = logging.getLogger(__name__)


def render(
    printer,
    *,
    recipe: dict[str, Any],
    image_bytes: bytes | None = None,
    column_width: int = 48,
    image_impl: str = "bitImageRaster",
    image_width_px: int = 384,
) -> dict[str, int]:
    """Render a recipe. Returns a small summary dict."""
    name = safe_text(recipe.get("name") or "Recipe")
    servings = recipe.get("servings")
    ingredients = recipe.get("ingredients") or []
    instructions = recipe.get("instructions") or []

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
    printer.set(align="center", bold=True, double_height=True, double_width=True)
    printer.text(name + "\n")
    printer.set(bold=False, double_height=False, double_width=False)
    if servings is not None:
        printer.text(f"Annokset: {fmt_amount(servings)}\n")
    printer.set(align="left")
    printer.text(divider(column_width) + "\n")

    # ── Ingredients ────────────────────────────────────────────────────────
    printer.set(bold=True, underline=1)
    printer.text("Ainekset\n")
    printer.set(bold=False, underline=0)

    for ing in ingredients:
        _render_ingredient(printer, ing, column_width=column_width)

    printer.text(divider(column_width) + "\n")

    # ── Instructions ───────────────────────────────────────────────────────
    printer.set(bold=True, underline=1)
    printer.text("Ohjeet\n")
    printer.set(bold=False, underline=0)

    for i, step in enumerate(instructions, start=1):
        body = safe_text(step)
        if not body:
            continue
        prefix = f"{i}. "
        wrapped = wrap(body, width=column_width - len(prefix))
        first, *rest = wrapped or [""]
        printer.text(prefix + first + "\n")
        indent = " " * len(prefix)
        for cont in rest:
            printer.text(indent + cont + "\n")
        printer.text("\n")

    # Source line (small) — kept simple, no QR for v1
    src = safe_text(recipe.get("source_url") or "")
    if src:
        try:
            printer.set(font="b")
        except Exception:  # noqa: BLE001
            pass
        printer.text(src[: column_width * 2] + "\n")
        try:
            printer.set(font="a")
        except Exception:  # noqa: BLE001
            pass

    return {
        "ingredients_printed": len(ingredients),
        "steps_printed": len(instructions),
        "image_printed": 1 if image_bytes else 0,
    }


def _render_ingredient(printer, ing: dict[str, Any], *, column_width: int) -> None:
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

    qty_col = qty.ljust(8)[:8] if qty else "        "
    suffix = f" ({parent})" if parent else ""
    line = f"- {qty_col} {name}{suffix}"
    if len(line) > column_width:
        line = line[: column_width - 1] + "…"
    printer.text(line + "\n")

    if note:
        try:
            printer.set(font="b")
        except Exception:  # noqa: BLE001
            pass
        printer.text("    " + note[: column_width - 4] + "\n")
        try:
            printer.set(font="a")
        except Exception:  # noqa: BLE001
            pass


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
