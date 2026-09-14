"""The committed support matrix must match the profiles it is generated from."""

from __future__ import annotations

from pathlib import Path

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
