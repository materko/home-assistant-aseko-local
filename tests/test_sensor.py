from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er

from custom_components.aseko_local.binary_sensor import (
    BINARY_SENSORS,
    AsekoLocalBinarySensorEntity,
    async_remove_retired_entities,
)
from custom_components.aseko_local.binary_sensor import (
    async_setup_entry as binary_async_setup_entry,
)
from custom_components.aseko_local.const import (
    DOMAIN,
    UNIT_TYPE_PROFI,
    WATER_FLOW_TO_PROBES,
)
from custom_components.aseko_local.decoding import decode
from custom_components.aseko_local.models import AsekoDeviceType
from custom_components.aseko_local.sensor import (
    RETIRED_UNIQUE_ID_SUFFIXES as RETIRED_SENSOR_IDS,
)
from custom_components.aseko_local.sensor import (
    SENSORS,
    AsekoConsumptionSensorEntity,
    AsekoLocalSensorEntity,
    async_migrate_unique_ids,
    async_setup_entry,
)


# Helper function to create a base bytearray for a device
def _make_salt_redox_bytes() -> bytearray:
    """Create a base bytearray with almost all possible entities."""

    data = bytearray([0xFF] * 120)
    data[0:4] = (1234).to_bytes(4, "big")  # serial_number
    data[4] = 0x0E  # SALT with REDOX probe
    data[6] = 24  # year (2024)
    data[7] = 6  # month
    data[8] = 15  # day
    data[9] = 12  # hour
    data[10] = 34  # minute
    data[11] = 56  # second
    data[14:16] = (700).to_bytes(2, "big")  # pH = 7.00
    data[16:18] = (680).to_bytes(2, "big")  # Redox = 650 mv
    data[20] = 32  # salinity = 3.2
    data[21] = 80  # chlorine_production
    data[25:27] = (245).to_bytes(2, "big")  # water_temperature = 24.5
    data[28] = WATER_FLOW_TO_PROBES
    data[29] = 0x10  # Electrolyzer on
    data[37] = 0xB3  # algicide mode (bit 7 set; confirmed by @hopkins-tk)
    data[52] = 70  # ph_target = 7.0
    data[53] = 65  # redox_target = 650
    data[54] = 5  # algaecide_dose_target
    data[55] = 28  # water_temperature_target
    data[56] = 8  # filtration_period_1_start hour
    data[57] = 0  # filtration_period_1_start min
    data[58] = 10  # filtration_period_1_end hour
    data[59] = 0  # filtration_period_1_end min
    data[60] = 14  # filtration_period_2_start hour
    data[61] = 0  # filtration_period_2_start min
    data[62] = 16  # filtration_period_2_end hour
    data[63] = 0  # filtration_period_2_end min
    data[68] = 3  # backwash_interval
    data[69] = 2  # backwash_start_time hour
    data[70] = 30  # backwash_start_time min
    data[71] = 2  # backwash_duration (20)
    data[74:76] = (120).to_bytes(2, "big")  # startup_delay
    data[92:94] = (5000).to_bytes(2, "big")  # pool_volume
    data[76:78] = (3600).to_bytes(2, "big")  # max_refill_time, raw 3600
    data[94:96] = (60).to_bytes(2, "big")  # byte 95 = ph_minus_flow_rate = 60
    data[97] = 255  # ph_plus_flow_rate: 0xFF = not present
    data[99] = 255  # chlorine_flow_rate: 0xFF = SALT has no chlorine pump
    data[101] = 255  # flocculant_flow_rate: 0xFF = SALT has no flocculant pump
    data[106:108] = (30).to_bytes(2, "big")  # dosing_delay
    return data


