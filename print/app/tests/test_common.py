"""Unit tests for shared templating helpers."""
from __future__ import annotations

from app.templating.common import safe_text


def test_safe_text_swaps_typography_cp858_lacks():
    s = "a – b — c ‒ d − e ‘f’ ‚g′ “h” „i″ j… • k l m"
    out = safe_text(s)
    assert out == "a - b - c - d - e 'f' 'g' \"h\" \"i\" j... * k l m"
    out.encode("cp858")  # strict: raises if anything unprintable is left


def test_safe_text_keeps_characters_cp858_has():
    assert safe_text("äöå é € ½ · Æ") == "äöå é € ½ · Æ"


def test_safe_text_still_strips_tags_and_nbsp():
    assert safe_text(" <b>Maito</b>\xa0 ") == "Maito"
