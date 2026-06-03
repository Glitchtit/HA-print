"""Load add-on options from /data/options.json (written by Supervisor)."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Options:
    printer_host: str
    printer_port: int
    printer_profile: str
    codepage: str
    image_impl: str
    enable_cut: bool
    column_width: int
    debug: bool
    title_style: str
    header_style: str
    item_style: str
    note_style: str
    beep_after_print: bool
    beep_count: int
    beep_duration_ms: int
    print_density: int
    header_text: str
    footer_text: str
    # Defaults at the end so existing positional/keyword constructions (and the
    # test fixtures) keep working without naming these.
    full_width_px: int = 576
    svg_default_dither: bool = False
    cut_feed_lines: int = 0

    @classmethod
    def load(cls, path: str = "/data/options.json") -> "Options":
        data: dict = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError) as exc:
                logger.warning("Failed to read %s: %s", path, exc)
        return cls(
            printer_host=str(data.get("printer_host", "")).strip(),
            printer_port=int(data.get("printer_port", 9100)),
            printer_profile=str(data.get("printer_profile", "default") or "default"),
            codepage=str(data.get("codepage", "CP858") or "CP858"),
            image_impl=str(data.get("image_impl", "bitImageRaster") or "bitImageRaster"),
            enable_cut=bool(data.get("enable_cut", True)),
            column_width=int(data.get("column_width", 48) or 48),
            debug=bool(data.get("debug", False)),
            title_style=str(data.get("title_style", "a1x2-bold") or "a1x2-bold"),
            header_style=str(data.get("header_style", "a-bold-underline") or "a-bold-underline"),
            item_style=str(data.get("item_style", "b") or "b"),
            note_style=str(data.get("note_style", "b") or "b"),
            beep_after_print=bool(data.get("beep_after_print", False)),
            beep_count=_clamp(int(data.get("beep_count", 2) or 2), 1, 9),
            beep_duration_ms=_clamp(int(data.get("beep_duration_ms", 200) or 200), 50, 1000),
            print_density=_clamp(int(data.get("print_density", 5) or 5), 0, 8),
            header_text=str(data.get("header_text", "") or ""),
            footer_text=str(data.get("footer_text", "") or ""),
            full_width_px=_clamp(int(data.get("full_width_px", 576) or 576), 8, 576),
            svg_default_dither=bool(data.get("svg_default_dither", False)),
            cut_feed_lines=_clamp(int(data.get("cut_feed_lines", 0) or 0), 0, 20),
        )


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))
