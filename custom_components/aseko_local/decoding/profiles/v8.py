"""v8 profiles: the text protocol, firmware 8.x, port 51050.

Every v8 frame observed so far uses the same layout regardless of the
header's type field, so SALT takes over the NET list -- minus the chlorine
pump: a SALT makes its chlorine by electrolysis, and the Aseko Live app gives
its Salt units a pH- and an algicide canister and an electrode, but no
chlorine canister.

Values v8 does not transmit -- pump flow rates above all -- are not listed
rather than invented, with one deliberate exception: the chlorine and
pH-minus flow rates are assumed at 60 ml/min so the consumption counters
have something to integrate.
"""

from __future__ import annotations

from ...aseko_data import AsekoDeviceType
from ..decoders import (
    ChlorinePumpRunning,
    Configuration,
    DosingDelay,
    StartupDelay,
    FiltrationRunning,
    ChlorineFlowRate,
    PhMinusFlowRate,
    Ph,
    PhMinusPumpRunning,
    PoolVolume,
    Redox,
    PhTarget,
    RedoxTarget,
    SerialNumber,
    Timestamp,
    WaterFlowToProbes,
    WaterTemperature,
)
from ..frame import Protocol
from ..profile import Profile

#: Header field f2 -> model.  Unknown values fall back to NET with a warning.
MODEL_BY_HEADER_TYPE: dict[int, AsekoDeviceType] = {
    105: AsekoDeviceType.SALT,  # ASIN Aqua Salt NET
    804: AsekoDeviceType.NET,
    805: AsekoDeviceType.NET,
    812: AsekoDeviceType.NET,
}

_FEATURES = (
    SerialNumber,
    Configuration,
    Timestamp,
    WaterTemperature,
    WaterFlowToProbes,
    Ph,
    Redox,
    FiltrationRunning,
    PhMinusPumpRunning,
    ChlorinePumpRunning,
    PhMinusFlowRate,
    ChlorineFlowRate,
    PhTarget,
    RedoxTarget,
    PoolVolume,
    StartupDelay,
    DosingDelay,
)

_SALT_FEATURES = tuple(
    f for f in _FEATURES if f not in (ChlorinePumpRunning, ChlorineFlowRate)
)

NET = Profile(
    name="v8 NET",
    protocol=Protocol.V8,
    model=AsekoDeviceType.NET,
    features=_FEATURES,
    evidence={
        ChlorinePumpRunning: "unconfirmed: outs[9] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running",
        Configuration: "derived: a probe is installed when its ains slot is not -500",
        DosingDelay: "confirmed: areqs[18] = 2 min vs the app",
        StartupDelay: "confirmed: areqs[17] = 2 min vs the app",
        FiltrationRunning: "confirmed: outs[2] = 1 while the app showed 'Pump: ON / NONSTOP' (2026-04-13)",
        ChlorineFlowRate: "assumed: not transmitted, 60 ml/min taken for consumption",
        PhMinusFlowRate: "assumed: not transmitted, 60 ml/min taken for consumption",
        Ph: "confirmed: ains[0] / 100 vs the app (6.49 vs 6.56, later reading), serial 110203680",
        PhMinusPumpRunning: "unconfirmed: outs[8] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running",
        PoolVolume: "confirmed: areqs[14] = 45 m3 vs the app",
        Redox: "confirmed: ains[6] = 809 mV vs 848 mV in the app (later reading), serial 110203680",
        PhTarget: "confirmed: areqs[0] / 10 = 7.4 vs the app",
        RedoxTarget: "confirmed: areqs[1] * 10 = 740 mV vs the app",
        SerialNumber: "confirmed: header token 2, serial 110203680",
        Timestamp: "confirmed: ins[16] hour, ins[17] minute match the HA log; date taken from HA",
        WaterFlowToProbes: "confirmed: ins[8] = 1 while the app showed 'Water flow: YES'",
        WaterTemperature: "confirmed: ins[0] / 10 = 31.4 C (Sep 2025) and 18.0 C (Apr 2026) vs the app",
    },
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

BY_MODEL: dict[AsekoDeviceType, Profile] = {
    AsekoDeviceType.NET: NET,
    AsekoDeviceType.SALT: SALT,
}
