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

import logging
from unittest.mock import MagicMock

import pytest

from custom_components.aseko_local.aseko_decoder import AsekoDecoder
from custom_components.aseko_local.binary_sensor import _build_binary_sensor_entities
from custom_components.aseko_local.button import _build_button_entities
from custom_components.aseko_local.coordinator import AsekoLocalDataUpdateCoordinator
from custom_components.aseko_local.datetime import _build_entities as _build_datetime
from custom_components.aseko_local.sensor import _build_sensor_entities

from .test_aseko_decoder import _make_base_bytes

logging.disable(logging.CRITICAL)

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

    coordinator.devices_update_callback(AsekoDecoder.decode(_salt_frame(0xFF)))

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

    coordinator.devices_update_callback(AsekoDecoder.decode(_salt_frame(0xFF)))
    stored = coordinator.get_device(SERIAL)
    coordinator.devices_update_callback(
        AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert len(new_features) == 1
    device, features = new_features[0]
    assert device is stored  # the object the existing entities read
    assert features == ALGICIDE_FIELDS
    assert ALGICIDE_FIELDS <= stored.features


def test_presence_is_sticky_and_nothing_is_reported_twice() -> None:
    coordinator = _coordinator()
    new_features: list = []
    coordinator.async_add_new_features_listener(
        lambda device, features: new_features.append(features)
    )

    coordinator.devices_update_callback(AsekoDecoder.decode(_salt_frame(0xFF)))
    coordinator.devices_update_callback(
        AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )
    # the port goes unreadable again, then comes back
    coordinator.devices_update_callback(AsekoDecoder.decode(_salt_frame(0xFF)))
    coordinator.devices_update_callback(
        AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert new_features == [ALGICIDE_FIELDS]
    assert ALGICIDE_FIELDS <= coordinator.get_device(SERIAL).features


def test_an_unchanged_frame_calls_nobody() -> None:
    coordinator = _coordinator()
    calls: list = []
    coordinator.async_add_new_device_listener(calls.append)
    coordinator.async_add_new_features_listener(lambda d, f: calls.append(f))

    frame = AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    coordinator.devices_update_callback(frame)
    coordinator.devices_update_callback(
        AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert len(calls) == 1  # the discovery only


def test_new_features_listener_can_unsubscribe() -> None:
    coordinator = _coordinator()
    calls: list = []
    unsub = coordinator.async_add_new_features_listener(lambda d, f: calls.append(f))

    coordinator.devices_update_callback(AsekoDecoder.decode(_salt_frame(0xFF)))
    unsub()
    coordinator.devices_update_callback(
        AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    )

    assert calls == []


# ── the platforms build only what was added ─────────────────────────────────


class _PlatformCoordinator:
    def get_tracker(self, serial_number):
        return None


@pytest.fixture
def grown_device():
    """A SALT that has just started showing its algicide port."""
    device = AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
    assert ALGICIDE_FIELDS <= device.features
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


def test_growth_never_builds_a_field_the_unit_lacks(grown_device) -> None:
    """A field named by the listener is still checked against the device."""
    keys = {
        e.entity_description.key
        for e in _build_sensor_entities(
            [grown_device], _PlatformCoordinator(), frozenset({"free_chlorine"})
        )
    }
    assert keys == set()  # REDOX unit: no free-chlorine probe


def test_the_whole_chain_adds_exactly_the_algicide_entities() -> None:
    """Coordinator listener wired to the builders, the way the platforms do it."""
    coordinator = _coordinator()
    platform = _PlatformCoordinator()
    added: list = []

    def on_new_features(device, features):
        added.extend(_build_sensor_entities([device], platform, features))
        added.extend(_build_binary_sensor_entities([device], platform, features))
        added.extend(_build_button_entities([device], platform, features))
        added.extend(_build_datetime([device], platform, features))

    coordinator.async_add_new_features_listener(on_new_features)
    coordinator.devices_update_callback(AsekoDecoder.decode(_salt_frame(0xFF)))
    assert added == []

    coordinator.devices_update_callback(
        AsekoDecoder.decode(_salt_frame(0xC3, flowrate_third_pump=40))
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
