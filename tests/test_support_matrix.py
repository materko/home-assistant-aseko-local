"""The committed support matrix must match the profiles it is generated from."""

from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.aseko_local.decoding.support_matrix import render

MATRIX = Path(__file__).resolve().parent.parent / "docs" / "support_matrix.md"


def test_support_matrix_is_up_to_date() -> None:
    """Regenerate with ``python scripts/generate_support_matrix.py``."""
    assert MATRIX.read_text(encoding="utf-8") == render()


def test_every_profile_and_field_is_in_the_matrix() -> None:
    text = render()
    from custom_components.aseko_local.decoding.features import ALL_FEATURES
    from custom_components.aseko_local.decoding.profiles import ALL_PROFILES

    for profile in ALL_PROFILES:
        assert profile.name.split(" ", 1)[1] in text
    for feature in ALL_FEATURES:
        assert f"`{feature.field}`" in text


def _status_for(evidence: str, profile_name: str = "v7 SALT") -> str:
    from custom_components.aseko_local.decoding import support_matrix
    from custom_components.aseko_local.decoding.features import SerialNumber
    from custom_components.aseko_local.decoding.frames import Protocol
    from custom_components.aseko_local.decoding.profile import Profile
    from custom_components.aseko_local.models import AsekoDeviceType

    model = (
        AsekoDeviceType.SALT if profile_name.endswith("SALT") else AsekoDeviceType.HOME
    )
    profile = Profile(
        name=profile_name,
        protocol=Protocol.V7,
        model=model,
        features=(SerialNumber,),
        evidence={SerialNumber: evidence},
    )
    return support_matrix._status(profile, SerialNumber)  # noqa: SLF001


@pytest.mark.parametrize(
    ("evidence", "profile_name", "mark"),
    [
        ("confirmed: against the unit", "v7 SALT", "✅"),
        ("derived: from confirmed values", "v7 SALT", "✅"),
        ("confirmed on SALT: byte[14]", "v7 SALT", "✅"),
        ("confirmed on HOME: byte[14]", "v7 SALT", "❓"),  # another model's proof
        ("confirmed on HOME: byte[14]", "v7 HOME", "✅"),
        ("confirmed on NET, HOME: byte[14]", "v7 HOME", "✅"),
        ("observed: plausible in 28 frames", "v7 SALT", "👁"),
        ("assumed: as on OXY", "v7 SALT", "❓"),
        ("", "v7 SALT", "❓"),
    ],
)
def test_evidence_words_decide_the_mark(evidence, profile_name, mark) -> None:
    """docs/evidence-rules.md: a confirmation counts only for the model it names."""
    assert _status_for(evidence, profile_name) == mark
