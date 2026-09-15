"""A known device that starts showing new features gets their entities.

Presence is decided per frame by the decoder, but a unit can show a quantity
for the first time long after it was first seen: the shared pump port gets
configured, a setting is made, byte[37] becomes readable.  The coordinator
keeps the stored device's feature set as the union of everything seen, and
tells the platforms about each addition so they can build just those
entities.  These tests drive the coordinator with a mock ``hass`` and the
platform builders directly, so they run without the Home Assistant fixtures.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.aseko_local import entity as entity_module
from custom_components.aseko_local.binary_sensor import _build_binary_sensor_entities
from custom_components.aseko_local.button import _build_button_entities
from custom_components.aseko_local.coordinator import AsekoLocalDataUpdateCoordinator
from custom_components.aseko_local.datetime import _build_entities as _build_datetime
from custom_components.aseko_local.decoding import decode
from custom_components.aseko_local.entity import enabled_unique_ids
from custom_components.aseko_local.models import AsekoDevice
from custom_components.aseko_local.sensor import _build_sensor_entities

from .test_decode_v7 import _make_base_bytes


@pytest.fixture(autouse=True)
def _quiet_logging() -> Iterator[None]:
    """Silence logging for this module's tests only, and turn it back on."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


SERIAL = 1234  # what _make_base_bytes writes into bytes 0-3


def _coordinator() -> AsekoLocalDataUpdateCoordinator:
    hass = MagicMock()
    hass.config.path.side_effect = lambda *parts: "/tmp/aseko_test/" + "/".join(parts)
    hass.async_create_task.side_effect = lambda coro, *args, **kwargs: coro.close()
    entry = MagicMock()
    entry.data = {"host": "0.0.0.0", "port": 47524}
    entry.unique_id = "test"
    return AsekoLocalDataUpdateCoordinator(hass, entry)


def _salt_frame(byte37: int, flowrate_third_pump: int = 0xFF) -> bytes:
    data = _make_base_bytes()  # SALT, REDOX probe
    data[37] = byte37
    data[101] = flowrate_third_pump
    return bytes(data)


ALGICIDE_FIELDS = {
    "algaecide_flow_rate",
    "algaecide_pump_running",
    "algaecide_dose_target",
}


# ── the coordinator ──────────────────────────────────────────────────────────


def test_first_frame_goes_through_the_new_device_listener_only() -> None:
    coordinator = _coordinator()
    new_devices: list = []
    new_features: list = []
    coordinator.async_add_new_device_listener(new_devices.append)
    coordinator.async_add_new_features_listener(
        lambda device, features: new_features.append((device, features))
    )

    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))

    assert [d.serial_number for d in new_devices] == [SERIAL]
    assert new_features == []
    assert "algaecide_flow_rate" not in new_devices[0].features


def test_a_later_frame_that_adds_features_calls_the_new_features_listener() -> None:
    """The shared port gets routed to algicide after the unit was first seen."""
    coordinator = _coordinator()
    new_features: list = []
    coordinator.async_add_new_features_listener(
        lambda device, features: new_features.append((device, features))
    )

    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))
    stored = coordinator.get_device(SERIAL)
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert len(new_features) == 1
    device, features = new_features[0]
    assert device is stored  # the object the existing entities read
    assert features == ALGICIDE_FIELDS
    assert stored.features >= ALGICIDE_FIELDS


def test_presence_is_sticky_and_nothing_is_reported_twice() -> None:
    coordinator = _coordinator()
    new_features: list = []
    coordinator.async_add_new_features_listener(
        lambda device, features: new_features.append(features)
    )

    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )
    # the port goes unreadable again, then comes back
    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert new_features == [ALGICIDE_FIELDS]
    assert coordinator.get_device(SERIAL).features >= ALGICIDE_FIELDS


def test_an_unchanged_frame_calls_nobody() -> None:
    coordinator = _coordinator()
    calls: list = []
    coordinator.async_add_new_device_listener(calls.append)
    coordinator.async_add_new_features_listener(lambda d, f: calls.append(f))

    frame = decode(_salt_frame(0xC3, flowrate_third_pump=40))
    coordinator.devices_update_callback(frame)
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert len(calls) == 1  # the discovery only


def test_new_features_listener_can_unsubscribe() -> None:
    coordinator = _coordinator()
    calls: list = []
    unsub = coordinator.async_add_new_features_listener(lambda d, f: calls.append(f))

    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))
    unsub()
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert calls == []


# ── the platforms build only what was added ─────────────────────────────────


class _PlatformCoordinator:
    def get_tracker(self, serial_number) -> None:
        return None


