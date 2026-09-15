"""The config entries of this integration that are set up and running.

Shared by the domain services and the recording views: both act on every
running entry, and an entry whose set-up has not finished (or failed) has
no runtime data to act on.  A module of its own so the views need not import
the package ``__init__``, which imports them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import AsekoLocalConfigEntry


def loaded_entries(hass: HomeAssistant) -> list[AsekoLocalConfigEntry]:
    """Return every Aseko Local entry whose runtime data is in place."""
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if getattr(entry, "runtime_data", None)
    ]
