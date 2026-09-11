"""v7 profiles: the 120-byte binary protocol, firmware up to 7.x, port 47524.

One profile per model, two for HOME because its firmware revisions encode
byte[37] differently.  A feature listed here is one the model has; a
feature missing from a profile is one it does not have, and its field stays
None so no entity is created for it.  ``overrides`` name the reading to use
where this model's frame differs from the protocol default; everything else
uses the default reading from the feature's own file.

``evidence`` records why each entry is believed, in the words of the
captures and issues that established it.  "confirmed" means checked against
the unit's display or the Aseko Live app; "uncertain" and "assumed" mean the
earlier decoder read it that way and nothing has contradicted it yet.  The
support matrix in the docs is generated from these dictionaries.
"""

from __future__ import annotations

from ...aseko_data import AsekoDeviceType, AsekoFirmwareVariant, AsekoProfileFlag
from ..decoders import (
    AirTemperature,
    AlarmNoFlowToProbes,
    AlarmOrpTooManyDoses,
    AlarmPhTooManyDoses,
    AlarmRapidPhChange,
    AlgicidePumpRunning,
    AntifreezeEnabled,
    BackwashActive,
    BackwashDuration,
    BackwashEveryNDays,
    BackwashTime,
    ClFree,
    ClFreeMv,
    ClPumpRunning,
    Configuration,
    DelayAfterDose,
    DelayAfterStartup,
    ElectrolyzerActive,
    ElectrolyzerDirection,
    ElectrolyzerPower,
    FiltrationPumpRunning,
    FiltrationSchedule,
    FlocPumpRunning,
    FlowrateAlgicide,
    FlowrateChlor,
    FlowrateFloc,
    FlowrateOxy,
    FlowratePhMinus,
    HeatingActive,
    HeatingControlEnabled,
    MaxFillingTime,
    OxyPumpRunning,
    Ph,
    PhMinusConcentration,
    PhMinusPumpRunning,
    PoolVolume,
    Redox,
    RequiredAlgicide,
    RequiredClDose,
    RequiredClFree,
    RequiredFloc,
    RequiredOxyDose,
    RequiredPh,
    RequiredRedox,
    RequiredWaterTemperature,
    Salinity,
    SerialNumber,
    ServiceMenuOpen,
    Start1,
    Start2,
    Stop1,
    Stop2,
    Timestamp,
    VspPumpRunning,
    WaterFillingActive,
    WaterFlowToProbes,
    WaterLevel,
    WaterLevelFillingOff,
    WaterLevelFillingOn,
    WaterLevelHighAlarm,
    WaterLevelLowAlarm,
    WaterTemperature,
)
from ..frame import Protocol
from ..profile import Profile

# ---------------------------------------------------------------------------
# Feature groups shared between profiles.  A group is a convenience for
# reading the lists below, not a concept the decoder knows.
# ---------------------------------------------------------------------------

_IDENTITY = (SerialNumber, Configuration, Timestamp)
_MEASUREMENTS = (WaterTemperature, WaterFlowToProbes)
_CHLORINE_PROBES = (Ph, Redox, ClFree, ClFreeMv)
_SETTINGS = (
    RequiredPh,
    RequiredWaterTemperature,
    PoolVolume,
    DelayAfterStartup,
    DelayAfterDose,
    FlowratePhMinus,
)
_ALARMS = (
    AlarmPhTooManyDoses,
    AlarmOrpTooManyDoses,
    AlarmNoFlowToProbes,
    AlarmRapidPhChange,
)
_FILTRATION = (
    Start1,
    Stop1,
    Start2,
    Stop2,
    FiltrationSchedule,
    FiltrationPumpRunning,
)
_BACKWASH = (BackwashEveryNDays, BackwashTime, BackwashDuration, BackwashActive)
_WATER_LEVEL = (
    WaterLevel,
    WaterLevelLowAlarm,
    WaterLevelFillingOn,
    WaterLevelFillingOff,
    WaterLevelHighAlarm,
    WaterFillingActive,
)
_UNIT_STATE = (HeatingActive, VspPumpRunning, PhMinusConcentration)