@pytest.fixture
def grown_device() -> AsekoDevice:
    """A SALT that has just started showing its algicide port."""
    device = decode(_salt_frame(0xC3, flowrate_third_pump=40))
    assert device.features >= ALGICIDE_FIELDS
    return device


def test_sensor_platform_builds_only_the_added_fields(grown_device) -> None:
    keys = {
        e.entity_description.key
        for e in _build_sensor_entities(
            [grown_device], _PlatformCoordinator(), frozenset(ALGICIDE_FIELDS)
        )
    }
    assert keys == {
        "flowrate_algicide",
        "required_algicide",
        "algicide_consumed",
        "algicide_total_consumed",
    }


def test_binary_sensor_platform_builds_only_the_added_fields(grown_device) -> None:
    keys = {
        e.entity_description.key
        for e in _build_binary_sensor_entities(
            [grown_device], _PlatformCoordinator(), frozenset(ALGICIDE_FIELDS)
        )
    }
    assert keys == {"algicide_pump_running"}


def test_button_platform_builds_only_the_added_pump(grown_device) -> None:
    keys = {
        e.entity_description.key
        for e in _build_button_entities(
            [grown_device], _PlatformCoordinator(), frozenset(ALGICIDE_FIELDS)
        )
    }
    assert keys == {"algicide_refill_reset"}


def test_datetime_platform_only_reacts_to_the_backwash_valve(grown_device) -> None:
    coordinator = _PlatformCoordinator()
    assert (
        _build_datetime([grown_device], coordinator, frozenset(ALGICIDE_FIELDS)) == []
    )
    assert (
        len(
            _build_datetime(
                [grown_device], coordinator, frozenset({"backwash_running"})
            )
        )
        == 1
    )


def test_always_present_sensors_are_not_rebuilt_on_growth(grown_device) -> None:
    """connection_status and last_seen belong to the first set-up only."""
    keys = {
        e.entity_description.key
        for e in _build_sensor_entities(
            [grown_device], _PlatformCoordinator(), frozenset({"ph"})
        )
    }
    assert keys == {"ph"}


def test_growth_never_builds_a_field_the_model_lacks(grown_device) -> None:
    """A field named by the listener is still checked against the model."""
    keys = {
        e.entity_description.key
        for e in _build_sensor_entities(
            [grown_device], _PlatformCoordinator(), frozenset({"oxygen_dose_target"})
        )
    }
    assert keys == set()  # a SALT has no OXY Pure dose


def test_the_whole_chain_adds_exactly_the_algicide_entities() -> None:
    """Coordinator listener wired to the builders, the way the platforms do it."""
    coordinator = _coordinator()
    platform = _PlatformCoordinator()
    added: list = []

    def on_new_features(device, features) -> None:
        added.extend(_build_sensor_entities([device], platform, features))
        added.extend(_build_binary_sensor_entities([device], platform, features))
        added.extend(_build_button_entities([device], platform, features))
        added.extend(_build_datetime([device], platform, features))

    coordinator.async_add_new_features_listener(on_new_features)
    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))
    assert added == []

    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )
    assert {e.entity_description.key for e in added} == {
        "flowrate_algicide",
        "required_algicide",
        "algicide_consumed",
        "algicide_total_consumed",
        "algicide_pump_running",
        "algicide_refill_reset",
    }
    stored = coordinator.get_device(SERIAL)
    assert all(e.device is stored for e in added)


# ── every quantity the model can have gets an entity ────────────────────────


class _AvailableCoordinator(_PlatformCoordinator):
    last_update_success = True


def _entities_by_key(device) -> dict[str, Any]:
    coordinator = _AvailableCoordinator()
    entities = (
        _build_sensor_entities([device], coordinator)
        + _build_binary_sensor_entities([device], coordinator)
        + _build_button_entities([device], coordinator)
        + _build_datetime([device], coordinator)
    )
    return {e.entity_description.key: e for e in entities}


def test_quantities_the_unit_has_not_shown_get_disabled_entities() -> None:
    """R7: a REDOX SALT with an unrouted port -- the entities exist, disabled."""
    device = decode(_salt_frame(0xFF))
    entities = _entities_by_key(device)

    # the quantities the unit shows are enabled
    assert entities["ph"].entity_registry_enabled_default is True
    assert entities["rx"].entity_registry_enabled_default is True
    assert entities["connection_status"].entity_registry_enabled_default is True
    # the model has them, this unit has not shown them: there, but disabled
    for key in (
        "free_chlorine",
        "flowrate_algicide",
        "algicide_pump_running",
        "algicide_refill_reset",
    ):
        assert key in entities, key
        assert entities[key].entity_registry_enabled_default is False, key
    # a quantity no SALT has gets no entity at all
    assert "required_oxy" not in entities
    assert "flowrate_oxy" not in entities


