"""Tests for AsekoV8Decoder."""

import pytest

from custom_components.aseko_local.decoding import decode
from custom_components.aseko_local.decoding.frames import parse_v8
from custom_components.aseko_local.models import (
    AsekoDeviceType,
    AsekoProbeType,
)

# ---------------------------------------------------------------------------
# Real reference frame from fekberg (Sep 16, 2025, 22:27 CEST).
# Used as the primary test fixture — all expected values are cross-validated
# against a second frame (Apr 13, 2026, 12:27 CEST) and Aseko app screenshots.
# ---------------------------------------------------------------------------
REFERENCE_FRAME = (
    b"{v1 123456789 804 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)

REFERENCE_FRAME_805 = (
    b"{v1 123456789 805 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)

REFERENCE_FRAME_812 = (
    b"{v1 123456789 812 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)

# Header type 105 = ASIN Aqua Salt NET. Same body as the 805 reference; only the
# type field differs, to verify 105 decodes to AsekoDeviceType.SALT.
REFERENCE_FRAME_105 = (
    b"{v1 123456789 105 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)

# Second reference frame (Apr 13, 2026, 12:27 CEST) — used as cross-check fixture.
REFERENCE_FRAME_APR = (
    b"{v1 123456789 804 0 27 "
    b"ins: 180 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 25 1 24 12 27 0 "
    b"ains: 649 649 804 8090 0 0 809 809 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 74 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)

# Reference frame for FW 8.05 devices (header type 805).
# Same body layout as REFERENCE_FRAME — only the f2 header value changes.
REFERENCE_FRAME_805 = (
    b"{v1 123456789 805 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)

# Reference frame for FW 8.12 devices (header type 812).
# Same body layout as REFERENCE_FRAME — only the f2 header value changes.
REFERENCE_FRAME_812 = (
    b"{v1 123456789 812 0 27 "
    b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
    b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
    b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
    b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
    b"fncs: 0 0 3 0 0 0 2 0 "
    b"mods: 2 0 0 1 0 0 0 0 "
    b"flags: 2 0 0 0 0 0 0 0 "
    b"crc16: C3C8}\n"
)


@pytest.fixture
def device_sep():
    return decode(REFERENCE_FRAME)


@pytest.fixture
def device_805():
    return decode(REFERENCE_FRAME_805)


@pytest.fixture
def device_812():
    return decode(REFERENCE_FRAME_812)


@pytest.fixture
def device_105():
    return decode(REFERENCE_FRAME_105)


@pytest.fixture
def device_apr():
    return decode(REFERENCE_FRAME_APR)


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_serial_number(device_sep):
    assert device_sep.serial_number == 123456789


def test_device_type_is_net(device_sep):
    assert device_sep.device_type == AsekoDeviceType.NET


def test_device_805_type_is_net(device_805):
    assert device_805.device_type == AsekoDeviceType.NET


def test_device_812_type_is_net(device_812):
    assert device_812.device_type == AsekoDeviceType.NET


def test_device_105_type_is_salt(device_105):
    assert device_105.device_type == AsekoDeviceType.SALT


def test_configuration_contains_ph_and_redox(device_sep):
    assert AsekoProbeType.PH in device_sep.configuration
    assert AsekoProbeType.REDOX in device_sep.configuration


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def test_water_temperature_sep(device_sep):
    assert device_sep.water_temperature == pytest.approx(31.4)


def test_water_temperature_apr(device_apr):
    assert device_apr.water_temperature == pytest.approx(18.0)


def test_ph_sep(device_sep):
    assert device_sep.ph == pytest.approx(7.08)


def test_ph_apr(device_apr):
    assert device_apr.ph == pytest.approx(6.49)


def test_redox_sep(device_sep):
    assert device_sep.redox == 779


def test_redox_apr(device_apr):
    assert device_apr.redox == 809


def test_water_flow_to_probes(device_sep):
    assert device_sep.water_flow_to_probes is True


# ---------------------------------------------------------------------------
# Pump states
# ---------------------------------------------------------------------------


def test_filtration_pump_running(device_sep):
    assert device_sep.filtration_running is True


def test_ph_minus_pump_not_running_baseline(device_sep):
    """Baseline frame has outs[8] == 0 → ph_minus_pump_running is False."""
    assert device_sep.ph_minus_pump_running is False


def test_ph_minus_pump_running_when_dosing():
    """Frame with outs[8] == 1 (pH− dosing event) → ph_minus_pump_running is True."""
    dosing_frame = (
        b"{v1 123456789 804 0 27 "
        b"ins: 180 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 25 1 24 12 27 0 "
        b"ains: 649 649 804 8090 0 0 809 809 0 0 0 0 0 0 0 0 "
        b"outs: 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 "
        b"areqs: 74 74 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
        b"reqs: 0 0 0 0 0 0 0 24 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
        b"0 10 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
        b"fncs: 0 0 3 0 0 0 2 0 "
        b"mods: 2 0 0 1 0 0 0 0 "
        b"flags: 2 0 0 0 0 0 0 0 "
        b"crc16: C3C8}\n"
    )
    device = decode(dosing_frame)
    assert device.ph_minus_pump_running is True
    # Other pump states must be unaffected
    assert device.filtration_running is True


# ---------------------------------------------------------------------------
# Setpoints / configuration
# ---------------------------------------------------------------------------


def test_required_ph_sep(device_sep):
    assert device_sep.ph_target == pytest.approx(7.4)


def test_required_ph_apr(device_apr):
    assert device_apr.ph_target == pytest.approx(7.4)


def test_required_redox_sep(device_sep):
    # areqs[1] = 73 → 73 × 10 = 730 mV
    assert device_sep.redox_target == 730


def test_required_redox_apr(device_apr):
    # areqs[1] = 74 → 74 × 10 = 740 mV  (matches app screenshot)
    assert device_apr.redox_target == 740


def test_pool_volume(device_sep):
    assert device_sep.pool_volume == 45


def test_delay_after_startup(device_sep):
    assert device_sep.startup_delay == 2


def test_delay_after_dose(device_sep):
    assert device_sep.dosing_delay == 2


# ---------------------------------------------------------------------------
# Timestamp
# ---------------------------------------------------------------------------


def test_timestamp_hour_minute(device_sep):
    assert device_sep.timestamp is not None
    assert device_sep.timestamp.hour == 22
    assert device_sep.timestamp.minute == 27


def test_timestamp_hour_minute_apr(device_apr):
    assert device_apr.timestamp is not None
    assert device_apr.timestamp.hour == 12
    assert device_apr.timestamp.minute == 27


# ---------------------------------------------------------------------------
# Absent-probe sentinel (-500 → None)
# ---------------------------------------------------------------------------


def test_absent_probe_returns_none():
    """A frame where all ains are -500 must yield None for ph and redox."""
    frame = (
        b"{v1 999 804 0 27 "
        b"ins: -500 -500 -500 -500 0 0 0 0 0 -500 -500 -500 0 0 0 0 0 0 0 "
        b"ains: -500 -500 -500 -500 0 0 -500 -500 0 0 0 0 0 0 0 0 "
        b"outs: 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
        b"areqs: 74 74 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
        b"crc16: 0000}\n"
    )
    device = decode(frame)
    assert device.ph is None
    assert device.redox is None
    assert device.water_temperature is None
    assert AsekoProbeType.PH not in device.configuration
    assert AsekoProbeType.REDOX not in device.configuration


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_missing_braces_raises():
    with pytest.raises(ValueError, match="braces"):
        parse_v8(b"v1 999999999 804 0 27 ins: 0\n")


def test_bad_header_raises():
    with pytest.raises(ValueError, match="header"):
        parse_v8(b"{not a valid v8 header}\n")


def test_unknown_header_type_is_tolerated(caplog):
    """A header type no product line matches must not raise (PR #119).

    It decodes with the unknown v8 profile -- no model, so no entities --
    and a warning names it; a new firmware of a known line (813, 106) does
    not get here.
    """
    import logging

    with caplog.at_level(
        logging.WARNING, logger="custom_components.aseko_local.decoding.profiles"
    ):
        device = decode(
            b"{v1 123456789 999 0 27 "
            b"ins: 314 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 24 6 29 22 27 0 "
            b"ains: 708 708 774 7790 0 0 779 779 0 0 0 0 0 0 0 0 "
            b"outs: 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
            b"areqs: 74 73 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
            b"crc16: C3C8}\n"
        )
    assert device.device_type is None
    assert device.serial_number == 123456789
    assert device.ph == pytest.approx(7.08)
    # Warning must have been emitted to help diagnose the unknown header in the wild.
    assert any("999" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Pump states — outs[] mapping
# ---------------------------------------------------------------------------


def test_cl_pump_running_false_in_reference_frame(device_sep):
    """Baseline frames have outs[9] = 0 → chlorine_pump_running is False."""
    assert device_sep.chlorine_pump_running is False


def test_cl_pump_running_true_when_outs9_set():
    """Frame with outs[9] = 1 → chlorine_pump_running is True (confirmed April 19 fekberg)."""
    frame = (
        b"{v1 999999999 804 0 27 "
        b"ins: 214 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 25 1 30 18 23 0 "
        b"ains: 740 688 734 7390 0 0 739 739 0 0 0 0 0 0 0 0 "
        b"outs: 0 0 1 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 "
        b"areqs: 74 74 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
        b"crc16: 0000}\n"
    )
    device = decode(frame)
    assert device.chlorine_pump_running is True
    assert device.ph_minus_pump_running is False


def test_ph_minus_pump_running_true_when_outs8_set():
    """Frame with outs[8] = 1 → ph_minus_pump_running is True (confirmed April 15 fekberg)."""
    frame = (
        b"{v1 999999999 804 0 27 "
        b"ins: 183 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 25 1 27 2 14 0 "
        b"ains: 741 689 789 7940 0 0 794 794 0 0 0 0 0 0 0 0 "
        b"outs: 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 "
        b"areqs: 74 74 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
        b"crc16: 0000}\n"
    )
    device = decode(frame)
    assert device.ph_minus_pump_running is True
    assert device.chlorine_pump_running is False


def test_both_pumps_independent():
    """outs[8] and outs[9] are independently decoded."""
    frame = (
        b"{v1 999999999 804 0 27 "
        b"ins: 200 -500 -500 -500 0 0 0 0 1 -500 -500 -500 0 25 1 27 12 0 0 "
        b"ains: 740 688 789 7940 0 0 794 794 0 0 0 0 0 0 0 0 "
        b"outs: 0 0 1 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 "
        b"areqs: 74 74 4 5 0 36 36 0 0 0 6 0 36 0 45 0 255 2 2 10 0 15 0 0 0 0 "
        b"crc16: 0000}\n"
    )
    device = decode(frame)
    assert device.ph_minus_pump_running is True
    assert device.chlorine_pump_running is True


def test_delays_are_minutes_and_the_profile_says_so():
    """R3: areqs[17] / areqs[18] = 2 is "2 min" in the app; kept as 2, flagged as minutes."""
    from custom_components.aseko_local.models import AsekoProfileFlag

    device = decode(REFERENCE_FRAME)
    assert device.startup_delay == 2
    assert device.dosing_delay == 2
    assert AsekoProfileFlag.DELAYS_IN_MINUTES in device.flags
    assert AsekoProfileFlag.DELAYS_IN_MINUTES in decode(REFERENCE_FRAME_105).flags


# ---------------------------------------------------------------------------
# Unreadable values and the profile on the device
# ---------------------------------------------------------------------------


def test_crc16_is_read_as_hex():
    """crc16 is the one hex section; it no longer comes out empty."""
    assert parse_v8(REFERENCE_FRAME).sections["crc16"] == [0xC3C8]
    assert parse_v8(REFERENCE_FRAME).problems == ()


def test_one_unreadable_value_does_not_blank_its_section():
    """A corrupt token reads None and is reported; its neighbours stay."""
    frame = parse_v8(REFERENCE_FRAME.replace(b"ains: 708 ", b"ains: 7x8 "))
    assert frame.sections["ains"][0] is None
    assert frame.sections["ains"][1] == 708
    assert frame.problems == ("ains[0]: '7x8' is not a number",)

    device = decode(REFERENCE_FRAME.replace(b"ains: 708 ", b"ains: 7x8 "))
    assert device.ph is None
    assert device.redox == 779
    assert device.frame_problems == ("ains[0]: '7x8' is not a number",)


def test_device_names_the_profile_that_read_it():
    assert decode(REFERENCE_FRAME).profile == "v8 NET"
    assert decode(REFERENCE_FRAME_105).profile == "v8 SALT"
    unknown = decode(REFERENCE_FRAME.replace(b" 804 ", b" 999 "))
    assert unknown.profile == "v8 unknown header type"


def test_a_header_without_sections_reads_unknown_and_says_so():
    """Nothing to read is not an error, but the missing sections are reported."""
    device = decode(b"{v1 123456789 804 0 27}")
    assert device.profile == "v8 NET"
    assert device.ph is None
    assert device.water_temperature is None
    assert device.chlorine_pump_running is None
    assert device.frame_problems == (
        "section 'ins' is missing",
        "section 'ains' is missing",
        "section 'outs' is missing",
        "section 'areqs' is missing",
    )


def test_a_complete_frame_reports_no_problem():
    assert decode(REFERENCE_FRAME).frame_problems == ()