# The disinfection setpoint family on chlorine units: byte[53] is one of
# these three depending on the installed probes, each answers only when it
# is the one that applies.
_DISINFECTION_SETPOINTS = (RequiredClFree, RequiredRedox, RequiredClDose)

# Algicide / flocculant on a single shared port, routed by byte[37] bit 0x80.
_SHARED_THIRD_PUMP = {
    RequiredAlgicide: "decode_v7_routed_by_byte37",
    RequiredFloc: "decode_v7_routed_by_byte37",
    FlowrateAlgicide: "decode_v7_routed_by_byte37",
    FlowrateFloc: "decode_v7_routed_by_byte37",
}

# Evidence that holds for every v7 model.
_COMMON_EVIDENCE = {
    SerialNumber: "confirmed: bytes 0-3, repeated in every segment header",
    Timestamp: "confirmed: bytes 6-11",
    WaterTemperature: "confirmed: bytes 25-26 / 10 on every model",
    WaterFlowToProbes: "confirmed: byte[28] == 0xAA",
    Ph: "confirmed: bytes 14-15 / 100 on every model",
    RequiredPh: "confirmed: byte[52] / 10 on every model",
    RequiredWaterTemperature: "unverified: byte[55], read as-is",
    PoolVolume: "confirmed: bytes 92-93",
    DelayAfterStartup: "confirmed: bytes 74-75",
    DelayAfterDose: "confirmed: bytes 106-107",
    FlowratePhMinus: "confirmed: byte[95] (Issue #110, #115)",
    AlarmNoFlowToProbes: "confirmed: byte[13] 0x04 (DomSchCoding, NET frame)",
    AlarmPhTooManyDoses: "confirmed on HOME: byte[12] 0x40 (Issue #134); byte[13] 0x02 inferred",
    AlarmOrpTooManyDoses: "confirmed on HOME: byte[12] 0x20 (Issue #134), byte[13] 0x01 (Issue #151)",
    AlarmRapidPhChange: "unconfirmed: byte[13] 0x08 from error_codes.md, no capture",
}

# ---------------------------------------------------------------------------
# SALT
# ---------------------------------------------------------------------------

