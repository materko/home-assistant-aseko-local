"""The decode loop.  Knows no bytes and no models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..aseko_data import AsekoDevice
from .frame import parse_frame
from .profiles import detect_profile

if TYPE_CHECKING:
    from ..aseko_data import AsekoFirmwareVariant
    from .frame import V7Frame, V8Frame
    from .profile import Profile, ProfileMemory


def decode(
    frame: V7Frame | V8Frame,
    profile: Profile,
    firmware: AsekoFirmwareVariant | None = None,
) -> AsekoDevice:
    """Fill an ``AsekoDevice`` from ``frame`` the way ``profile`` says to.

    Each feature's chosen reading gets the frame and the device as filled so
    far, so a feature listed after its dependencies can read their values.
    ``firmware`` is what detection actually established for this frame; it
    can differ from ``profile.firmware`` when the frame did not allow the
    variant to be told apart and the profile is a fallback.
    """
    device = AsekoDevice(
        device_type=profile.model,
        firmware_variant=firmware,
        features=profile.feature_names,
        flags=profile.flags,
    )
    for feature, read in profile.plan:
        setattr(device, feature.field, read(frame, device))
    return device


def decode_raw(raw: bytes, memory: ProfileMemory | None = None) -> AsekoDevice:
    """Parse, detect and decode in one go.  Raises ValueError on a bad v8 frame."""
    frame = parse_frame(raw)
    profile, firmware = detect_profile(frame, memory)
    return decode(frame, profile, firmware)
