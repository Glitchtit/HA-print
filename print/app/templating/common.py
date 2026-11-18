"""Shared helpers for receipt rendering."""
from __future__ import annotations

import textwrap
from datetime import datetime


def divider(width: int = 48, char: str = "-") -> str:
    return char * width


def wrap(text: str, width: int = 46) -> list[str]:
    """Word-wrap a paragraph, preserving manual line breaks."""
    out: list[str] = []
    for line in (text or "").splitlines() or [""]:
        if not line.strip():
            out.append("")
            continue
        pieces = textwrap.wrap(
            line,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
        )
        out.extend(pieces or [""])
    return out


def fmt_amount(amount: float | int | None) -> str:
    """Pretty-format a quantity, stripping trailing zeros."""
    if amount is None:
        return ""
    try:
        v = float(amount)
    except (ValueError, TypeError):
        return str(amount)
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def qty_unit(amount: float | int | None, unit: str | None) -> str:
    a = fmt_amount(amount)
    u = (unit or "").strip()
    if a and u:
        return f"{a} {u}"
    return a or u


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# Typographic characters CP858 lacks; python-escpos would print each as "?".
_ASCII_TYPOGRAPHY = str.maketrans({
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u2033": '"',
    "\u2026": "...",
    "\u2022": "*",
    "\u2009": " ", "\u202f": " ",
})


def safe_text(s: object) -> str:
    """Return a string suitable for ESC/POS — strip HTML tags defensively and
    swap dashes, curly quotes and the like for characters CP858 has."""
    if s is None:
        return ""
    out = str(s)
    while True:
        i = out.find("<")
        if i == -1:
            break
        j = out.find(">", i + 1)
        if j == -1:
            break
        out = out[:i] + out[j + 1 :]
    return out.replace("\xa0", " ").translate(_ASCII_TYPOGRAPHY).strip()
