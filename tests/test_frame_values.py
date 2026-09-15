"""The value helpers features read a frame with: what 0xFF and -500 turn into."""

from __future__ import annotations

import pytest

from custom_components.aseko_local.decoding.frames import (
    byte_when_flags,
    flag_or_none,
)
from custom_components.aseko_local.decoding.presence import NOT_PRESENT


@pytest.mark.parametrize(
    ("flags", "expected"),
    [(0x00, False), (0x08, True), (0xF7, False), (0x0C, True), (0xFF, None)],
)
def test_flag_or_none(flags, expected) -> None:
    assert flag_or_none(flags, 0x08) is expected


@pytest.mark.parametrize(
    ("flags", "expected"),
    [(0x80, 54), (0x00, NOT_PRESENT), (0xFF, NOT_PRESENT)],
)
def test_byte_when_flags_follows_the_routing_bit(flags, expected) -> None:
    assert byte_when_flags(54, flags, 0x80, 0x80) == expected
