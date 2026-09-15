"""Which entries the services and the recording views act on (audit D3)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.aseko_local.runtime import loaded_entries


def _entry(state: ConfigEntryState, *, runtime_data: object = True) -> MagicMock:
    entry = MagicMock()
    entry.state = state
    entry.runtime_data = runtime_data
    return entry


@pytest.mark.parametrize(
    "state",
    [
        ConfigEntryState.SETUP_IN_PROGRESS,
        ConfigEntryState.SETUP_RETRY,
        ConfigEntryState.SETUP_ERROR,
        ConfigEntryState.NOT_LOADED,
    ],
)
def test_an_entry_not_loaded_is_skipped_even_with_runtime_data(state) -> None:
    """runtime_data is set early in the set-up and stays for a retry."""
    hass = MagicMock()
    loaded = _entry(ConfigEntryState.LOADED)
    hass.config_entries.async_entries.return_value = [_entry(state), loaded]

    assert loaded_entries(hass) == [loaded]


def test_a_loaded_entry_without_runtime_data_is_skipped() -> None:
    hass = MagicMock()
    hass.config_entries.async_entries.return_value = [
        _entry(ConfigEntryState.LOADED, runtime_data=None)
    ]

    assert loaded_entries(hass) == []