SALT = Profile(
    name="v7 SALT",
    protocol=Protocol.V7,
    model=AsekoDeviceType.SALT,
    features=(
        *_IDENTITY,
        *_MEASUREMENTS,
        AirTemperature,
        *_CHLORINE_PROBES,
        Salinity,
        ElectrolyzerPower,
        ElectrolyzerActive,
        ElectrolyzerDirection,
        *_SETTINGS,
        *_DISINFECTION_SETPOINTS,
        RequiredAlgicide,
        RequiredFloc,
        FlowrateChlor,
        FlowrateAlgicide,
        FlowrateFloc,
        *_FILTRATION,
        ServiceMenuOpen,
        PhMinusPumpRunning,
        AlgicidePumpRunning,
        FlocPumpRunning,
        *_WATER_LEVEL,
        MaxFillingTime,
        *_UNIT_STATE,
        *_BACKWASH,
        *_ALARMS,
    ),
    overrides=_SHARED_THIRD_PUMP,
    flags=frozenset({AsekoProfileFlag.MENU_BIT_IS_PRESENCE_ONLY}),
    evidence={
        **_COMMON_EVIDENCE,
        Configuration: "confirmed: byte[4] missing-probe bits (0x0D CLF, 0x0E REDOX, 0x0F DOSE)",
        AirTemperature: "confirmed: serial 110194590, two dumps vs unit display (Issue #155)",
        Salinity: "confirmed: byte[20] / 10",
        ElectrolyzerActive: "confirmed: byte[29] 0x10, 25 frames (PR #87)",
        ElectrolyzerPower: "confirmed: byte[21] while 0x10 set (PR #87)",
        ElectrolyzerDirection: "confirmed: left, right and waiting all seen (own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer)",
        RequiredAlgicide: "confirmed: byte[54] via byte[37] 0x80 (@hopkins-tk, Issue #84)",
        RequiredFloc: "confirmed: byte[54] via byte[37] 0x80 clear",
        FlowrateAlgicide: "confirmed: byte[101] via byte[37] 0x80",
        FlowrateFloc: "confirmed: byte[101] via byte[37] 0x80 clear",
        FlowrateChlor: "unverified: byte[99]; 0xFF in every frame of the own SALT dumps, 37 frames 2026-08-08..28 (no chlorine pump on a SALT)",
        FiltrationSchedule: "confirmed: 0xC3 / 0xD3 / 0xF3, every transition both ways",
        ServiceMenuOpen: "confirmed: 0xD7 / 0xF7 then the unit goes offline",
        FiltrationPumpRunning: "confirmed: byte[29] 0x08 in every active phase (PR #87)",
        PhMinusPumpRunning: "unconfirmed: byte[29] 0x80; the bit was never set in the own SALT dumps, 37 frames 2026-08-08..28",
        AlgicidePumpRunning: "confirmed: byte[29] 0x20, 27 frames (PR #87)",
        FlocPumpRunning: "confirmed: byte[29] 0x20, Apr 3 frames",
        MaxFillingTime: "confirmed: bytes 76-77 vs Aseko Live (1800 s = 30 min)",
        BackwashActive: "confirmed: byte[29] 0x01, 2026-08-11 capture of a manual backwash",
        BackwashDuration: "confirmed: byte[71] * 10 matched the relay window",
        BackwashEveryNDays: "confirmed: byte[68] vs the unit's backwash settings (own SALT, the v1.8.0 backwash tracker classifies cycles against it)",
        BackwashTime: "confirmed: bytes 69-70 vs the unit's backwash settings (own SALT, v1.8.0 backwash tracker)",
        HeatingActive: "assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2; never set in the own SALT dumps, 37 frames 2026-08-08..28",
        VspPumpRunning: "confirmed: byte[22] toggles 0x10 / 0x18 across the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        PhMinusConcentration: "confirmed: byte[112] = 14 then 15 % in the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        WaterLevel: "confirmed: byte[27] 14..25 cm across the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        WaterLevelLowAlarm: "confirmed: byte[102] = 5 and 31 cm on the two units of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer; thresholds ordered low < on < off < high",
        WaterLevelFillingOn: "confirmed: byte[103] = 10 and 33 cm on the two units of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        WaterLevelFillingOff: "confirmed: byte[104] = 25 and 35 cm on the two units of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        WaterLevelHighAlarm: "confirmed: byte[105] = 40 and 56..73 cm on the two units of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        WaterFillingActive: "assumed: byte[29] 0x02, confirmed on HOME only; never set in the own SALT dumps, 37 frames 2026-08-08..28",
        Redox: "confirmed: bytes 16-19 = 593..670 mV on the REDOX unit of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        RequiredRedox: "confirmed: byte[53] * 10 = 670 mV on the REDOX unit of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        ClFree: "confirmed: bytes 16-17 = 0.77 and 0.93 mg/l on the CLF unit (serial 110194590) of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        ClFreeMv: "confirmed: bytes 20-21 = 6656 and 6934 mV on the CLF unit of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        RequiredClFree: "confirmed: byte[53] / 10 = 0.9 mg/l on the CLF unit of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        RequiredClDose: "unverified: byte[53] for a DOSE unit; neither unit of the own SALT dumps, 37 frames 2026-08-08..28 is one",
        RequiredWaterTemperature: "confirmed: byte[55] = 25 C in every frame of the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        Start1: "confirmed: bytes 56-57 changed 08:00 -> 09:00 with the timer settings during the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        Stop1: "confirmed: bytes 58-59 changed 18:05 / 19:00 / 21:35 with the timer settings during the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        Start2: "confirmed: bytes 60-61 changed 18:00 -> 18:10 with the timer settings during the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        Stop2: "confirmed: bytes 62-63 changed 22:00 -> 23:55 with the timer settings during the own SALT dumps, 37 frames 2026-08-08..28, checked against the unit by the maintainer",
        AlarmRapidPhChange: "unconfirmed: byte[13] 0x08 from error_codes.md; never set in the own SALT dumps, 37 frames 2026-08-08..28",
    },
)

