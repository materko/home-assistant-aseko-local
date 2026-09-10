"""Public entry point for decoding a v7 (120-byte binary) frame.

A thin facade over ``decoding/``: parse the frame, detect its profile, run
the profile's plan.  Kept under its old name so the server and the test
suite keep calling ``AsekoDecoder.decode(bytes)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .aseko_data import AsekoDevice, AsekoDeviceType, AsekoProbeType
from .decoding import engine
from .decoding.decoders import Configuration
from .decoding.frame import (
    Protocol,
    decode_time,
    decode_timestamp,
    normalize_value,
    parse_v7,
)
from .decoding.profiles import detect_profile, profile_for

if TYPE_CHECKING:
    from .decoding.profile import ProfileMemory


class AsekoDecoder:
    """Decoder of Aseko unit data."""

    @staticmethod
    def decode(data: bytes, memory: ProfileMemory | None = None) -> AsekoDevice:
        """Decode one 120-byte frame into an ``AsekoDevice``.

        ``memory`` lets a long-lived caller (the server) carry the last
        confidently detected firmware variant from frame to frame; without
        it every frame is decoded on its own.
        """
        frame = parse_v7(data)
        profile, firmware = detect_profile(frame, memory)
        return engine.decode(frame, profile, firmware)

    # -- helpers kept for existing callers and tests ------------------------

    _normalize_value = staticmethod(normalize_value)
    _timestamp = staticmethod(decode_timestamp)
    _time = staticmethod(decode_time)

    @staticmethod
    def _configuration(
        data: bytes, device_type: AsekoDeviceType | None = None
    ) -> set[AsekoProbeType]:
        """Read the installed probes the way ``device_type``'s profile does."""
        profile = profile_for(Protocol.V7, device_type)
        feature = Configuration()
        read = getattr(feature, profile.variant_for(Configuration))
        return read(parse_v7(data), AsekoDevice(device_type=device_type))
