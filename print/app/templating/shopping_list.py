"""Render a shopping list onto an escpos printer-like object.

The caller submits items already grouped into aisles. HA-print only renders.
"""
from __future__ import annotations

from typing import Any

from .common import divider, fmt_amount, now_stamp, qty_unit, safe_text


def render(
    printer,
    *,
    title: str = "Ostoslista",
    timestamp: str | None = None,
    aisles: list[dict] | None = None,
    done_filter: str = "strike",
    column_width: int = 48,
) -> dict[str, int]:
    """Render the receipt. Returns a small summary dict.

    `aisles` is a list of `{label: str, items: [{name, amount, unit, done, note}]}`.
    `done_filter` is one of "skip" (drop done items), "strike" (print with line
    through them) or "include" (print as normal). Default is "strike".
    """
    aisles = aisles or []
    ts = timestamp or now_stamp()

    items_printed = 0

    # ── Header ──────────────────────────────────────────────────────────────
    printer.set(align="center", bold=True, double_height=True, double_width=True)
    printer.text(safe_text(title) + "\n")
    printer.set(align="center", bold=False, double_height=False, double_width=False)
    printer.text(ts + "\n")
    printer.set(align="left")
    printer.text(divider(column_width) + "\n")

    # ── Aisles ──────────────────────────────────────────────────────────────
    for aisle in aisles:
        label = safe_text(aisle.get("label") or "")
        items = aisle.get("items") or []
        # Apply done_filter
        visible = []
        for it in items:
            if it.get("done") and done_filter == "skip":
                continue
            visible.append(it)
        if not visible:
            continue

        printer.text("\n")
        printer.set(bold=True, underline=1)
        printer.text((label or "Muut") + "\n")
        printer.set(bold=False, underline=0)

        for it in visible:
            _render_item(printer, it, done_filter=done_filter, column_width=column_width)
            items_printed += 1

    if items_printed == 0:
        printer.text("\n")
        printer.set(align="center")
        printer.text("(tyhja lista)\n")
        printer.set(align="left")

    return {"items_printed": items_printed, "aisles_printed": sum(1 for a in aisles if a.get("items"))}


def _render_item(printer, item: dict[str, Any], *, done_filter: str, column_width: int) -> None:
    name = safe_text(item.get("name") or "")
    qty = qty_unit(item.get("amount"), item.get("unit"))
    note = safe_text(item.get("note") or "")
    done = bool(item.get("done"))

    box = "[x]" if done else "[ ]"
    qty_col = qty.ljust(7)[:7] if qty else "       "
    line = f"{box} {qty_col} {name}"
    # Trim to column width so we don't wrap mid-line on the printer
    if len(line) > column_width:
        line = line[: column_width - 1] + "…"
    printer.text(line + "\n")

    if done and done_filter == "strike":
        # ESC/POS has no native strikethrough — overprint a row of "-" the same
        # length as the line we just printed. This works because the printer
        # advances by one line, but we use ESC d 0 / line feed reset trick by
        # printing on the next line; visually it looks like an underline of
        # equal width, which the eye reads as "done". Good enough for v1.
        bar = "-" * min(len(line), column_width)
        printer.text(bar + "\n")

    if note:
        # Font B (smaller) for the note
        try:
            printer.set(font="b")
        except Exception:  # noqa: BLE001
            pass
        printer.text("   " + note[: column_width - 3] + "\n")
        try:
            printer.set(font="a")
        except Exception:  # noqa: BLE001
            pass
