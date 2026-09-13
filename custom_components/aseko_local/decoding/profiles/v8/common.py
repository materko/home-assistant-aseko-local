"""What every v8 profile shares: the header type table and the frame layout.

Every v8 frame observed so far uses the same layout regardless of the
header's type field, so the device modules take ``FEATURES`` as it is or
leave out what their model does not have.
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

#: Header field f2 -> model.  Unknown values fall back to NET with a warning.
MODEL_BY_HEADER_TYPE: dict[int, AsekoDeviceType] = {
    105: AsekoDeviceType.SALT,  # ASIN Aqua Salt NET
    804: AsekoDeviceType.NET,
    805: AsekoDeviceType.NET,
    812: AsekoDeviceType.NET,
}

FEATURES = (
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
