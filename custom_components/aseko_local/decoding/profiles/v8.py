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

_EVIDENCE = {
    SerialNumber: "confirmed: header token 2 on every captured frame",
    WaterTemperature: "confirmed: ins[0] on fekberg frames (Sep 2025, Apr 2026) vs app",
    Ph: "confirmed: ains[0] on fekberg frames vs app",
    Redox: "confirmed: ains[6] on fekberg frames vs app",
    FiltrationPumpRunning: "confirmed: outs[2]",
    PhMinusPumpRunning: "confirmed: outs[8]",
    ClPumpRunning: "confirmed: outs[9]",
    FlowratePhMinus: "assumed: not transmitted, 60 ml/min taken for consumption",
    FlowrateChlor: "assumed: not transmitted, 60 ml/min taken for consumption",
    RequiredPh: "confirmed: areqs[0] / 10",
    RequiredRedox: "confirmed: areqs[1] * 10",
    PoolVolume: "confirmed: areqs[14]",
    DelayAfterStartup: "confirmed: areqs[17]",
    DelayAfterDose: "confirmed: areqs[18]",
    Timestamp: "confirmed: ins[16] hour, ins[17] minute; date taken from HA",
    WaterFlowToProbes: "confirmed: ins[8]",
    Configuration: "derived: a probe is installed when its ains slot is not -500",
}

NET = Profile(
    name="v8 NET",
    protocol=Protocol.V8,
    model=AsekoDeviceType.NET,
    features=_FEATURES,
    evidence=_EVIDENCE,
)

SALT = Profile(
    name="v8 SALT",
    protocol=Protocol.V8,
    model=AsekoDeviceType.SALT,
    features=_FEATURES,
    evidence={
        **_EVIDENCE,
        Configuration: "assumed: same layout as NET; header type 105 only tells the model",
    },
)

BY_MODEL: dict[AsekoDeviceType, Profile] = {
    AsekoDeviceType.NET: NET,
    AsekoDeviceType.SALT: SALT,
}