def _make_salt_clf_bytes() -> bytearray:
    """Create a base bytearray with almost all possible entities."""

    data = bytearray([0xFF] * 120)
    data[0:4] = (1234).to_bytes(4, "big")  # serial_number
    data[4] = 0x0D  # SALT with CLF probe
    data[6] = 24  # year (2024)
    data[7] = 6  # month
    data[8] = 15  # day
    data[9] = 12  # hour
    data[10] = 34  # minute
    data[11] = 56  # second
    data[14:16] = (700).to_bytes(2, "big")  # pH = 7.00
    data[16:18] = (100).to_bytes(2, "big")  # CL free = 1.00 mg/L
    data[20] = 32  # salinity = 3.2
    data[21] = 80  # chlorine_production
    data[25:27] = (245).to_bytes(2, "big")  # water_temperature = 24.5
    data[28] = WATER_FLOW_TO_PROBES
    data[29] = 0x50  # filtration_running + Electrolyzer LEFT
    data[37] = 0xB3  # algicide mode (bit 7 set; confirmed by @hopkins-tk)
    data[52] = 70  # ph_target = 7.0
    data[53] = 30  # required_cl = 3.0
    data[54] = 5  # algaecide_dose_target
    data[55] = 28  # water_temperature_target
    data[56] = 8  # filtration_period_1_start hour
    data[57] = 0  # filtration_period_1_start min
    data[58] = 10  # filtration_period_1_end hour
    data[59] = 0  # filtration_period_1_end min
    data[60] = 14  # filtration_period_2_start hour
    data[61] = 0  # filtration_period_2_start min
    data[62] = 16  # filtration_period_2_end hour
    data[63] = 0  # filtration_period_2_end min
    data[68] = 3  # backwash_interval
    data[69] = 2  # backwash_start_time hour
    data[70] = 30  # backwash_start_time min
    data[71] = 2  # backwash_duration (20)
    data[74:76] = (120).to_bytes(2, "big")  # startup_delay
    data[92:94] = (5000).to_bytes(2, "big")  # pool_volume
    data[76:78] = (3600).to_bytes(2, "big")  # max_refill_time, raw 3600
    data[94:96] = (60).to_bytes(2, "big")  # byte 95 = ph_minus_flow_rate = 60
    data[97] = 20  # ph_plus_flow_rate
    data[99] = 255  # chlorine_flow_rate: 0xFF = SALT has no chlorine pump
    data[101] = 255  # flocculant_flow_rate: 0xFF = SALT has no flocculant pump
    data[106:108] = (30).to_bytes(2, "big")  # dosing_delay
    return data


def _make_net_clf_bytes() -> bytearray:
    """Create a base bytearray for test data with default values for Aseko NET with CLF and PH."""
    """with CL free and cl free mV and PH no redox"""

    data = bytearray([0xFF] * 120)
    data[0:4] = (110200612).to_bytes(4, "big")  # serial_number / HEX: 0x06918724
    data[4] = 9  # probe info / HEX: 0x09
    data[6] = 255  # year / HEX: 0xff
    data[7] = 255  # month / HEX: 0xff
    data[8] = 255  # day / HEX: 0xff
    data[9] = 255  # hour / HEX: 0xff
    data[10] = 255  # minute / HEX: 0xff
    data[11] = 255  # second / HEX: 0xff
    data[14:16] = (721).to_bytes(2, "big")  # ph_value / HEX: 0x02d1
    data[16:18] = (36).to_bytes(2, "big")  # free_chlorine or redox / HEX: 0x0024
    data[18:20] = (65535).to_bytes(2, "big")  # redox / HEX: 0xffff
    data[20] = 0  # salinity / HEX: 0x00
    data[21] = 38  # chlorine_production / HEX: 0x26
    data[20:22] = (38).to_bytes(2, "big")  # free_chlorine_mv / HEX: 0x0026
    data[25:27] = (327).to_bytes(2, "big")  # water_temperature / HEX: 0x0147
    data[28] = 0  # water_flow_probe / HEX: 0x00
    data[29] = 0  # pump_or_electrolizer / HEX: 0x00
    data[52] = 71  # ph_target / HEX: 0x47
    data[53] = 10  # required_cl_free_or_redox / HEX: 0x0a
    data[54] = 8  # algaecide_dose_target / HEX: 0x08
    data[55] = 255  # water_temperature_target / HEX: 0xff
    data[56:58] = (65535).to_bytes(2, "big")  # start_1_time / HEX: 0xffff
    data[58:60] = (65535).to_bytes(2, "big")  # stop_1_time / HEX: 0xffff
    data[60:62] = (65535).to_bytes(2, "big")  # start_2_time / HEX: 0xffff
    data[62:64] = (65535).to_bytes(2, "big")  # stop_2_time / HEX: 0xffff
    data[68] = 255  # backwash_interval / HEX: 0xff
    data[69:71] = (65535).to_bytes(2, "big")  # backwash_start_time / HEX: 0xffff
    data[71] = 255  # backwash_duration / HEX: 0xff
    data[74:76] = (65535).to_bytes(2, "big")  # startup_delay / HEX: 0xffff
    data[92:94] = (1).to_bytes(2, "big")  # pool_volume / HEX: 0x0001
    data[76:78] = (3600).to_bytes(2, "big")  # max_refill_time, raw 3600
    data[94:96] = (60).to_bytes(2, "big")  # byte 95 = flowrate / HEX: 0x003c
    data[95] = 60  # chlorine_flow_rate / HEX: 0x3c
    data[97] = 255  # ph_plus_flow_rate / HEX: 0xff
    data[99] = 60  # ph_minus_flow_rate / HEX: 0x3c
    data[101] = 255  # flocculant_flow_rate / HEX: 0xff
    data[106:108] = (120).to_bytes(2, "big")  # dosing_delay / HEX: 0x0078
    return data


