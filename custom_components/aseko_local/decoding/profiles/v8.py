"""v8 profiles: the text protocol, firmware 8.x, port 51050.

Every v8 frame observed so far uses the same layout regardless of the
header's type field, so the two profiles list the same features.  They are
kept apart so that a difference, once one is captured, has a place to go.

Values v8 does not transmit -- pump flow rates above all -- are not listed
rather than invented, with one deliberate exception: the chlorine and
pH-minus flow rates are assumed at 60 ml/min so the consumption counters
have something to integrate.
"""

from __future__ import annotations

from ...aseko_data import AsekoDeviceType
from ..decoders import (
    ClPumpRunning,
    Configuration,
    DelayAfterDose,
    DelayAfterStartup,
    FiltrationPumpRunning,
    FlowrateChlor,
    FlowratePhMinus,
    Ph,
    PhMinusPumpRunning,
    PoolVolume,
    Redox,
    RequiredPh,
    RequiredRedox,
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
    FiltrationPumpRunning,
    PhMinusPumpRunning,
    ClPumpRunning,
    FlowratePhMinus,
    FlowrateChlor,
    RequiredPh,
    RequiredRedox,
    PoolVolume,
    DelayAfterStartup,
    DelayAfterDose,
)

NET = Profile(
    name="v8 NET",
    protocol=Protocol.V8,
    model=AsekoDeviceType.NET,
    features=_FEATURES,
    evidence={
        ClPumpRunning: "unconfirmed: outs[9] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running",
        Configuration: "derived: a probe is installed when its ains slot is not -500",
        DelayAfterDose: "confirmed: areqs[18] = 2 min vs the app",
        DelayAfterStartup: "confirmed: areqs[17] = 2 min vs the app",
        FiltrationPumpRunning: "confirmed: outs[2] = 1 while the app showed 'Pump: ON / NONSTOP' (2026-04-13)",
        FlowrateChlor: "assumed: not transmitted, 60 ml/min taken for consumption",
        FlowratePhMinus: "assumed: not transmitted, 60 ml/min taken for consumption",
        Ph: "confirmed: ains[0] / 100 vs the app (6.49 vs 6.56, later reading), serial 110203680",
        PhMinusPumpRunning: "unconfirmed: outs[8] per the current decoder; net_v8_device_analysis.md lists outs[0] / outs[1] as candidates and no frame shows a pump running",
        PoolVolume: "confirmed: areqs[14] = 45 m3 vs the app",
        Redox: "confirmed: ains[6] = 809 mV vs 848 mV in the app (later reading), serial 110203680",
        RequiredPh: "confirmed: areqs[0] / 10 = 7.4 vs the app",
        RequiredRedox: "confirmed: areqs[1] * 10 = 740 mV vs the app",
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
    features=_FEATURES,
    evidence={
        ClPumpRunning: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        Configuration: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        DelayAfterDose: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        DelayAfterStartup: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        FiltrationPumpRunning: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        FlowrateChlor: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        FlowratePhMinus: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        Ph: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        PhMinusPumpRunning: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        PoolVolume: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        Redox: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        RequiredPh: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        RequiredRedox: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        SerialNumber: "confirmed: bytes 0-3, repeated in every segment header",
        Timestamp: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        WaterFlowToProbes: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
        WaterTemperature: "assumed: only the header type (105) says SALT; the NET layout is taken over unverified",
    },
)

BY_MODEL: dict[AsekoDeviceType, Profile] = {
    AsekoDeviceType.NET: NET,
    AsekoDeviceType.SALT: SALT,
}
