"""Render a recipe onto an escpos printer-like object.

Includes optional hero image rendering via Pillow (downscale → 1-bit dither).
Body text uses Font B (smaller, ~33% denser) so a recipe fits on less paper.
"""
from __future__ import annotations

import io
import logging
import textwrap
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

    # Body uses Font B → ~33% more chars per physical line on the XP-80T
    # default profile (~42 chars vs 32 in Font A). Track separately so the
    # caller's `column_width` stays the Font A budget.
    body_width = max(column_width, int(column_width * 4 / 3))

    # ── Title block ────────────────────────────────────────────────────────
    # Bold + double-height keeps the title prominent without burning horizontal
    # width on a double-wide that would only fit ~16 chars on a real XP-80T.
    printer.set(align="center", bold=True, double_height=True, double_width=False, font="a")
    printer.text(name + "\n")
    printer.set(bold=False, double_height=False, double_width=False)
    if servings is not None:
        printer.text(f"Annokset: {fmt_amount(servings)}\n")
    printer.set(align="left")

    # Switch to Font B for the rest of the body.
    try:
        printer.set(font="b")
    except Exception:  # noqa: BLE001
        pass

    printer.text(divider(body_width) + "\n")

    # ── Ingredients ────────────────────────────────────────────────────────
    printer.set(bold=True, underline=1, font="b")
    printer.text("Ainekset\n")
    printer.set(bold=False, underline=0, font="b")

    for ing in ingredients:
        _render_ingredient(printer, ing, column_width=body_width)

    printer.text(divider(body_width) + "\n")

    # ── Instructions ───────────────────────────────────────────────────────
    printer.set(bold=True, underline=1, font="b")
    printer.text("Ohjeet\n")
    printer.set(bold=False, underline=0, font="b")

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

    # Source line (already Font B) — wrap, don't truncate.
    src = safe_text(recipe.get("source_url") or "")
    if src:
        for line in textwrap.wrap(src, width=body_width) or [""]:
            printer.text(line + "\n")

    # Restore Font A so the cut/feed in the driver leaves things clean.
    try:
        printer.set(font="a", bold=False, underline=0)
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

    # Compact prefix: "- 200 g " or "- " when no qty — no fixed padding column.
    prefix = f"- {qty} " if qty else "- "
    suffix = f" ({parent})" if parent else ""
    body = name + suffix
    body_width = max(8, column_width - len(prefix))

    lines = textwrap.wrap(body, width=body_width, break_long_words=True) or [""]
    printer.text(prefix + lines[0] + "\n")
    indent = " " * len(prefix)
    for cont in lines[1:]:
        printer.text(indent + cont + "\n")

    # HA-recipes often stores the original ingredient text in `note` and the
    # matched product in `product_name`; when they're identical (or the note is
    # a substring of the name), printing the note duplicates the line. Skip.
    if note and not _note_is_duplicate(note, name, parent):
        note_lines = textwrap.wrap(note, width=column_width - 4) or [""]
        for nl in note_lines:
            printer.text("    " + nl + "\n")


def _note_is_duplicate(note: str, name: str, parent: str) -> bool:
    n = note.strip().lower()
    if not n:
        return True
    name_l = (name or "").strip().lower()
    parent_l = (parent or "").strip().lower()
    if not name_l and not parent_l:
        return False
    # Exact, or note is a substring of the name (or vice-versa).
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