def _make_profi_clf_redox_bytes() -> bytearray:
    """Create a base bytearray for Aseko Profi with CL and REDOX probe."""

    data = bytearray([0xFF] * 120)
    data[0:4] = (1234).to_bytes(4, "big")  # serial_number
    data[4] = UNIT_TYPE_PROFI  # PROFI with CL and REDOX probe
    data[6] = 24  # year (2024)
    data[7] = 6  # month
    data[8] = 15  # day
    data[9] = 12  # hour
    data[10] = 34  # minute
    data[11] = 56  # second
    data[14:16] = (800).to_bytes(2, "big")  # pH = 7.00
    data[16:18] = (100).to_bytes(2, "big")  # Redox
    data[18:20] = (650).to_bytes(2, "big")  # Redox = 650 mv if Byte 18 and 19
    # are not UNSPECIFIED
    data[25:27] = (245).to_bytes(2, "big")  # water_temperature = 24.5
    data[28] = WATER_FLOW_TO_PROBES
    data[29] = 0x08  # filtration_running
    data[37] = 0x00  # flocculant mode (PROFI uses flocculant, not algicide)
    data[52] = 70  # ph_target = 7.0
    data[53] = 30  # required_cl = 3.0
    data[54] = (
        5  # required dosing rate (byte 54; flocculant mode → flocculant_dose_target)
    )
    data[55] = 28  # water_temperature_target
    data[56] = 8  # filtration_period_1_start hour
    data[57] = 0  # filtration_period_1_start min
    data[58] = 10  # filtration_period_1_end hour
    data[59] = 0  # filtration_period_1_end min
    data[60] = 14  # filtration_period_2_start hour
    data[61] = 0  # filtration_period_2_start min
    data[62] = 16  # filtration_period_2_end hour
    data[63] = 0  # filtration_period_2_end min
    data[68] = 3  # backwash_interval
    data[69] = 2  # backwash_start_time hour
    data[70] = 30  # backwash_start_time min
    data[71] = 2  # backwash_duration (20)
    data[74:76] = (120).to_bytes(2, "big")  # startup_delay
    data[92:94] = (5000).to_bytes(2, "big")  # pool_volume
    data[95] = 10  # chlorine_flow_rate
    data[76:78] = (3600).to_bytes(2, "big")  # max_refill_time, raw 3600
    data[94:96] = (60).to_bytes(2, "big")  # byte 95 = ph_minus_flow_rate
    data[97] = 20  # ph_plus_flow_rate
    data[99] = 255  # ph_minus_flow_rate (not measured)
    data[101] = 60  # flocculant_flow_rate (PROFI has flocculant pump configured)
    data[106:108] = (30).to_bytes(2, "big")  # dosing_delay
    return data


@pytest.mark.asyncio
async def test_async_setup_salt_redox(hass) -> None:
    """Test that async_setup_entry adds sensor entities for available sensors."""

    # Use the decoder to create a valid device
    raw_bytes = _make_salt_redox_bytes()
    device = decode(raw_bytes)

    class DummyCoordinator:
        def get_devices(self):
            return [device]

        def get_tracker(self, serial_number):
            return None

        def async_add_new_device_listener(self, listener):
            return lambda: None

        def async_add_new_features_listener(self, listener):
            return lambda: None

    # Create a MagicMock for ConfigEntry with runtime_data attribute
    dummy_entry = MagicMock(spec=ConfigEntry)
    # entry_id is an instance attribute, so spec= does not provide it, but
    # async_setup_entry needs it for the unique_id migration pass.
    dummy_entry.entry_id = "test_entry_id"
    dummy_entry.runtime_data = type(
        "RuntimeData", (), {"coordinator": DummyCoordinator()}
    )

    added_entities = []

    # Correct callback signature for async_add_entities
    def mock_add_entities(
        new_entities, update_before_add=False, *, config_subentry_id=None
    ):
        # Only what the unit has shown: every other quantity the model can
        # have gets an entity too, created disabled (entity.py).
        added_entities.extend(
            e for e in new_entities if e.entity_registry_enabled_default
        )

    await async_setup_entry(hass, dummy_entry, mock_add_entities)
    await binary_async_setup_entry(hass, dummy_entry, mock_add_entities)

    print(device.device_type)

    for entity in added_entities:
        name = getattr(entity.entity_description, "key", "unknown")
        value = (
            entity.is_on
            if isinstance(entity, AsekoLocalBinarySensorEntity)
            else entity.native_value
        )
        status = "enabled" if getattr(entity, "enabled", True) else "disabled"
        print(f"Sensor: {name}, Status: {status}, Value: {value}")

    assert device.device_type == AsekoDeviceType.SALT
    assert any(isinstance(e, AsekoLocalSensorEntity) for e in added_entities)
    assert any(isinstance(e, AsekoLocalBinarySensorEntity) for e in added_entities)
    assert any(
        getattr(e.device, "serial_number", None) == device.serial_number
        for e in added_entities
    )
    # 11 sensors + 7 new (filtration schedule, pool volume, delays) + 4 binary
    # water_flow, electrolysis_running, filtration and ph_minus
    # + 2 consumption (ph_minus canister + total) + 1 connection_status
    # + 3 new backwash config sensors (every_n_days, time, duration)
    # + 3 backwash history sensors (last_backwash, last_manual_backwash,
    #   next_scheduled_backwash) — created for every device with a backwash
    #   valve even though they read "unknown" until a cycle is seen.
    #   last_scheduled_backwash is a datetime entity, not a sensor, so it is
    #   not in this platform's count.
    # + 1 new backwash_running binary sensor
    # + 1 new heating_running binary sensor
    # + 1 last_manual_backwash sensor; last_scheduled_backwash is a datetime
    #   entity, counted by that platform rather than here
    # byte[37] reshuffle, net zero:
    #   -1 filtration_nonstop24 binary sensor (the schedule sensor covers it)
    #   -1 filtration_mode sensor (it conflated the schedule with bit 0x04)
    #   +1 filtration_schedule sensor  — what the unit runs unattended
    #   +1 service_menu binary sensor  — bit 0x04, a device state, not a
    #      filtration one
    # + 1 last_seen: present on every unit, so it is created up front and
    #   reads "unknown" until the coordinator stamps the first frame.  It used
    #   to be skipped here only because this test hands the platform a device
    #   the coordinator has not stamped yet.
    # + 2 heating_control_enabled / freeze_protection_enabled binary sensors: the
    #   SALT Configuration menu has Heating control and Winter mode, but
    #   their place in the frame is not known yet, so they read unknown
    # + 2 clock_offset sensor / clock_out_of_sync binary sensor: the unit sends
    #   its clock (bytes 6-11)
    assert len(added_entities) == 48
    # Nothing has been observed yet, so the history is unknown rather than
    # guessed from the schedule.
    backwash_history = {
        e.entity_description.key: e.native_value
        for e in added_entities
        if getattr(e.entity_description, "key", None)
        in {
            "last_backwash",
            "last_manual_backwash",
            "next_scheduled_backwash",
        }
    }
    assert len(backwash_history) == 3
    assert all(value is None for value in backwash_history.values())
    assert any(
        getattr(e.entity_description, "key", None) != "water_flow_to_probes"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "electrolyzer_active"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "pump_running"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "free_chlorine_mv"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "required_free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "rx" for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "required_rx"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "required_algicide"
        for e in added_entities
    )
    assert any(isinstance(e, AsekoConsumptionSensorEntity) for e in added_entities)


