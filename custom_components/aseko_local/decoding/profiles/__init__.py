"""The profile registry and the lookup from a parsed frame into it."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...aseko_data import AsekoDeviceType, AsekoFirmwareVariant
from ..frame import Protocol, V8Frame
from ..profile import Profile, home_firmware_from_byte37, unit_type_from_byte
from . import v7, v8

if TYPE_CHECKING:
    from ..frame import V7Frame
    from ..profile import ProfileMemory

_LOGGER = logging.getLogger(__name__)

#: Every profile, in the order the support matrix lists them.  Includes the
#: two fallbacks below, which the matrix mentions but does not tabulate.
ALL_PROFILES: tuple[Profile, ...] = (
    v7.HOME_A,
    v7.HOME_B,
    v7.HOME_UNKNOWN_FIRMWARE,
    v7.SALT,
    v7.OXY,
    v7.NET,
    v7.PROFI,
    v7.UNKNOWN,
    v8.NET,
    v8.SALT,
)

#: Profiles no unit is *meant* to decode with: the frame did not allow the
#: proper one to be picked.  Real decoding paths, but not answers to "what
#: does my model support", so the support matrix keeps them out of its tables.
FALLBACK_PROFILES: tuple[Profile, ...] = (v7.HOME_UNKNOWN_FIRMWARE, v7.UNKNOWN)


def profile_for(
    protocol: Protocol,
    model: AsekoDeviceType | None,
    firmware: AsekoFirmwareVariant | None = None,
) -> Profile:
    """Return the profile for a known combination.

    HOME with the firmware variant not established resolves to a profile
    of its own that reads only what both revisions share, so nothing gets
    an entity on the strength of a guess.
    """
    if protocol is Protocol.V8:
        return v8.BY_MODEL[model]
    if model is AsekoDeviceType.HOME:
        if firmware is AsekoFirmwareVariant.HOME_A:
            return v7.HOME_A
        if firmware is AsekoFirmwareVariant.HOME_B:
            return v7.HOME_B
        return v7.HOME_UNKNOWN_FIRMWARE
    return v7.BY_MODEL[model]


def detect_profile(
    frame: V7Frame | V8Frame,
    memory: ProfileMemory | None = None,
) -> tuple[Profile, AsekoFirmwareVariant | None]:
    """Pick the profile for ``frame``: protocol, then model, then firmware.

    Runs on every frame, not once at setup.  Returns the profile together
    with the firmware variant detection actually established, which is None
    where the model has no variants or the frame did not allow one to be
    told apart -- in that case ``memory``, when given, supplies the last
    variant seen for this serial number.
    """
    if isinstance(frame, V8Frame):
        model = v8.MODEL_BY_HEADER_TYPE.get(frame.header_type)
        if model is None:
            _LOGGER.warning(
                "Unknown V8 header type %s for serial %s - falling back to NET. "
                "Please report this at https://github.com/hopkins-tk/home-assistant-aseko-local/issues",
                frame.header_type,
                frame.serial_number,
            )
            model = AsekoDeviceType.NET
        return v8.BY_MODEL[model], None

    model = unit_type_from_byte(frame.unit_type)
    firmware: AsekoFirmwareVariant | None = None
    if model is AsekoDeviceType.HOME:
        firmware = home_firmware_from_byte37(frame[37])
        if memory is not None:
            if firmware is None:
                firmware = memory.recall(frame.serial_number)
            else:
                memory.remember(frame.serial_number, firmware)
    return profile_for(Protocol.V7, model, firmware), firmware


__all__ = [
    "ALL_PROFILES",
    "FALLBACK_PROFILES",
    "detect_profile",
    "profile_for",
    "v7",
    "v8",
]