# ---------------------------------------------------------------------------
# HOME, two firmware revisions
# ---------------------------------------------------------------------------

_HOME_FEATURES = (
    *_IDENTITY,
    *_MEASUREMENTS,
    *_CHLORINE_PROBES,
    *_SETTINGS,
    *_DISINFECTION_SETPOINTS,
    RequiredAlgicide,
    RequiredFloc,
    FlowrateChlor,
    FlowrateAlgicide,
    FlowrateFloc,
    *_FILTRATION,
    ClPumpRunning,
    PhMinusPumpRunning,
    AlgicidePumpRunning,
    FlocPumpRunning,
    *_WATER_LEVEL,
    MaxFillingTime,
    *_UNIT_STATE,
    HeatingControlEnabled,
    AntifreezeEnabled,
    *_BACKWASH,
    *_ALARMS,
)

_HOME_EVIDENCE = {
    **_COMMON_EVIDENCE,
    Configuration: "confirmed: byte[4] exact sub-type, 0x02 CLF / 0x03 REDOX (Issue #110)",
    RequiredAlgicide: "confirmed: byte[72], serial 110128063 (2026-04-28)",
    RequiredFloc: "confirmed: byte[54], serial 110128063 (2026-04-28)",
    FlowrateChlor: "confirmed: byte[99], serials 110071590 / 110128063 (Issues #110, #115)",
    FlowrateAlgicide: "confirmed: byte[103], Issues #110, #115",
    FlowrateFloc: "confirmed: byte[101], Issues #110, #115",
    FiltrationPumpRunning: "uncertain: byte[29] 0x08 assumed from SALT / OXY",
    ClPumpRunning: "uncertain: byte[29] 0x40, port may be chlorine or OXY Pure",
    PhMinusPumpRunning: "uncertain: byte[29] 0x80 assumed",
    AlgicidePumpRunning: "uncertain: byte[29] 0x20 assumed",
    FlocPumpRunning: "uncertain: byte[29] 0x20 assumed",
    WaterLevel: "confirmed: byte[27] (domin211, Issue #110)",
    WaterLevelLowAlarm: "confirmed: byte[102] (domin211, Issue #110)",
    WaterLevelFillingOn: "confirmed: byte[103] (domin211, DomSchCoding, Issue #110)",
    WaterLevelFillingOff: "confirmed: byte[104] (domin211, DomSchCoding, Issue #110)",
    WaterLevelHighAlarm: "confirmed: byte[105] (domin211, Issue #110)",
    WaterFillingActive: "confirmed: byte[29] 0x02 (DomSchCoding #100)",
    MaxFillingTime: "assumed: bytes 76-77, confirmed on SALT",
    VspPumpRunning: "confirmed: byte[22] 0x08, serial 110175608",
    PhMinusConcentration: "confirmed: byte[112], serial 110175608 (Issue #139)",
    HeatingActive: "assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2",
    BackwashActive: "assumed: byte[29] 0x01, confirmed on SALT",
    BackwashEveryNDays: "unverified: byte[68]",
    BackwashTime: "unverified: bytes 69-70",
    BackwashDuration: "unverified: byte[71] * 10",
}

