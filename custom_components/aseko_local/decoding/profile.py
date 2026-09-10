"""A profile: what one (protocol, model, firmware) combination reads, and how.

The profile is the only place that knows models.  It lists the features a
device has, names a different reading for the few that are encoded
differently on this model, records the evidence behind each entry, and
carries the semantic flags consumers need instead of a device type.

Validation happens at construction, i.e. at import time: a feature listed
without a reading for the profile's protocol, an override naming a reading
the feature does not have, or a dependency cycle all fail before a single
frame is decoded.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..aseko_data import AsekoDeviceType, AsekoFirmwareVariant, AsekoProfileFlag
from ..const import (
    UNIT_TYPE_HOME,
    UNIT_TYPE_NET,
    UNIT_TYPE_OXY,
    UNIT_TYPE_PROFI,
    UNIT_TYPE_SALT,
    UNSPECIFIED_VALUE,
)
from .frame import Protocol

if TYPE_CHECKING:
    from ..aseko_data import AsekoDevice
    from .feature import Feature

_LOGGER = logging.getLogger(__name__)

Reader = Callable[[Any, "AsekoDevice"], Any]


@dataclass(frozen=True)
class Profile:
    """One (protocol, model, firmware) combination and everything it reads."""

    name: str
    protocol: Protocol
    #: None for a v7 unit type nobody has mapped yet.
    model: AsekoDeviceType | None
    firmware: AsekoFirmwareVariant | None = None
    #: The features this device has.  Order is a hint only; dependencies win.
    features: tuple[type[Feature], ...] = ()
    #: Feature -> name of the reading to use instead of the protocol default.
    overrides: Mapping[type[Feature], str] = field(default_factory=dict)
    #: Feature -> why we believe this profile reads it the way it does.
    evidence: Mapping[type[Feature], str] = field(default_factory=dict)
    flags: frozenset[AsekoProfileFlag] = frozenset()

    #: Decoding order with the bound reading for each feature.  Built once.
    plan: tuple[tuple[Feature, Reader], ...] = field(
        init=False, repr=False, compare=False
    )
    #: Names of the AsekoDevice fields this profile fills.
    feature_names: frozenset[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._validate()
        plan = []
        for feature_cls in _ordered(self.features):
            feature = feature_cls()
            plan.append((feature, getattr(feature, self.variant_for(feature_cls))))
        object.__setattr__(self, "plan", tuple(plan))
        object.__setattr__(
            self, "feature_names", frozenset(f.field for f in self.features)
        )

    def variant_for(self, feature: type[Feature]) -> str:
        """Name of the reading this profile uses for ``feature``."""
        override = self.overrides.get(feature)
        if override is not None:
            return override
        default = feature.default_variant(self.protocol)
        if default is None:
            raise ValueError(
                f"{self.name}: {feature.__name__} has no {self.protocol.value} reading"
            )
        return default

    def _validate(self) -> None:
        listed = set(self.features)
        if len(listed) != len(self.features):
            raise ValueError(f"{self.name}: a feature is listed twice")
        fields = [f.field for f in self.features]
        if len(set(fields)) != len(fields):
            raise ValueError(f"{self.name}: two features fill the same field")

        for feature, variant in self.overrides.items():
            if feature not in listed:
                raise ValueError(
                    f"{self.name}: override for unlisted {feature.__name__}"
                )
            if not variant.startswith(f"decode_{self.protocol.value}"):
                raise ValueError(
                    f"{self.name}: {feature.__name__}.{variant} is not a "
                    f"{self.protocol.value} reading"
                )
            if not feature.has_variant(variant):
                raise ValueError(
                    f"{self.name}: {feature.__name__} has no reading {variant!r}"
                )
        for feature in self.evidence:
            if feature not in listed:
                raise ValueError(
                    f"{self.name}: evidence for unlisted {feature.__name__}"
                )
        for feature in self.features:
            self.variant_for(feature)  # raises when there is nothing to call


def _ordered(features: tuple[type[Feature], ...]) -> list[type[Feature]]:
    """Return ``features`` with every dependency ahead of its dependant.

    Stable: features stay in listed order unless a dependency forces a move.
    A dependency that is not listed is simply not decoded; the dependant
    sees None for it, which every reading treats as "not configured".
    """
    listed = set(features)
    done: list[type[Feature]] = []
    seen: set[type[Feature]] = set()
    visiting: set[type[Feature]] = set()

    def visit(feature: type[Feature]) -> None:
        if feature in seen:
            return
        if feature in visiting:
            raise ValueError(f"dependency cycle through {feature.__name__}")
        visiting.add(feature)
        for dependency in feature.depends_on:
            if dependency in listed:
                visit(dependency)
        visiting.remove(feature)
        seen.add(feature)
        done.append(feature)

    for feature in features:
        visit(feature)
    return done


# ---------------------------------------------------------------------------
# Detection helpers: frame bytes -> model / firmware.  Pure functions; the
# lookup into the registry lives in ``profiles/__init__.py``.
# ---------------------------------------------------------------------------


def unit_type_from_byte(value: int) -> AsekoDeviceType | None:
    """Map v7 byte[4] to a model, or None for a value nobody has mapped yet.

    byte[4] carries the probe configuration in its low bits, so models are
    ranges rather than exact values: NET is 0x09-0x0B, SALT 0x0D-0x0F, HOME
    0x02-0x04.  OXY (0x05) and PROFI (0x10, unconfirmed) are exact.
    """
    if value == UNIT_TYPE_PROFI:
        return AsekoDeviceType.PROFI
    if value > UNIT_TYPE_SALT:
        return AsekoDeviceType.SALT
    if value > UNIT_TYPE_NET:
        return AsekoDeviceType.NET
    if value == UNIT_TYPE_OXY:
        return AsekoDeviceType.OXY
    if value >= UNIT_TYPE_HOME:
        return AsekoDeviceType.HOME

    _LOGGER.warning("Unknown unit type: %s", value)
    return None


# HOME firmware A sets bit 0x40 of byte[37] in every observed value (high
# nibble 0x4 / 0x5); firmware B never does (0x0 / 0x1 / 0x3).
_HOME_FIRMWARE_A_BIT = 0x40


def home_firmware_from_byte37(value: int) -> AsekoFirmwareVariant | None:
    """Tell the two HOME encodings apart, or None when byte[37] is unset."""
    if value == UNSPECIFIED_VALUE:
        return None
    if value & _HOME_FIRMWARE_A_BIT:
        return AsekoFirmwareVariant.HOME_A
    return AsekoFirmwareVariant.HOME_B


class ProfileMemory:
    """The last firmware variant confidently detected, per serial number.

    Detection runs on every frame, but byte[37] is 0xFF on some HOME frames
    and then says nothing about the firmware.  Rather than lock a guess in
    at setup, the decoder remembers the last frame that did allow the
    variant to be told apart and falls back to that.
    """

    def __init__(self) -> None:
        self._firmware: dict[int, AsekoFirmwareVariant] = {}

    def remember(self, serial_number: int, firmware: AsekoFirmwareVariant) -> None:
        self._firmware[serial_number] = firmware

    def recall(self, serial_number: int) -> AsekoFirmwareVariant | None:
        return self._firmware.get(serial_number)