def test_an_entity_is_unavailable_while_its_quantity_is_not_present() -> None:
    """R7: shown once, then not in the last frame -> unavailable, not removed."""
    coordinator = _coordinator()
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )
    stored = coordinator.get_device(SERIAL)
    entities = _entities_by_key(stored)
    algicide = entities["flowrate_algicide"]
    assert algicide.entity_registry_enabled_default is True
    assert algicide.available is True

    # the port goes unreadable: the stored device keeps the feature, the frame does not
    coordinator.devices_update_callback(decode(_salt_frame(0xFF)))
    assert "algaecide_flow_rate" in stored.features
    assert algicide.available is False
    assert entities["ph"].available is True
    assert entities["connection_status"].available is True


def test_growth_enables_the_entities_the_integration_disabled(monkeypatch) -> None:
    """R7: only integration-disabled entries are enabled; a user's choice stays."""

    class _Entry:
        def __init__(self, disabled_by) -> None:
            self.disabled_by = disabled_by

    entries = {
        "sensor.algicide": _Entry(er.RegistryEntryDisabler.INTEGRATION),
        "sensor.floc": _Entry(er.RegistryEntryDisabler.USER),
    }
    ids = {
        "1234flowrate_algicide": "sensor.algicide",
        "1234flowrate_floc": "sensor.floc",
    }
    enabled: list[str] = []

    class _Registry:
        def async_get_entity_id(self, platform, domain, unique_id) -> str | None:
            return ids.get(unique_id)

        def async_get(self, entity_id) -> MagicMock | None:
            return entries.get(entity_id)

        def async_update_entity(self, entity_id, disabled_by) -> None:
            assert disabled_by is None
            enabled.append(entity_id)

    monkeypatch.setattr(entity_module.er, "async_get", lambda hass: _Registry())
    entity_module.async_enable_entities(
        None, "sensor", ["1234flowrate_algicide", "1234flowrate_floc", "1234unknown"]
    )
    assert enabled == ["sensor.algicide"]


def test_enabled_unique_ids_are_the_shown_quantities() -> None:
    device = decode(_salt_frame(0xFF))
    entities = list(_entities_by_key(device).values())
    ids = set(enabled_unique_ids(entities))
    assert f"{SERIAL}ph" in ids
    assert f"{SERIAL}flowrate_algicide" not in ids


def test_a_failed_platform_setup_is_asked_again_on_the_next_frame() -> None:
    """Minor fix 1: until the platforms are up, every frame requests the set-up."""
    requested: list[int] = []

    async def cb(device) -> None:
        requested.append(device.serial_number)

    coordinator = _coordinator()
    coordinator.cb_new_device = cb

    def run(coro) -> None:
        with contextlib.suppress(StopIteration):
            coro.send(None)

    coordinator.hass.loop.create_task.side_effect = run

    frame = decode(_salt_frame(0xC3, flowrate_third_pump=40))
    coordinator.devices_update_callback(frame)  # new device
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )  # setup failed: again
    assert requested == [SERIAL, SERIAL]

    coordinator.platforms_ready = True
    coordinator.devices_update_callback(
        decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )
    assert requested == [SERIAL, SERIAL]  # set up: not asked again


def test_a_unit_is_offline_after_five_minutes_but_keeps_its_values() -> None:
    """Audit A1: offline is a flag; the last values stay as they were."""

    device = decode(bytes(_make_base_bytes()))
    device.last_seen = dt_util.now() - timedelta(minutes=4)
    assert device.online() is True  # a settings menu can keep it quiet for minutes
    device.last_seen = dt_util.now() - timedelta(minutes=6)
    assert device.online() is False
    assert device.water_temperature == 24.5
    assert "water_temperature" in device.present_features


def test_online_counts_real_minutes_across_a_change_of_time(monkeypatch) -> None:
    """A frame 10 real seconds old is fresh even when the local clock jumped."""

    zone = ZoneInfo("Europe/Bratislava")
    for now in (
        datetime(2026, 3, 29, 1, 0, 5, tzinfo=UTC),
        datetime(2026, 10, 25, 1, 0, 5, tzinfo=UTC),
    ):
        monkeypatch.setattr(dt_util, "utcnow", lambda now=now: now)
        fresh = AsekoDevice(last_seen=(now - timedelta(seconds=10)).astimezone(zone))
        stale = AsekoDevice(last_seen=(now - timedelta(minutes=7)).astimezone(zone))
        assert fresh.online() is True
        assert stale.online() is False
