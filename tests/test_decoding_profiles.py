"""Tests for the profile-driven decoder: features, profiles, detection, engine.

The byte-level behaviour of every reading is covered by test_aseko_decoder.py
and test_aseko_decoder_v8.py through the public facades.  What is tested here
is the machinery those facades stand on: that the registry is consistent,
that a profile cannot be built wrong, that detection picks the right profile
for the right frame, and that the device says how it was decoded.
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from custom_components.aseko_local.aseko_data import (
    AsekoDevice,
    AsekoDeviceType,
    AsekoFirmwareVariant,
    AsekoProfileFlag,
)
from custom_components.aseko_local.aseko_decoder import AsekoDecoder
from custom_components.aseko_local.aseko_decoder_v8 import AsekoV8Decoder
from custom_components.aseko_local.const import UNIT_TYPE_PROFI, WATER_FLOW_TO_PROBES
from custom_components.aseko_local.decoding import engine
from custom_components.aseko_local.decoding.decoders import (
    ALL_FEATURES,
    AlgicidePumpRunning,
    Configuration,
    FiltrationPumpRunning,
    FiltrationSchedule,
    FlowrateAlgicide,
    Ph,
    ServiceMenuOpen,
    Start2,
)
from custom_components.aseko_local.decoding.feature import Feature
from custom_components.aseko_local.decoding.frame import (
    Protocol,
    parse_frame,
    parse_v7,
    parse_v8,
)
from custom_components.aseko_local.decoding.profile import Profile, ProfileMemory
from custom_components.aseko_local.decoding.profiles import (
    ALL_PROFILES,
    detect_profile,
    profile_for,
    v7,
    v8,
)

from .test_aseko_decoder import _make_base_bytes
from .test_aseko_decoder_v8 import REFERENCE_FRAME, REFERENCE_FRAME_105

DEVICE_FIELDS = {f.name for f in fields(AsekoDevice)}


def _home_bytes(byte37: int) -> bytes:
    data = _make_base_bytes()
    data[4] = 0x02  # HOME, CLF
    data[37] = byte37
    return bytes(data)


# ── the feature registry ─────────────────────────────────────────────────────


def test_every_feature_fills_one_real_field() -> None:
    """One feature, one field on AsekoDevice, no two features on the same one."""
    seen: dict[str, type[Feature]] = {}
    for feature in ALL_FEATURES:
        assert feature.field in DEVICE_FIELDS, feature.__name__
        assert feature.field not in seen, (feature.__name__, seen[feature.field])
        seen[feature.field] = feature


def test_every_frame_derived_field_has_a_feature() -> None:
    """The fields the decoder does not own are the tracker's and the profile's."""
    owned = {f.field for f in ALL_FEATURES}
    not_from_the_frame = {
        "device_type",  # set from the profile
        "firmware_variant",
        "features",
        "flags",
        "last_seen",  # stamped by the coordinator
        "last_backwash",  # BackwashTracker
        "last_scheduled_backwash",
        "last_scheduled_backwash_source",
        "last_manual_backwash",
        "last_backwash_trigger",
        "next_scheduled_backwash",
    }
    assert DEVICE_FIELDS - owned == not_from_the_frame


def test_default_and_named_variants() -> None:
    assert FiltrationSchedule.default_variant(Protocol.V7) == "decode_v7"
    assert FiltrationSchedule.default_variant(Protocol.V8) is None
    assert FiltrationSchedule.variants(Protocol.V7) == (
        "decode_v7",
        "decode_v7_home_a",
    )
    assert FiltrationSchedule.protocols() == (Protocol.V7,)
    assert Ph.protocols() == (Protocol.V7, Protocol.V8)


def test_unmapped_features_have_no_reading_and_no_profile() -> None:
    """pH+ is a field on the device but nothing knows how to read it yet."""
    unmapped = [f for f in ALL_FEATURES if not f.protocols()]
    assert {f.field for f in unmapped} == {
        "ph_plus_pump_running",
        "flowrate_ph_plus",
    }
    for profile in ALL_PROFILES:
        for feature in unmapped:
            assert feature not in profile.features


# ── profiles ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_profile_plan_respects_dependencies(profile: Profile) -> None:
    position = {type(feature): i for i, (feature, _) in enumerate(profile.plan)}
    assert len(position) == len(profile.features)
    for feature in profile.features:
        for dependency in feature.depends_on:
            if dependency in position:
                assert position[dependency] < position[feature], (
                    profile.name,
                    feature.__name__,
                )


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_profile_readings_match_its_protocol(profile: Profile) -> None:
    for feature, read in profile.plan:
        assert read.__name__.startswith(f"decode_{profile.protocol.value}")
        assert type(feature).has_variant(read.__name__)
    assert profile.feature_names <= DEVICE_FIELDS


def test_overrides_pick_the_named_reading() -> None:
    assert v7.HOME_A.variant_for(FiltrationSchedule) == "decode_v7_home_a"
    assert v7.HOME_B.variant_for(FiltrationSchedule) == "decode_v7"
    assert v7.HOME_B.variant_for(FiltrationPumpRunning) == "decode_v7_menu_override"
    assert v7.SALT.variant_for(FiltrationPumpRunning) == "decode_v7"
    assert v7.OXY.variant_for(AlgicidePumpRunning) == "decode_v7_oxy"


def test_a_feature_absent_from_a_profile_is_a_model_without_it() -> None:
    assert Start2 not in v7.NET.features
    assert ServiceMenuOpen not in v7.HOME_A.features
    assert ServiceMenuOpen in v7.HOME_B.features
    assert "backwash_active" not in v7.NET.feature_names
    assert "backwash_active" in v7.SALT.feature_names


def test_only_salt_treats_the_menu_bit_as_presence() -> None:
    with_flag = {
        p.name
        for p in ALL_PROFILES
        if AsekoProfileFlag.MENU_BIT_IS_PRESENCE_ONLY in p.flags
    }
    assert with_flag == {"v7 SALT"}


def test_profile_rejects_a_feature_without_a_reading_for_its_protocol() -> None:
    with pytest.raises(ValueError, match="has no v8 reading"):
        Profile(
            name="broken",
            protocol=Protocol.V8,
            model=AsekoDeviceType.NET,
            features=(FiltrationSchedule,),
        )


def test_profile_rejects_an_override_naming_a_missing_reading() -> None:
    with pytest.raises(ValueError, match="has no reading"):
        Profile(
            name="broken",
            protocol=Protocol.V7,
            model=AsekoDeviceType.SALT,
            features=(FiltrationSchedule,),
            overrides={FiltrationSchedule: "decode_v7_salt_special"},
        )


def test_profile_rejects_an_override_for_an_unlisted_feature() -> None:
    with pytest.raises(ValueError, match="unlisted"):
        Profile(
            name="broken",
            protocol=Protocol.V7,
            model=AsekoDeviceType.SALT,
            features=(Ph,),
            overrides={FiltrationSchedule: "decode_v7_home_a"},
        )


def test_profile_rejects_an_override_from_the_other_protocol() -> None:
    with pytest.raises(ValueError, match="is not a v8 reading"):
        Profile(
            name="broken",
            protocol=Protocol.V8,
            model=AsekoDeviceType.NET,
            features=(Ph,),
            overrides={Ph: "decode_v7"},
        )


def test_profile_orders_dependencies_ahead_whatever_the_listing_says() -> None:
    profile = Profile(
        name="reordered",
        protocol=Protocol.V7,
        model=AsekoDeviceType.SALT,
        features=(AlgicidePumpRunning, FlowrateAlgicide, Ph, Configuration),
    )
    order = [type(feature) for feature, _ in profile.plan]
    assert order.index(FlowrateAlgicide) < order.index(AlgicidePumpRunning)
    assert order.index(Configuration) < order.index(Ph)


def test_profile_detects_a_dependency_cycle() -> None:
    class A(Feature):
        field = "ph"

        def decode_v7(self, frame, device):
            return None

    class B(Feature):
        field = "redox"
        depends_on = (A,)

        def decode_v7(self, frame, device):
            return None

    A.depends_on = (B,)
    with pytest.raises(ValueError, match="cycle"):
        Profile(name="cyclic", protocol=Protocol.V7, model=None, features=(A, B))


# ── detection ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("unit_type", "expected"),
    [
        (0x0E, v7.SALT),
        (0x09, v7.NET),
        (0x05, v7.OXY),
        (UNIT_TYPE_PROFI, v7.PROFI),
        (0x00, v7.UNKNOWN),
    ],
)
def test_detect_v7_model_from_byte4(unit_type: int, expected: Profile) -> None:
    data = _make_base_bytes()
    data[4] = unit_type
    profile, firmware = detect_profile(parse_v7(bytes(data)))
    assert profile is expected
    assert firmware is None


@pytest.mark.parametrize(
    ("byte37", "expected_profile", "expected_firmware"),
    [
        (0x43, v7.HOME_A, AsekoFirmwareVariant.HOME_A),
        (0x53, v7.HOME_A, AsekoFirmwareVariant.HOME_A),
        (0x49, v7.HOME_A, AsekoFirmwareVariant.HOME_A),
        (0x01, v7.HOME_B, AsekoFirmwareVariant.HOME_B),
        (0x31, v7.HOME_B, AsekoFirmwareVariant.HOME_B),
        (0xFF, v7.HOME_UNKNOWN_FIRMWARE, None),
    ],
)
def test_detect_home_firmware_from_byte37(
    byte37: int, expected_profile: Profile, expected_firmware
) -> None:
    profile, firmware = detect_profile(parse_v7(_home_bytes(byte37)))
    assert profile is expected_profile
    assert firmware is expected_firmware


def test_memory_carries_the_firmware_over_an_unset_byte37() -> None:
    """Detection runs per frame; a frame that says nothing borrows the last that did."""
    memory = ProfileMemory()

    profile, firmware = detect_profile(parse_v7(_home_bytes(0x43)), memory)
    assert (profile, firmware) == (v7.HOME_A, AsekoFirmwareVariant.HOME_A)

    profile, firmware = detect_profile(parse_v7(_home_bytes(0xFF)), memory)
    assert (profile, firmware) == (v7.HOME_A, AsekoFirmwareVariant.HOME_A)

    # and a frame that does say something wins over the memory
    profile, firmware = detect_profile(parse_v7(_home_bytes(0x11)), memory)
    assert (profile, firmware) == (v7.HOME_B, AsekoFirmwareVariant.HOME_B)

    # a different unit shares nothing
    other = _make_base_bytes()
    other[0:4] = (4321).to_bytes(4, "big")
    other[4] = 0x02
    other[37] = 0xFF
    profile, firmware = detect_profile(parse_v7(bytes(other)), memory)
    assert (profile, firmware) == (v7.HOME_UNKNOWN_FIRMWARE, None)


def test_detect_v8_model_from_header_type() -> None:
    assert detect_profile(parse_v8(REFERENCE_FRAME)) == (v8.NET, None)
    assert detect_profile(parse_v8(REFERENCE_FRAME_105)) == (v8.SALT, None)


def test_detect_v8_unknown_header_falls_back_to_net() -> None:
    frame = parse_v8(REFERENCE_FRAME.replace(b" 804 ", b" 999 "))
    assert detect_profile(frame) == (v8.NET, None)


def test_parse_frame_picks_the_protocol() -> None:
    assert parse_frame(bytes(_make_base_bytes())).protocol is Protocol.V7
    assert parse_frame(REFERENCE_FRAME).protocol is Protocol.V8
    assert parse_frame(b"\n" + REFERENCE_FRAME).protocol is Protocol.V8


def test_profile_for_home_without_a_firmware_reads_only_the_shared_part() -> None:
    assert profile_for(Protocol.V7, AsekoDeviceType.HOME) is v7.HOME_UNKNOWN_FIRMWARE
    assert ServiceMenuOpen not in v7.HOME_UNKNOWN_FIRMWARE.features
    assert v7.HOME_UNKNOWN_FIRMWARE.feature_names <= v7.HOME_B.feature_names
    assert (
        profile_for(Protocol.V7, AsekoDeviceType.HOME, AsekoFirmwareVariant.HOME_A)
        is v7.HOME_A
    )
    assert profile_for(Protocol.V7, None) is v7.UNKNOWN


# ── the engine, and what the device says about itself ───────────────────────


def test_decoded_device_says_how_it_was_read() -> None:
    device = AsekoDecoder.decode(_home_bytes(0x43))
    assert device.device_type is AsekoDeviceType.HOME
    assert device.firmware_variant is AsekoFirmwareVariant.HOME_A
    assert device.features <= v7.HOME_A.feature_names
    assert "filtration_schedule" in device.features
    assert device.flags == frozenset()

    salt = AsekoDecoder.decode(bytes(_make_base_bytes()))
    assert salt.firmware_variant is None
    assert AsekoProfileFlag.MENU_BIT_IS_PRESENCE_ONLY in salt.flags

    net_v8 = AsekoV8Decoder.decode(REFERENCE_FRAME)
    assert net_v8.features <= v8.NET.feature_names
    assert "ph" in net_v8.features
    assert "start1" not in net_v8.features


def test_facades_are_the_engine() -> None:
    raw = bytes(_make_base_bytes())
    assert AsekoDecoder.decode(raw) == engine.decode_raw(raw)
    assert AsekoV8Decoder.decode(REFERENCE_FRAME) == engine.decode_raw(REFERENCE_FRAME)


def test_a_field_outside_the_profile_stays_none_whatever_the_frame_says() -> None:
    """NET has no filtration output; the bytes are read by nobody."""
    data = _make_base_bytes()
    data[4] = 0x09  # NET
    device = AsekoDecoder.decode(bytes(data))
    assert "start1" not in device.features
    assert device.start1 is None
    assert device.filtration_pump_running is None


def test_home_b_menu_override_forces_the_pump_off() -> None:
    data = _make_base_bytes()
    data[4] = 0x02
    data[29] = 0x08  # relay bit says running
    data[37] = 0x15  # firmware B, period 1, settings menu open
    device = AsekoDecoder.decode(bytes(data))
    assert device.firmware_variant is AsekoFirmwareVariant.HOME_B
    assert device.service_menu_open is True
    assert device.filtration_pump_running is False

    data[37] = 0x11  # menu closed
    assert AsekoDecoder.decode(bytes(data)).filtration_pump_running is True


def test_entity_layer_reads_pump_presence_off_the_device() -> None:
    from custom_components.aseko_local.sensor import device_has_pump

    data = _make_base_bytes()
    data[4] = 0x09  # NET
    data[28] = WATER_FLOW_TO_PROBES
    data[29] = 0x00
    net = AsekoDecoder.decode(bytes(data))
    assert device_has_pump(net, "cl")
    assert device_has_pump(net, "ph_minus")
    assert not device_has_pump(net, "algicide")  # not a NET feature
    assert not device_has_pump(net, "ph_plus")  # nobody's feature

    salt = AsekoDecoder.decode(bytes(_make_base_bytes()))  # byte[37] = 0xFF
    assert "algicide_pump_running" in v7.SALT.feature_names  # the model has it
    assert "algicide_pump_running" not in salt.features  # this unit's port is unrouted
    assert not device_has_pump(salt, "algicide")


# ── the three states: value, unknown, not present ───────────────────────────


def test_a_probe_the_unit_lacks_is_not_present() -> None:
    """SALT with a REDOX probe: the model reads free chlorine, this unit has none."""
    salt = AsekoDecoder.decode(bytes(_make_base_bytes()))  # byte[4] = 0x0E, REDOX
    assert "cl_free" in v7.SALT.feature_names
    assert "cl_free" not in salt.features
    assert salt.cl_free is None
    assert "redox" in salt.features
    assert "required_redox" in salt.features
    assert "required_cl_free" not in salt.features


def test_a_setting_unset_on_the_unit_is_not_present() -> None:
    data = _make_base_bytes()
    data[68] = 0xFF  # backwash interval never configured
    data[76:78] = b"\xff\xff"  # max filling time not implemented
    device = AsekoDecoder.decode(bytes(data))
    assert "backwash_every_n_days" not in device.features
    assert "max_filling_time" not in device.features
    assert "backwash_active" in device.features  # the valve itself is there


def test_a_value_unknown_in_this_frame_stays_present() -> None:
    """byte[37] unset: the unit has a schedule, this frame just does not say which."""
    salt = AsekoDecoder.decode(bytes(_make_base_bytes()))  # byte[37] = 0xFF
    assert "filtration_schedule" in salt.features
    assert salt.filtration_schedule is None
    assert "service_menu_open" in salt.features
    assert salt.service_menu_open is None

    home = AsekoDecoder.decode(_home_bytes(0xFF))
    assert "heating_control_enabled" in home.features
    assert home.heating_control_enabled is None
    assert "service_menu_open" not in home.features  # firmware unknown: not guessed


def test_shared_port_routing_decides_which_chemical_is_present() -> None:
    data = _make_base_bytes()
    data[101] = 40
    data[37] = 0x43  # SALT, bit 0x80 clear: shared port routed to flocculant
    device = AsekoDecoder.decode(bytes(data))
    assert "flowrate_floc" in device.features
    assert "floc_pump_running" in device.features
    assert "flowrate_algicide" not in device.features
    assert "algicide_pump_running" not in device.features

    data[37] = 0xC3  # bit 0x80 set: routed to algicide
    device = AsekoDecoder.decode(bytes(data))
    assert "flowrate_algicide" in device.features
    assert "flowrate_floc" not in device.features


def test_v8_sentinel_means_not_present() -> None:
    """v8 cannot tell an absent probe from an unreadable one; both are -500."""
    frame = REFERENCE_FRAME.replace(b"ains: 708 708", b"ains: -500 708")
    device = AsekoV8Decoder.decode(frame)
    assert "ph" not in device.features
    assert device.ph is None
    assert "redox" in device.features
