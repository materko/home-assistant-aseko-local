"""Public entry point for decoding a v8 text frame.

A thin facade over ``decoding/``: parse the frame, detect its profile, run
the profile's plan.  Kept under its old name so the server and the test
suite keep calling ``AsekoV8Decoder.decode(bytes)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .decoding import engine
from .decoding.frame import parse_v8
from .decoding.profiles import detect_profile

if TYPE_CHECKING:
    from .aseko_data import AsekoDevice


class AsekoV8Decoder:
    """Decoder for Aseko fw v8 text frames."""

    @classmethod
    def decode(cls, raw: bytes) -> AsekoDevice:
        """Decode a raw v8 frame into an ``AsekoDevice``.

        Raises ValueError if the frame cannot be parsed.
        """
        frame = parse_v8(raw)
        return engine.decode(frame, detect_profile(frame))