@pytest.mark.asyncio
async def test_async_setup_salt_clf(hass) -> None:
    """Test that async_setup_entry adds sensor entities for available sensors."""

    # Use the decoder to create a valid device
    raw_bytes = _make_salt_clf_bytes()
    device = decode(raw_bytes)

    class DummyCoordinator:
        def get_devices(self):
            return [device]

        def get_tracker(self, serial_number):
            return None

        def last_update_success(self):
            return True

        def async_add_new_device_listener(self, listener):
            return lambda: None

        def async_add_new_features_listener(self, listener):
            return lambda: None

    # Create a MagicMock for ConfigEntry with runtime_data attribute
    dummy_entry = MagicMock(spec=ConfigEntry)
    # entry_id is an instance attribute, so spec= does not provide it, but
    # async_setup_entry needs it for the unique_id migration pass.
    dummy_entry.entry_id = "test_entry_id"
    dummy_entry.runtime_data = type(
        "RuntimeData", (), {"coordinator": DummyCoordinator()}
    )

    added_entities = []

    # Correct callback signature for async_add_entities
    def mock_add_entities(
        new_entities, update_before_add=False, *, config_subentry_id=None
    ):
        # Only what the unit has shown: every other quantity the model can
        # have gets an entity too, created disabled (entity.py).
        added_entities.extend(
            e for e in new_entities if e.entity_registry_enabled_default
        )

    await async_setup_entry(hass, dummy_entry, mock_add_entities)
    await binary_async_setup_entry(hass, dummy_entry, mock_add_entities)

    for entity in added_entities:
        name = getattr(entity.entity_description, "key", "unknown")
        value = (
            entity.is_on
            if isinstance(entity, AsekoLocalBinarySensorEntity)
            else entity.native_value
        )
        available = entity.available
        status = "enabled" if getattr(entity, "enabled", True) else "disabled"
        print(
            f"Sensor: {name}, Available: {available}, Status: {status}, Value: {value}"
        )

    assert device.device_type == AsekoDeviceType.SALT
    assert any(isinstance(e, AsekoLocalSensorEntity) for e in added_entities)
    assert any(isinstance(e, AsekoLocalBinarySensorEntity) for e in added_entities)
    assert any(
        getattr(e.device, "serial_number", None) == device.serial_number
        for e in added_entities
    )
    # 12 sensors + 7 new (filtration schedule, pool volume, delays) + 4 binary
    # water_flow, electrolysis_running, filtration and ph_minus
    # + 2 consumption (ph_minus canister + total) + 1 connection_status
    # + 3 new backwash config sensors (every_n_days, time, duration)
    # + 4 backwash history sensors (last_backwash, last_scheduled_backwash,
    #   last_manual_backwash, next_scheduled_backwash; last_scheduled_backwash
    #   is a datetime entity, counted by that platform instead)
    # + 1 new backwash_running binary sensor
    # + 1 new heating_running binary sensor
    # + 1 last_manual_backwash sensor; last_scheduled_backwash is a datetime
    #   entity, counted by that platform rather than here
    # byte[37] reshuffle, net zero:
    #   -1 filtration_nonstop24 binary sensor (the schedule sensor covers it)
    #   -1 filtration_mode sensor (it conflated the schedule with bit 0x04)
    #   +1 filtration_schedule sensor  — what the unit runs unattended
    #   +1 service_menu binary sensor  — bit 0x04, a device state, not a
    #      filtration one
    # + 1 last_seen: present on every unit, so it is created up front and
    #   reads "unknown" until the coordinator stamps the first frame.  It used
    #   to be skipped here only because this test hands the platform a device
    #   the coordinator has not stamped yet.
    # + 2 heating_control_enabled / freeze_protection_enabled binary sensors: the
    #   SALT Configuration menu has Heating control and Winter mode, but
    #   their place in the frame is not known yet, so they read unknown
    # - 1 free_chlorine_mv: bytes 20-21 are salinity and chlorine production
    #   on SALT, not a probe voltage
    # + 2 clock_offset sensor / clock_out_of_sync binary sensor: the unit sends
    #   its clock (bytes 6-11)
    assert len(added_entities) == 48
    assert not any(
        getattr(e.entity_description, "key", None) == "free_chlorine_mv"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "water_flow_to_probes"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "electrolyzer_active"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "pump_running"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "required_free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "rx" for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "required_rx"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "required_algicide"
        for e in added_entities
    )
    assert any(isinstance(e, AsekoConsumptionSensorEntity) for e in added_entities)