HOME_A = Profile(
    name="v7 HOME firmware A",
    protocol=Protocol.V7,
    model=AsekoDeviceType.HOME,
    firmware=AsekoFirmwareVariant.HOME_A,
    features=_HOME_FEATURES,
    overrides={
        Configuration: "decode_v7_by_unit_type_byte",
        FiltrationSchedule: "decode_v7_home_a",
    },
    evidence={
        **_HOME_EVIDENCE,
        FiltrationSchedule: "confirmed: 0x43 nonstop / 0x53 timer, serial 110128063; fallback for 0x41 / 0x45 / 0x49 (Issue #135)",
        HeatingControlEnabled: "confirmed: byte[37] 0x08, serial 110175608 (Issue #135)",
        AntifreezeEnabled: "confirmed: byte[37] 0x80, serial 110175608 (Issue #136)",
    },
)

HOME_B = Profile(
    name="v7 HOME firmware B",
    protocol=Protocol.V7,
    model=AsekoDeviceType.HOME,
    firmware=AsekoFirmwareVariant.HOME_B,
    features=(*_HOME_FEATURES, ServiceMenuOpen),
    overrides={
        Configuration: "decode_v7_by_unit_type_byte",
        FiltrationPumpRunning: "decode_v7_menu_override",
    },
    evidence={
        **_HOME_EVIDENCE,
        FiltrationSchedule: "confirmed: 0x01 / 0x11 / 0x31, serial 110169464 (Issue #133)",
        ServiceMenuOpen: "confirmed: byte[37] 0x04 as a standing pump override (Issue #133)",
        FiltrationPumpRunning: "confirmed: byte[29] 0x08 stays set under the override, so 0x04 wins (Issue #133)",
        HeatingControlEnabled: "unverified: byte[37] 0x08 read as on firmware A, no capture on B",
        AntifreezeEnabled: "unverified: byte[37] 0x80 read as on firmware A, no capture on B",
    },
)

# A HOME frame with byte[37] unset says nothing about its firmware.  Read
# what both revisions share and nothing that only one of them has, so that no
# entity is created on the strength of a guess: service_menu_open exists only
# on firmware B and is left out.  Every byte[37] reading returns "unknown"
# on such a frame anyway, so the values cannot differ from either revision.
HOME_UNKNOWN_FIRMWARE = Profile(
    name="v7 HOME firmware not yet known",
    protocol=Protocol.V7,
    model=AsekoDeviceType.HOME,
    features=_HOME_FEATURES,
    overrides={Configuration: "decode_v7_by_unit_type_byte"},
    evidence={
        **_HOME_EVIDENCE,
        FiltrationSchedule: "n/a: byte[37] is unset on every frame decoded with this profile",
        HeatingControlEnabled: "n/a: byte[37] is unset on every frame decoded with this profile",
        AntifreezeEnabled: "n/a: byte[37] is unset on every frame decoded with this profile",
    },
)

# ---------------------------------------------------------------------------
# OXY (ASIN AQUA Oxygen)
# ---------------------------------------------------------------------------

