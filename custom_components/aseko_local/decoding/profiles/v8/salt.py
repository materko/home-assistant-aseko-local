"""v8 profile: ASIN AQUA Salt NET.

Takes over the NET layout minus the chlorine pump: a SALT makes its chlorine
by electrolysis, and the Aseko Live app gives its Salt units a pH- and an
algicide canister and an electrode, but no chlorine canister.
"""

from __future__ import annotations

from ....aseko_data import AsekoDeviceType
from ...decoders import (
    ChlorineFlowRate,
    ChlorinePumpRunning,
    Configuration,
    DosingDelay,
    FiltrationRunning,
    Ph,
    PhMinusFlowRate,
    PhMinusPumpRunning,
    PhTarget,
    PoolVolume,
    Redox,
    RedoxTarget,
    SerialNumber,
    StartupDelay,
    Timestamp,
    WaterFlowToProbes,
    WaterTemperature,
)
from ...frame import Protocol
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
    evidence={
        Configuration: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        DosingDelay: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        StartupDelay: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        FiltrationRunning: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        PhMinusFlowRate: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        Ph: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        PhMinusPumpRunning: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        PoolVolume: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        Redox: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        PhTarget: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        RedoxTarget: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        SerialNumber: "confirmed: header token 2 on every captured frame",
        Timestamp: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        WaterFlowToProbes: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        WaterTemperature: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
    },
)
