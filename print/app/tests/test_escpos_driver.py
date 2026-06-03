"""Driver-level tests: the pre-cut feed must not waste paper.

Regression guard for the ~35mm-of-blank-paper bug, where the driver fed 6 lines
manually *and* python-escpos's cut() fed 6 more by default.
"""
from __future__ import annotations

from escpos.printer import Dummy

from app import escpos_driver
from app.options import Options


class FakeNetwork(Dummy):
    """A Dummy that accepts Network's constructor args and ignores close()."""

    def __init__(self, *args, **kwargs):
        super().__init__()

    def close(self):  # keep the captured buffer after the context exits
        pass


def _opts(**overrides) -> Options:
    o = Options.load(path="/nonexistent.json")
    o.printer_host = "127.0.0.1"
    for k, v in overrides.items():
        setattr(o, k, v)
    return o


def test_cut_uses_function_b_without_double_feed(monkeypatch):
    monkeypatch.setattr(escpos_driver, "Network", FakeNetwork)
    opts = _opts(enable_cut=True, cut_feed_lines=0)
    with escpos_driver.thermal_printer(opts) as p:
        p.text("hello\n")
    out = p.output
    assert out.endswith(b"\x1dVB\x00")  # GS V B 0 — feed-to-cutter + partial cut
    assert b"\x1bd\x06" not in out  # no ESC d 6 manual feed (the old waste)


def test_cut_feed_lines_adds_exactly_one_feed(monkeypatch):
    monkeypatch.setattr(escpos_driver, "Network", FakeNetwork)
    opts = _opts(enable_cut=True, cut_feed_lines=4)
    with escpos_driver.thermal_printer(opts) as p:
        pass
    out = p.output
    assert b"\x1bd\x04" in out  # one ESC d 4 margin feed
    assert out.endswith(b"\x1dVB\x00")


def test_no_cut_command_when_disabled(monkeypatch):
    monkeypatch.setattr(escpos_driver, "Network", FakeNetwork)
    opts = _opts(enable_cut=False)
    with escpos_driver.thermal_printer(opts) as p:
        pass
    assert b"\x1dV" not in p.output  # no GS V cut at all
