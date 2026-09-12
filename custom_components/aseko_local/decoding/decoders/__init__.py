"""One decoder file per field on ``AsekoDevice``.

``ALL_FEATURES`` lists every feature the integration knows, whether or not
any profile currently uses it.  Profiles import the classes they list from
here; the support-matrix generator walks this list to report what each
profile does and does not read.
"""

from __future__ import annotations

from ..feature import Feature
from .air_temperature import AirTemperature
from .alarm_no_flow_to_probes import AlarmNoFlowToProbes
from .alarm_orp_too_many_doses import AlarmOrpTooManyDoses
from .alarm_ph_too_many_doses import AlarmPhTooManyDoses
from .alarm_rapid_ph_change import AlarmRapidPhChange
from .algicide_pump_running import AlgicidePumpRunning
from .antifreeze_enabled import AntifreezeEnabled
from .backwash_active import BackwashActive
from .backwash_duration import BackwashDuration
from .backwash_every_n_days import BackwashEveryNDays
from .backwash_time import BackwashTime
from .cl_free import ClFree
from .cl_free_mv import ClFreeMv
from .cl_pump_running import ClPumpRunning
from .configuration import Configuration
from .delay_after_dose import DelayAfterDose
from .delay_after_startup import DelayAfterStartup
from .electrolyzer_active import ElectrolyzerActive
from .electrolyzer_direction import ElectrolyzerDirection
from .electrolyzer_power import ElectrolyzerPower
from .filtration_pump_running import FiltrationPumpRunning
from .filtration_schedule import FiltrationSchedule
from .filtration_start1 import FiltrationStart1
from .filtration_start2 import FiltrationStart2
from .filtration_stop1 import FiltrationStop1
from .filtration_stop2 import FiltrationStop2
from .floc_pump_running import FlocPumpRunning
from .flowrate_algicide import FlowrateAlgicide
from .flowrate_chlor import FlowrateChlor
from .flowrate_floc import FlowrateFloc
from .flowrate_oxy import FlowrateOxy
from .flowrate_ph_minus import FlowratePhMinus
from .flowrate_ph_plus import FlowratePhPlus
from .heating_active import HeatingActive
from .heating_control_enabled import HeatingControlEnabled
from .max_filling_time import MaxFillingTime
from .max_ph_doses import MaxPhDoses
from .oxy_pump_running import OxyPumpRunning
from .ph import Ph
from .ph_minus_concentration import PhMinusConcentration
from .ph_minus_pump_running import PhMinusPumpRunning
from .ph_plus_pump_running import PhPlusPumpRunning
from .pool_volume import PoolVolume
from .redox import Redox
from .required_algicide import RequiredAlgicide
from .required_cl_dose import RequiredClDose
from .required_cl_free import RequiredClFree
from .required_floc import RequiredFloc
from .required_oxy_dose import RequiredOxyDose
from .required_ph import RequiredPh
from .required_redox import RequiredRedox
from .required_water_temperature import RequiredWaterTemperature
from .salinity import Salinity
from .serial_number import SerialNumber
from .service_menu_open import ServiceMenuOpen
from .timestamp import Timestamp
from .vsp_pump_running import VspPumpRunning
from .water_filling_active import WaterFillingActive
from .water_flow_to_probes import WaterFlowToProbes
from .water_level import WaterLevel
from .water_level_filling_off import WaterLevelFillingOff
from .water_level_filling_on import WaterLevelFillingOn
from .water_level_high_alarm import WaterLevelHighAlarm
from .water_level_low_alarm import WaterLevelLowAlarm
from .water_temperature import WaterTemperature

ALL_FEATURES: tuple[type[Feature], ...] = (
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
    FiltrationStart1,
    FiltrationStart2,
    FiltrationStop1,
    FiltrationStop2,
    FlocPumpRunning,
    FlowrateAlgicide,
    FlowrateChlor,
    FlowrateFloc,
    FlowrateOxy,
    FlowratePhMinus,
    FlowratePhPlus,
    HeatingActive,
    HeatingControlEnabled,
    MaxFillingTime,
    MaxPhDoses,
    OxyPumpRunning,
    Ph,
    PhMinusConcentration,
    PhMinusPumpRunning,
    PhPlusPumpRunning,
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

__all__ = [
    "ALL_FEATURES",
    "AirTemperature",
    "AlarmNoFlowToProbes",
    "AlarmOrpTooManyDoses",
    "AlarmPhTooManyDoses",
    "AlarmRapidPhChange",
    "AlgicidePumpRunning",
    "AntifreezeEnabled",
    "BackwashActive",
    "BackwashDuration",
    "BackwashEveryNDays",
    "BackwashTime",
    "ClFree",
    "ClFreeMv",
    "ClPumpRunning",
    "Configuration",
    "DelayAfterDose",
    "DelayAfterStartup",
    "ElectrolyzerActive",
    "ElectrolyzerDirection",
    "ElectrolyzerPower",
    "FiltrationPumpRunning",
    "FiltrationSchedule",
    "FiltrationStart1",
    "FiltrationStart2",
    "FiltrationStop1",
    "FiltrationStop2",
    "FlocPumpRunning",
    "FlowrateAlgicide",
    "FlowrateChlor",
    "FlowrateFloc",
    "FlowrateOxy",
    "FlowratePhMinus",
    "FlowratePhPlus",
    "HeatingActive",
    "HeatingControlEnabled",
    "MaxFillingTime",
    "MaxPhDoses",
    "OxyPumpRunning",
    "Ph",
    "PhMinusConcentration",
    "PhMinusPumpRunning",
    "PhPlusPumpRunning",
    "PoolVolume",
    "Redox",
    "RequiredAlgicide",
    "RequiredClDose",
    "RequiredClFree",
    "RequiredFloc",
    "RequiredOxyDose",
    "RequiredPh",
    "RequiredRedox",
    "RequiredWaterTemperature",
    "Salinity",
    "SerialNumber",
    "ServiceMenuOpen",
    "Timestamp",
    "VspPumpRunning",
    "WaterFillingActive",
    "WaterFlowToProbes",
    "WaterLevel",
    "WaterLevelFillingOff",
    "WaterLevelFillingOn",
    "WaterLevelHighAlarm",
    "WaterLevelLowAlarm",
    "WaterTemperature",
]
