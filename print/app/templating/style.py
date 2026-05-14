"""Parse and apply ESC/POS text styles.

A *style spec* is a small string the user puts in the add-on config. Examples:

    "a"              Font A, normal
    "b"              Font B, normal (~33% narrower per char)
    "a2"             Font A, 2x width AND 2x height (double-wide title)
    "a1x2"           Font A, 1x width, 2x height (tall, narrow — the classic
                     receipt banner that doesn't waste horizontal width)
    "a2x1"           Font A, 2x width, 1x height (wide, short)
    "b-bold"         Font B, bold
    "a-bold-underline"
    "a1x2-bold"      Tall + bold

Modifiers (`-bold`, `-underline`) can appear in any order after the font.
Width/height multipliers cap at 4. Invalid specs fall back to defaults.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_SPEC_RE = re.compile(r"^([ab])(?:(\d+)x(\d+)|(\d+))?$")


@dataclass(frozen=True)
class TextStyle:
    font: str = "a"          # "a" or "b"
    width: int = 1           # 1-4 horizontal multiplier
    height: int = 1          # 1-4 vertical multiplier
    bold: bool = False
    underline: bool = False

    @classmethod
    def parse(cls, spec: str | None, default: "TextStyle | None" = None) -> "TextStyle":
        if not spec:
            return default or cls()
        parts = spec.strip().lower().replace("_", "-").split("-")
        font = (default or cls()).font
        width = (default or cls()).width
        height = (default or cls()).height
        bold = False
        underline = False
        any_font_seen = False
        for raw in parts:
            p = raw.strip()
            if not p:
                continue
            m = _SPEC_RE.match(p)
            if m:
                any_font_seen = True
                font = m.group(1)
                if m.group(2) and m.group(3):
                    width = _clamp(int(m.group(2)))
                    height = _clamp(int(m.group(3)))
                elif m.group(4):
                    n = _clamp(int(m.group(4)))
                    width = height = n
                else:
                    width = height = 1
                continue
            if p == "bold":
                bold = True
            elif p == "underline":
                underline = True
            else:
                logger.warning("Unknown style fragment %r in %r", p, spec)
        if not any_font_seen and default is not None:
            # Caller passed only modifiers — keep default font/size
            return cls(font=default.font, width=default.width, height=default.height,
                       bold=bold or default.bold, underline=underline or default.underline)
        return cls(font=font, width=width, height=height, bold=bold, underline=underline)

    # ── ESC/POS application ────────────────────────────────────────────────

    def apply(self, printer) -> None:
        """Set the printer state to this style. Falls back gracefully on
        firmwares that don't support custom_size for >2x."""
        try:
            if self.width <= 2 and self.height <= 2:
                printer.set(
                    font=self.font,
                    bold=self.bold,
                    underline=1 if self.underline else 0,
                    double_width=(self.width == 2),
                    double_height=(self.height == 2),
                    custom_size=False,
                )
            else:
                printer.set(
                    font=self.font,
                    bold=self.bold,
                    underline=1 if self.underline else 0,
                    custom_size=True,
                    width=self.width,
                    height=self.height,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to apply style %r: %s", self, exc)

    # ── Effective wrap width for this style ────────────────────────────────

    def width_chars(self, base_width: int) -> int:
        """Effective columns-per-line for this style.

        `base_width` is the Font A normal-scale budget (the `column_width`
        add-on option). Font B is ~33% narrower per char so more fits.
        Each unit of horizontal scale halves the budget.
        """
        factor = 1.33 if self.font == "b" else 1.0
        return max(4, int(base_width * factor / max(1, self.width)))


def _clamp(n: int, lo: int = 1, hi: int = 4) -> int:
    return max(lo, min(hi, n))