@pytest.mark.asyncio
async def test_async_setup_net_clf(hass) -> None:
    """Test that async_setup_entry adds sensor entities for available sensors."""

    # Use the decoder to create a valid device
    raw_bytes = _make_net_clf_bytes()
    device = decode(raw_bytes)

    class DummyCoordinator:
        def get_devices(self):
            return [device]

        def get_tracker(self, serial_number):
            return None

        def async_add_new_device_listener(self, listener):
            return lambda: None

        def async_add_new_features_listener(self, listener):
            return lambda: None

    # Create a MagicMock for ConfigEntry with runtime_data attribute
    dummy_entry = MagicMock(spec=ConfigEntry)
    # entry_id is an instance attribute, so spec= does not provide it, but
    # async_setup_entry needs it for the unique_id migration pass.
    dummy_entry.entry_id = "test_entry_id"
    dummy_entry.runtime_data = type(
        "RuntimeData", (), {"coordinator": DummyCoordinator()}
    )

    added_entities = []

    # Correct callback signature for async_add_entities
    def mock_add_entities(
        new_entities, update_before_add=False, *, config_subentry_id=None
    ):
        # Only what the unit has shown: every other quantity the model can
        # have gets an entity too, created disabled (entity.py).
        added_entities.extend(
            e for e in new_entities if e.entity_registry_enabled_default
        )

    await async_setup_entry(hass, dummy_entry, mock_add_entities)
    await binary_async_setup_entry(hass, dummy_entry, mock_add_entities)

    print(device.device_type)

    for entity in added_entities:
        name = getattr(entity.entity_description, "key", "unknown")
        value = (
            entity.is_on
            if isinstance(entity, AsekoLocalBinarySensorEntity)
            else entity.native_value
        )
        status = "enabled" if getattr(entity, "enabled", True) else "disabled"
        print(f"Sensor: {name}, Status: {status}, Value: {value}")

    assert device.device_type == AsekoDeviceType.NET
    assert any(isinstance(e, AsekoLocalSensorEntity) for e in added_entities)
    assert any(isinstance(e, AsekoLocalBinarySensorEntity) for e in added_entities)
    assert any(
        getattr(e.device, "serial_number", None) == device.serial_number
        for e in added_entities
    )
    # 8 sensors + 2 new (pool_volume, dosing_delay; filtration None).
    # startup_delay is not created: this NET frame carries 0xFFFF in
    # bytes 74-75, the "not filled in" marker, which used to read as 65535 s.
    # + 3 binary (water_flow, cl_pump, ph_minus_pump – NET has no filtration output,
    #   so it never had the retired filtration_nonstop24 sensor either)
    # + 4 consumption (ph_minus canister + total, cl canister + total) + 1 connection_status
    # note: algaecide_dose_target/flocculant_dose_target are absent because byte[37]=0xFF (undefined)
    # note: filtration sensors skipped because start/stop times are None in NET test data
    # + 1 heating_running binary sensor
    # Issue #129: NET has no backwash valve and no filling valve, so the
    # backwash / water_level / max_refill_time groups are *all* suppressed.
    # The backwash config + history sensors that the old code created
    # (every_n_days, time, duration, last_backwash, next_scheduled_backwash) plus
    # max_refill_time are no longer created for NET, even when the frame
    # carries non-0xFF data in those byte slots.  The history sensors are
    # gated on the device having a backwash valve, not on their own value,
    # so this stays true now that they start out unknown.
    # + 1 last_seen: present on every unit, so it is created up front and
    #   reads "unknown" until the coordinator stamps the first frame.  It used
    #   to be skipped here only because this test hands the platform a device
    #   the coordinator has not stamped yet.
    assert len(added_entities) == 23
    assert not any(
        getattr(e.entity_description, "key", None) == "backwash_every_n_days"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "backwash_time"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "backwash_duration"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "last_backwash"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "next_scheduled_backwash"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "last_manual_backwash"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "last_scheduled_backwash"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "max_filling_time"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "water_level"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "free_chlorine_mv"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "required_free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "rx" for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "required_rx"
        for e in added_entities
    )
    assert not any(
        getattr(e.entity_description, "key", None) == "required_algicide"
        for e in added_entities
    )
    assert any(isinstance(e, AsekoConsumptionSensorEntity) for e in added_entities)


