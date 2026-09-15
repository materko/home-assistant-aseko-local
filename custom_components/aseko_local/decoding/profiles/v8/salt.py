"""v8 profile: ASIN AQUA Salt NET.

Takes over the NET layout minus the chlorine pump: a SALT makes its chlorine
by electrolysis, and the Aseko Live app gives its Salt units a pH- and an
algicide canister and an electrode, but no chlorine canister.
"""

from __future__ import annotations

from ....models import AsekoDeviceType, AsekoProfileFlag
from ...evidence import assumed, confirmed
from ...features import ChlorineFlowRate, ChlorinePumpRunning, SerialNumber
from ...frames import Protocol
from ...profile import Profile
from .common import FEATURES

_SALT_FEATURES = tuple(
    f for f in FEATURES if f not in (ChlorinePumpRunning, ChlorineFlowRate)
)


SALT = Profile(
    name="v8 SALT",
    protocol=Protocol.V8,
    model=AsekoDeviceType.SALT,
    features=_SALT_FEATURES,
    flags=frozenset({AsekoProfileFlag.DELAYS_IN_MINUTES}),
    evidence={
        # only the header type says SALT: every entry is the NET layout,
        # taken over, except what the header itself carries
        **dict.fromkeys(
            _SALT_FEATURES,
            assumed(
                "only the header type (105) says SALT; the NET layout is taken "
                "over unverified"
            ),
        ),
        SerialNumber: confirmed("header token 2 on every captured frame"),
    },
)
