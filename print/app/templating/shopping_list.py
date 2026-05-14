"""Render a shopping list onto an escpos printer-like object.

The caller submits items already grouped into aisles. HA-print only renders.
"""
from __future__ import annotations

import textwrap
from typing import Any

from .common import divider, now_stamp, qty_unit, safe_text
from .style import TextStyle


def render(
    printer,
    *,
    title: str = "Ostoslista",
    timestamp: str | None = None,
    aisles: list[dict] | None = None,
    done_filter: str = "strike",
    column_width: int = 32,
    title_style: TextStyle | None = None,
    header_style: TextStyle | None = None,
    item_style: TextStyle | None = None,
    note_style: TextStyle | None = None,
) -> dict[str, int]:
    """Render the receipt. Returns a small summary dict.

    `aisles` is a list of `{label: str, items: [{name, amount, unit, done, note}]}`.
    `done_filter` is one of "skip" (drop done items), "strike" (print with line
    through them) or "include" (print as normal). Default is "strike".
    """
    aisles = aisles or []
    ts = timestamp or now_stamp()
    title_style = title_style or TextStyle.parse("a1x2-bold")
    header_style = header_style or TextStyle.parse("a-bold-underline")
    item_style = item_style or TextStyle.parse("b")
    note_style = note_style or TextStyle.parse("b")

    items_printed = 0

    # ── Header ──────────────────────────────────────────────────────────────
    printer.set(align="center")
    title_style.apply(printer)
    printer.text(safe_text(title) + "\n")
    TextStyle().apply(printer)  # reset
    printer.set(align="center")
    printer.text(ts + "\n")
    printer.set(align="left")
    printer.text(divider(column_width) + "\n")

    # ── Aisles ──────────────────────────────────────────────────────────────
    for aisle in aisles:
        label = safe_text(aisle.get("label") or "")
        items = aisle.get("items") or []
        visible = [it for it in items if not (it.get("done") and done_filter == "skip")]
        if not visible:
            continue

        printer.text("\n")
        header_style.apply(printer)
        printer.text((label or "Muut") + "\n")
        TextStyle().apply(printer)

        for it in visible:
            _render_item(
                printer,
                it,
                done_filter=done_filter,
                column_width=column_width,
                item_style=item_style,
                note_style=note_style,
            )
            items_printed += 1

    if items_printed == 0:
        printer.text("\n")
        printer.set(align="center")
        printer.text("(tyhja lista)\n")
        printer.set(align="left")

    # Reset state on exit so the cut/feed in the driver runs clean.
    TextStyle().apply(printer)
    return {
        "items_printed": items_printed,
        "aisles_printed": sum(1 for a in aisles if a.get("items")),
    }


def _render_item(
    printer,
    item: dict[str, Any],
    *,
    done_filter: str,
    column_width: int,
    item_style: TextStyle,
    note_style: TextStyle,
) -> None:
    name = safe_text(item.get("name") or "")
    qty = qty_unit(item.get("amount"), item.get("unit"))
    note = safe_text(item.get("note") or "")
    done = bool(item.get("done"))

    item_style.apply(printer)
    body_width = item_style.width_chars(column_width)

    box = "[x]" if done else "[ ]"
    # Compact prefix: "[ ] 1 " or "[ ] " when no qty — no fixed padding column.
    prefix = f"{box} {qty} " if qty else f"{box} "
    body_budget = max(8, body_width - len(prefix))

    lines = textwrap.wrap(name, width=body_budget, break_long_words=True) or [""]
    printer.text(prefix + lines[0] + "\n")
    indent = " " * len(prefix)
    for cont in lines[1:]:
        printer.text(indent + cont + "\n")

    if done and done_filter == "strike":
        printer.text(("-" * body_width) + "\n")

    if note:
        note_style.apply(printer)
        note_width = note_style.width_chars(column_width)
        for nl in textwrap.wrap(note, width=note_width - 4) or [""]:
            printer.text("   " + nl + "\n")
        item_style.apply(printer)  # back to item style for the next item