OXY = Profile(
    name="v7 OXY",
    protocol=Protocol.V7,
    model=AsekoDeviceType.OXY,
    features=(
        *_IDENTITY,
        *_MEASUREMENTS,
        Ph,
        *_SETTINGS,
        RequiredOxyDose,
        RequiredFloc,
        RequiredAlgicide,
        FlowrateOxy,
        FlowrateFloc,
        FlowrateAlgicide,
        *_FILTRATION,
        ServiceMenuOpen,
        PhMinusPumpRunning,
        AlgicidePumpRunning,
        FlocPumpRunning,
        OxyPumpRunning,
        *_WATER_LEVEL,
        MaxFillingTime,
        *_UNIT_STATE,
        *_BACKWASH,
        *_ALARMS,
    ),
    overrides={
        Configuration: "decode_v7_ph_and_oxy",
        AlgicidePumpRunning: "decode_v7_oxy",
    },
    evidence={
        **_COMMON_EVIDENCE,
        Configuration: "confirmed: fixed pH + OXY Pure, the SANOSIL probe sits in the CLF slot",
        RequiredOxyDose: "confirmed: byte[53] (Winnetoux, 2026-04-11)",
        RequiredFloc: "confirmed: byte[54] = 10 (2026-04-11)",
        RequiredAlgicide: "confirmed: byte[72] = 15 (2026-04-11)",
        FlowrateOxy: "confirmed: byte[99]",
        FlowrateFloc: "confirmed: byte[101]",
        FlowrateAlgicide: "confirmed: byte[103] = 60 ml/min (2026-04-11)",
        FiltrationPumpRunning: "confirmed: byte[29] 0x08 in every captured frame",
        PhMinusPumpRunning: "confirmed: byte[29] 0x80, 2026-04-12 Winnetoux log",
        AlgicidePumpRunning: "confirmed: byte[29] 0x10, 2026-04-11 Winnetoux log",
        FlocPumpRunning: "confirmed: byte[29] 0x20 toggles at the 19:33:52 floc event",
        OxyPumpRunning: "confirmed: byte[29] 0x40, 2026-04-11 Winnetoux log",
        FiltrationSchedule: "assumed: bit flags as on SALT, no OXY capture of a transition",
        ServiceMenuOpen: "assumed: byte[37] 0x04 as on SALT",
        MaxFillingTime: "assumed: bytes 76-77, confirmed on SALT",
        WaterLevel: "assumed: byte[27], confirmed on HOME",
        WaterFillingActive: "assumed: byte[29] 0x02, confirmed on HOME",
        HeatingActive: "assumed: byte[29] 0x04 per JS-DE-Tech relay_byte bit 2",
        VspPumpRunning: "assumed: byte[22] 0x08, confirmed on HOME",
        PhMinusConcentration: "assumed: byte[112], confirmed on HOME",
        BackwashActive: "assumed: byte[29] 0x01, confirmed on SALT",
    },
)

# ---------------------------------------------------------------------------
# NET (Aqua NET): measurement and dosing only, no filter, no valve
# ---------------------------------------------------------------------------

NET = Profile(
    name="v7 NET",
    protocol=Protocol.V7,
    model=AsekoDeviceType.NET,
    features=(
        *_IDENTITY,
        *_MEASUREMENTS,
        *_CHLORINE_PROBES,
        *_SETTINGS,
        *_DISINFECTION_SETPOINTS,
        RequiredAlgicide,
        RequiredFloc,
        FlowrateChlor,
        FlowrateAlgicide,
        FlowrateFloc,
        ClPumpRunning,
        PhMinusPumpRunning,
        *_ALARMS,
    ),
    overrides={
        **_SHARED_THIRD_PUMP,
        ClPumpRunning: "decode_v7_net",
        PhMinusPumpRunning: "decode_v7_net",
    },
    evidence={
        **_COMMON_EVIDENCE,
        Configuration: "confirmed: byte[4] missing-probe bits (0x09 CLF, 0x0A REDOX, 0x0B DOSE)",
        ClFree: "confirmed: bytes 16-17 / 100",
        ClFreeMv: "confirmed: bytes 20-21",
        ClPumpRunning: "confirmed: byte[29] 0x02 (Issue #66)",
        PhMinusPumpRunning: "confirmed: byte[29] 0x01 (Issue #66)",
        FlowrateChlor: "unverified: byte[99]",
        FlowrateAlgicide: "unverified: byte[101] via byte[37] 0x80, as on SALT",
        FlowrateFloc: "unverified: byte[101] via byte[37] 0x80 clear, as on SALT",
        RequiredAlgicide: "unverified: byte[54] via byte[37] 0x80, as on SALT",
        RequiredFloc: "unverified: byte[54] via byte[37] 0x80 clear, as on SALT",
    },
)

# ---------------------------------------------------------------------------
# PROFI: unit type 0x10, unconfirmed
# ---------------------------------------------------------------------------