@pytest.mark.asyncio
async def test_async_setup_profi_clf_redox(hass) -> None:
    """Test that async_setup_entry adds sensor entities for available sensors."""

    # Use the decoder to create a valid device
    raw_bytes = _make_profi_clf_redox_bytes()
    device = decode(raw_bytes)

    class DummyCoordinator:
        def get_devices(self):
            return [device]

        def get_tracker(self, serial_number):
            return None

        def async_add_new_device_listener(self, listener):
            return lambda: None

        def async_add_new_features_listener(self, listener):
            return lambda: None

    # Create a MagicMock for ConfigEntry with runtime_data attribute
    dummy_entry = MagicMock(spec=ConfigEntry)
    # entry_id is an instance attribute, so spec= does not provide it, but
    # async_setup_entry needs it for the unique_id migration pass.
    dummy_entry.entry_id = "test_entry_id"
    dummy_entry.runtime_data = type(
        "RuntimeData", (), {"coordinator": DummyCoordinator()}
    )

    added_entities = []

    # Correct callback signature for async_add_entities
    def mock_add_entities(
        new_entities, update_before_add=False, *, config_subentry_id=None
    ):
        # Only what the unit has shown: every other quantity the model can
        # have gets an entity too, created disabled (entity.py).
        added_entities.extend(
            e for e in new_entities if e.entity_registry_enabled_default
        )

    await async_setup_entry(hass, dummy_entry, mock_add_entities)
    await binary_async_setup_entry(hass, dummy_entry, mock_add_entities)

    print(device.device_type)

    for entity in added_entities:
        name = getattr(entity.entity_description, "key", "unknown")
        value = (
            entity.is_on
            if isinstance(entity, AsekoLocalBinarySensorEntity)
            else entity.native_value
        )
        status = "enabled" if getattr(entity, "enabled", True) else "disabled"
        print(f"Sensor: {name}, Status: {status}, Value: {value}")

    assert device.device_type == AsekoDeviceType.PROFI
    assert any(isinstance(e, AsekoLocalSensorEntity) for e in added_entities)
    assert any(isinstance(e, AsekoLocalBinarySensorEntity) for e in added_entities)
    assert any(
        getattr(e.device, "serial_number", None) == device.serial_number
        for e in added_entities
    )
    # 16 sensors + 6 binary (water_flow, filtration, cl_pump, ph_minus_pump,
    # floc_pump, heating_running, refilling, backwash_running)
    # + 6 consumption (cl, ph_minus, floc × canister + total) + 1 connection_status
    # + 4 alarm binary sensors (ph_too_many_doses, orp_too_many_doses,
    #   no_flow_to_probes, rapid_ph_change)
    # + 3 new backwash config sensors (every_n_days, time, duration)
    # + 4 backwash history sensors (last_backwash, last_scheduled_backwash,
    #   last_manual_backwash, next_scheduled_backwash; last_scheduled_backwash
    #   is a datetime entity, counted by that platform instead)
    # + 1 max_refill_time sensor (data[76:78])
    #
    # Regular sensors (16): free_chlorine, free_chlorine_target,
    #   free_chlorine_mv, ph, ph_target, rx, water_temp, required_water_temp,
    #   ph_minus_flow_rate, flocculant_flow_rate,
    #   backwash_interval, backwash_start_time, backwash_duration,
    #   last_backwash, last_scheduled_backwash, last_manual_backwash,
    #   next_scheduled_backwash
    # Binary sensors (6): water_flow_to_probes, pump_running, chlorine_pump_running,
    #   ph_minus_pump_running, flocculant_pump_running, refilling
    # Heating-related (1 binary): heating_running
    # Backwash-related (1 binary): backwash_running
    # Alarm-related (4 binary): alarm_ph_dosing_ineffective, alarm_max_disinfection_dose,
    #   alarm_no_flow_to_probes, alarm_rapid_ph_change
    #
    # + 1 flocculant_dose_target: the PROFI manual's setpoints screen has a flocculant
    #   dose on its shared flocculant / algicide output, routed like SALT's
    #
    # NOTE: refilling is only present because _fill_home_water_level_data
    # was widened from a {HOME, SALT, OXY} whitelist to a {NET} blacklist (see
    # PR #120 review comment by hopkins-tk).  PROFI does have a water-level input
    # (confirmed via the Aseko Profi manual), so it must be decoded.
    #
    # + 1 max_refill_time: the 2021 PROFI manual shows a water filling relay
    #   and lists a max. filling time, so the value Issue #129 suppressed is
    #   read again (bytes 76-77)
    #
    # + 1 last_manual_backwash sensor; last_scheduled_backwash is a datetime
    #   entity, counted by that platform rather than here
    # byte[37] reshuffle, net zero:
    #   -1 filtration_nonstop24 binary sensor (the schedule sensor covers it)
    #   -1 filtration_mode sensor (it conflated the schedule with bit 0x04)
    #   +1 filtration_schedule sensor  — what the unit runs unattended
    #   +1 service_menu binary sensor  — bit 0x04, a device state, not a
    #      filtration one
    # + 1 last_seen: present on every unit, so it is created up front and
    #   reads "unknown" until the coordinator stamps the first frame.  It used
    #   to be skipped here only because this test hands the platform a device
    #   the coordinator has not stamped yet.
    # + 2 clock_offset sensor / clock_out_of_sync binary sensor: the unit sends
    #   its clock (bytes 6-11)
    assert len(added_entities) == 49
    assert any(
        getattr(e.entity_description, "key", None) == "free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "free_chlorine_mv"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "required_free_chlorine"
        for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) == "rx" for e in added_entities
    )
    assert any(
        getattr(e.entity_description, "key", None) != "required_rx"
        for e in added_entities
    )
    # the PROFI setpoints screen has a flocculant dose (profile per manuals)
    assert any(
        getattr(e.entity_description, "key", None) == "required_floc"
        for e in added_entities
    )
    # PROFI has a water-level input (confirmed by the Aseko Profi manual), so
    # _fill_home_water_level_data must run for it.  The refilling
    # bit (byte[29] & 0x02) is False in this fixture, but the entity must
    # still be registered.
    assert any(
        getattr(e.entity_description, "key", None) == "water_filling_active"
        for e in added_entities
    )
    # The 2021 PROFI manual shows a water filling relay and a max. filling
    # time, so the PROFI profile reads it again (bytes 76-77 = 3600 s here).
    assert any(
        getattr(e.entity_description, "key", None) == "max_filling_time"
        for e in added_entities
    )


