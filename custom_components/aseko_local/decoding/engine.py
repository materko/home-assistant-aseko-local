"""The decode loop.  Knows no bytes and no models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..aseko_data import AsekoDevice
from .frame import parse_frame
from .presence import NOT_PRESENT
from .profiles import detect_profile

if TYPE_CHECKING:
    from .frame import V7Frame, V8Frame
    from .profile import Profile


def decode(
    frame: V7Frame | V8Frame,
    profile: Profile,
) -> AsekoDevice:
    """Fill an ``AsekoDevice`` from ``frame`` the way ``profile`` says to.

    Each feature's chosen reading gets the frame and the device as filled so
    far, so a feature listed after its dependencies can read their values.

    ``device.features`` ends up as the fields *this unit* has: the profile's
    list minus every reading that answered ``NOT_PRESENT`` (see
    ``presence``).  A field the unit has but could not read in this frame is
    in ``features`` with the value None.
    """
    device = AsekoDevice(
        device_type=profile.model,
        flags=profile.flags,
    )
    present: set[str] = set()
    for feature, read in profile.plan:
        value = read(frame, device)
        if value is NOT_PRESENT:
            value = None
        else:
            present.add(feature.field)
        setattr(device, feature.field, value)
    device.features = frozenset(present)
    return device


def decode_raw(raw: bytes) -> AsekoDevice:
    """Parse, detect and decode in one go.  Raises ValueError on a bad v8 frame."""
    frame = parse_frame(raw)
    return decode(frame, detect_profile(frame))
