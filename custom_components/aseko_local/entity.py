"""Aseko Local Entity.

Every quantity a model can have gets an entity, whether this unit has shown
it or not, so an accessory fitted later (a level sensor, an air probe, the
shared pump port routed to the other chemical) does not need a new set-up
and one removed later does not lose its history:

* an entity for a quantity the unit has not shown since Home Assistant
  started is created **disabled**; when the quantity first arrives the
  platform enables it, and Home Assistant reloads the entry to add it;
* an enabled entity whose quantity the last frame did not show present is
  **unavailable** -- the accessory is not fitted (any more), the port is
  routed elsewhere, or the frame could not say.  The diagnostics download
  lists those fields under ``not_present_now``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AsekoLocalDataUpdateCoordinator
from .models import AsekoDevice

# ``feature`` left at this default is read off the entity description.
_FROM_DESCRIPTION = object()


class AsekoLocalEntity(CoordinatorEntity[AsekoLocalDataUpdateCoordinator]):
    """Representation of an Aseko Local Entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unit: AsekoDevice,
        coordinator: AsekoLocalDataUpdateCoordinator,
        description: EntityDescription,
        feature: str | None | object = _FROM_DESCRIPTION,
    ) -> None:
        """Initialize the Aseko Local Entity.

        ``feature`` is the AsekoDevice field the entity stands for (None: one
        every unit has); by default the description's ``feature``.
        """

        super().__init__(coordinator)

        self.entity_description = description
        self._feature: str | None = (
            getattr(description, "feature", None)
            if feature is _FROM_DESCRIPTION
            else feature  # type: ignore[assignment]
        )

        self.device = unit
        self._attr_unique_id = (
            f"{self.device.serial_number}{self.entity_description.key}"
        )
        # Disabled until the unit shows the quantity; see the module docstring.
        self._attr_entity_registry_enabled_default = (
            self._feature is None or self._feature in unit.features
        )
        model = (
            self.device.device_type.value
            if self.device.device_type is not None
            else None
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.device.serial_number))},
            serial_number=str(self.device.serial_number),
            name=f"{MANUFACTURER} {model} - {self.device.serial_number}",
            manufacturer=MANUFACTURER,
            model=model,
            configuration_url=f"https://aseko.cloud/unit/{self.device.serial_number}",
        )

    @property
    def feature(self) -> str | None:
        """The AsekoDevice field this entity stands for, if any."""
        return self._feature

    @property
    def available(self) -> bool:
        """Unavailable while the coordinator is, or the quantity is not present now."""
        if not super().available:
            return False
        return self._feature is None or self._feature in self.device.present_features


@callback
def async_enable_entities(
    hass: HomeAssistant, platform: str, unique_ids: Iterable[str]
) -> None:
    """Enable entities this integration created disabled, now that their quantity arrived.

    Only entities disabled by the integration are touched -- one a user
    disabled stays disabled.  Home Assistant reloads the entry shortly after
    an entity is enabled, which is what adds it.
    """
    registry = er.async_get(hass)
    for unique_id in unique_ids:
        entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if entity_id is None:
            continue
        entry = registry.async_get(entity_id)
        if (
            entry is not None
            and entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        ):
            registry.async_update_entity(entity_id, disabled_by=None)


def enabled_unique_ids(entities: Iterable[Any]) -> list[str]:
    """Return the unique ids of the entities this unit's features enable by default."""
    return [
        e.unique_id
        for e in entities
        if e.unique_id and getattr(e, "entity_registry_enabled_default", True)
    ]