# ── unique_id migration ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_migrate_next_backwash_unique_id(hass, mock_config_entry) -> None:
    """The renamed next_backwash sensor keeps its entity_id and history.

    Renaming a sensor key changes the unique_id, which would otherwise orphan
    the existing registry entry: the old entity would go permanently
    unavailable and a second one would appear beside it.
    """
    registry = er.async_get(hass)
    old = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "1234next_backwash",
        config_entry=mock_config_entry,
        suggested_object_id="aseko_next_backwash",
    )

    async_migrate_unique_ids(hass, mock_config_entry)

    migrated = registry.async_get(old.entity_id)
    assert migrated is not None
    assert migrated.unique_id == "1234next_scheduled_backwash"
    # Same registry entry, so the entity_id — and everything keyed on it — survives.
    assert migrated.entity_id == old.entity_id


@pytest.mark.asyncio
async def test_migrate_unique_ids_is_idempotent(hass, mock_config_entry) -> None:
    """Running the migration again leaves the already-migrated entry alone."""
    registry = er.async_get(hass)
    entry = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "1234next_scheduled_backwash",
        config_entry=mock_config_entry,
    )

    async_migrate_unique_ids(hass, mock_config_entry)
    async_migrate_unique_ids(hass, mock_config_entry)

    assert (
        registry.async_get(entry.entity_id).unique_id == "1234next_scheduled_backwash"
    )


@pytest.mark.asyncio
async def test_migrate_unique_ids_skips_when_target_exists(
    hass, mock_config_entry
) -> None:
    """A stale old entry is left in place rather than colliding with the new one.

    async_update_entity would raise if the target unique_id is already taken,
    which would break setup for the whole config entry.
    """
    registry = er.async_get(hass)
    old = registry.async_get_or_create(
        "sensor", DOMAIN, "1234next_backwash", config_entry=mock_config_entry
    )
    new = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "1234next_scheduled_backwash",
        config_entry=mock_config_entry,
    )

    async_migrate_unique_ids(hass, mock_config_entry)

    assert registry.async_get(old.entity_id).unique_id == "1234next_backwash"
    assert registry.async_get(new.entity_id).unique_id == "1234next_scheduled_backwash"


