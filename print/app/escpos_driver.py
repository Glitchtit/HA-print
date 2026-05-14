"""Thin wrapper around python-escpos's Network printer.

The rendering modules (templating/*.py) operate on any escpos printer-like
object — Network in production, Dummy in tests. This module owns the
connection lifecycle: connect, force codepage, render, partial-cut, close.
"""
from __future__ import annotations

import logging
import socket
from contextlib import contextmanager
from typing import Iterator, Optional

from escpos.printer import Network

from .options import Options

logger = logging.getLogger(__name__)


class PrinterError(RuntimeError):
    """Raised on any failure to talk to the printer."""


def probe_printer(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return True if a TCP connection to the printer succeeds quickly."""
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


@contextmanager
def thermal_printer(options: Options) -> Iterator[Network]:
    """Open a Network printer, force codepage on enter, partial-cut on exit."""
    if not options.printer_host:
        raise PrinterError("printer_host is not configured")

    try:
        printer = Network(
            options.printer_host,
            port=options.printer_port,
            timeout=8,
            profile=options.printer_profile,
        )
    except Exception as exc:  # noqa: BLE001 — wrap all socket/profile errors
        raise PrinterError(f"Failed to open printer: {exc}") from exc

    try:
        try:
            printer.charcode(options.codepage)
        except Exception as exc:  # noqa: BLE001
            logger.warning("charcode(%s) failed: %s", options.codepage, exc)

        yield printer

        if options.enable_cut:
            try:
                printer.ln(6)
                printer.cut(mode="PART")
            except Exception as exc:  # noqa: BLE001
                logger.warning("cut failed: %s", exc)
    except (OSError, socket.timeout) as exc:
        raise PrinterError(f"Connection lost: {exc}") from exc
    finally:
        try:
            printer.close()
        except Exception:  # noqa: BLE001
            pass
