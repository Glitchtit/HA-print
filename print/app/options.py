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
            column_width=int(data.get("column_width", 32) or 32),
            debug=bool(data.get("debug", False)),
        )