@pytest.mark.asyncio
async def test_migrate_unique_ids_leaves_other_sensors_untouched(
    hass, mock_config_entry
) -> None:
    """Only the renamed keys are rewritten."""
    registry = er.async_get(hass)
    entry = registry.async_get_or_create(
        "sensor", DOMAIN, "1234last_backwash", config_entry=mock_config_entry
    )

    async_migrate_unique_ids(hass, mock_config_entry)

    assert registry.async_get(entry.entity_id).unique_id == "1234last_backwash"


# ── retired entities ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retired_nonstop24_entity_is_removed(hass, mock_config_entry) -> None:
    """The dropped filtration_nonstop24 sensor is deleted from the registry.

    Removing the entity description alone would leave the registry entry
    behind, and the entity would sit in the UI as unavailable forever with
    no sign that it is never coming back.
    """
    registry = er.async_get(hass)
    retired = registry.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        "1234filtration_nonstop24",
        config_entry=mock_config_entry,
        suggested_object_id="aseko_filtration_nonstop_24h",
    )

    async_remove_retired_entities(hass, mock_config_entry)

    assert registry.async_get(retired.entity_id) is None


@pytest.mark.asyncio
async def test_retired_removal_leaves_other_entities_alone(
    hass, mock_config_entry
) -> None:
    """Only the retired key is touched — and only in its own domain."""
    registry = er.async_get(hass)
    keep_binary = registry.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        "1234filtration_pump_running",
        config_entry=mock_config_entry,
    )
    keep_sensor = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "1234filtration_schedule",
        config_entry=mock_config_entry,
    )

    async_remove_retired_entities(hass, mock_config_entry)

    assert registry.async_get(keep_binary.entity_id) is not None
    assert registry.async_get(keep_sensor.entity_id) is not None


@pytest.mark.asyncio
async def test_retired_removal_is_idempotent(hass, mock_config_entry) -> None:
    """A second run has nothing left to do and must not raise."""
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        "1234filtration_nonstop24",
        config_entry=mock_config_entry,
    )

    async_remove_retired_entities(hass, mock_config_entry)
    async_remove_retired_entities(hass, mock_config_entry)

    assert not [
        entry
        for entry in er.async_entries_for_config_entry(
            registry, mock_config_entry.entry_id
        )
        if entry.unique_id.endswith("filtration_nonstop24")
    ]


# ── filtration schedule, and the settings-menu flag beside it ───────────────


def _decode_salt(byte37: int):
    """Decode a SALT frame carrying the given byte[37]."""
    data = _make_salt_redox_bytes()
    data[37] = byte37
    return decode(bytes(data))


@pytest.mark.parametrize(
    ("byte37", "expected_schedule", "expected_menu"),
    [
        (0xC3, "nonstop_24h", False),
        (0xD3, "timer_period_1", False),
        (0xF3, "timer_period_1_and_2", False),
        (0xC7, "nonstop_24h", True),
        (0xD7, "timer_period_1", True),
        (0xF7, "timer_period_1_and_2", True),
    ],
)
def test_schedule_and_service_menu_are_independent(
    byte37: int, expected_schedule: str, expected_menu: bool
) -> None:
    """byte[37] holds two unrelated things, reported by two entities.

    The schedule is what the unit runs when nobody is at it.  The service
    menu says somebody is — and nothing more, because the unit stops
    transmitting while it is open.  Neither can stand in for the other.
    """
    schedule = next(d for d in SENSORS if d.key == "filtration_schedule")
    menu = next(d for d in BINARY_SENSORS if d.key == "service_menu")
    device = _decode_salt(byte37)

    assert schedule.value_fn(device) == expected_schedule
    assert menu.value_fn(device) is expected_menu


def test_no_filtration_mode_sensor_remains() -> None:
    """The conflated sensor is gone, and its registry entry with it.

    It reported a schedule *or* the menu flag, never both, so it could not
    answer either question reliably.
    """
    assert not any(d.key == "filtration_mode" for d in SENSORS)
    assert "filtration_mode" in RETIRED_SENSOR_IDS


def test_schedule_and_service_menu_absent_without_filtration() -> None:
    """NET has no filtration output, so neither entity is created for it."""
    schedule = next(d for d in SENSORS if d.key == "filtration_schedule")
    menu = next(d for d in BINARY_SENSORS if d.key == "service_menu")
    device = decode(bytes(_make_net_clf_bytes()))

    assert device.device_type == AsekoDeviceType.NET
    # A None value is what keeps an entity from being built for a device.
    assert schedule.value_fn(device) is None
    assert menu.value_fn(device) is None