PROFI = Profile(
    name="v7 PROFI",
    protocol=Protocol.V7,
    model=AsekoDeviceType.PROFI,
    features=(
        *_IDENTITY,
        *_MEASUREMENTS,
        *_CHLORINE_PROBES,
        *_SETTINGS,
        RequiredClFree,
        RequiredClDose,
        FlowrateChlor,
        FlowrateAlgicide,
        FlowrateFloc,
        *_FILTRATION,
        ServiceMenuOpen,
        ClPumpRunning,
        PhMinusPumpRunning,
        FlocPumpRunning,
        *_WATER_LEVEL,
        *_UNIT_STATE,
        *_BACKWASH,
        *_ALARMS,
    ),
    overrides={
        Configuration: "decode_v7_without_dose",
        FlowrateAlgicide: "decode_v7_routed_by_byte37",
        FlowrateFloc: "decode_v7_routed_by_byte37",
    },
    evidence={
        **_COMMON_EVIDENCE,
        Configuration: "uncertain: unit type 0x10 itself is unconfirmed; no DOSE bit",
        Redox: "uncertain: bytes 18-19",
        FiltrationPumpRunning: "uncertain: byte[29] 0x08 assumed",
        ClPumpRunning: "uncertain: byte[29] 0x40 assumed",
        PhMinusPumpRunning: "uncertain: byte[29] 0x80 assumed",
        FlocPumpRunning: "uncertain: byte[29] 0x20 assumed",
        FlowrateAlgicide: "unverified: byte[101] via byte[37] 0x80, as on SALT",
        FlowrateFloc: "unverified: byte[101] via byte[37] 0x80 clear, as on SALT",
    },
)

# ---------------------------------------------------------------------------
# A unit type nobody has mapped.  Read everything that has a generic v7
# reading -- every probe, the shared-port layout most models use, the
# default actuator bits -- so that the diagnostics of such a unit show as
# much as the frame can be made to say.  Nothing here is verified for the
# unit at hand: the coordinator keeps it out of the entity platforms and
# reports it separately in diagnostics as unrecognised.
#
# Left out are readings whose bytes mean something else on other models and
# so cannot be called generic: SALT's electrolyser and salinity (bytes 20-21
# are cl_free_mv elsewhere), the OXY dose and pump (byte[53] and bit 0x40
# are chlorine elsewhere), HOME's heating / antifreeze enables (byte[37] 0x80
# is the algicide routing elsewhere) and the air temperature, verified on
# SALT only.
# ---------------------------------------------------------------------------

_UNKNOWN_FEATURES = (
    *_IDENTITY,
    *_MEASUREMENTS,
    *_CHLORINE_PROBES,
    *_SETTINGS,
    *_DISINFECTION_SETPOINTS,
    RequiredAlgicide,
    RequiredFloc,
    FlowrateChlor,
    FlowrateAlgicide,
    FlowrateFloc,
    *_FILTRATION,
    ServiceMenuOpen,
    ClPumpRunning,
    PhMinusPumpRunning,
    AlgicidePumpRunning,
    FlocPumpRunning,
    *_WATER_LEVEL,
    MaxFillingTime,
    *_UNIT_STATE,
    *_BACKWASH,
    *_ALARMS,
)

UNKNOWN = Profile(
    name="v7 unknown unit type",
    protocol=Protocol.V7,
    model=None,
    features=_UNKNOWN_FEATURES,
    overrides={
        Configuration: "decode_v7_all_probes",
        **_SHARED_THIRD_PUMP,
    },
    evidence={
        feature: "unverified: unmapped unit type, read with the generic v7 reading"
        for feature in _UNKNOWN_FEATURES
    },
)

BY_MODEL: dict[AsekoDeviceType | None, Profile] = {
    AsekoDeviceType.SALT: SALT,
    AsekoDeviceType.OXY: OXY,
    AsekoDeviceType.NET: NET,
    AsekoDeviceType.PROFI: PROFI,
    None: UNKNOWN,
}
