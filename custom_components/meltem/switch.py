"""Support for Meltem ventilation on/off control."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VENTILATION_STATUS_REGISTER,
)
from .coordinator import MeltemCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Meltem ventilation switch."""
    coordinator: MeltemCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data["devices"].items():
        entities.append(
            MeltemVentilationSwitch(
                coordinator,
                device_id,
                device,
            )
        )

    async_add_entities(entities)


class MeltemVentilationSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Meltem ventilation on/off switch."""

    def __init__(
        self,
        coordinator: MeltemCoordinator,
        device_id: str,
        device_info: dict,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_info = device_info

        # Entity properties
        self._attr_name = "Power"
        self._attr_unique_id = f"{device_id}_power"
        self._attr_icon = "mdi:power"
        self._attr_has_entity_name = True
        self._attr_should_poll = False

        # Link to device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_info.get("name", "Meltem Ventilation"),
            "manufacturer": "Meltem",
            "model": f"Ventilation Unit ({device_info.get('productId', 'Unknown')})",
            "via_device": (DOMAIN, device_info.get("bridge_id")) if device_info.get("bridge_id") else None,
        }

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if not self.coordinator.data or not self.coordinator.data.get("data"):
            return None

        device_data = self.coordinator.data["data"].get(self._device_id, {})
        status_data = device_data.get(VENTILATION_STATUS_REGISTER)

        if not status_data or "value" not in status_data:
            return None

        return status_data.get("value") != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        # If device was previously in manual mode, restore it to manual mode
        device_data = self.coordinator.data["data"].get(self._device_id, {})
        status_data = device_data.get(VENTILATION_STATUS_REGISTER)

        if status_data and status_data.get("value") == 112:
            # Restore manual mode
            await self.coordinator.async_set_ventilation_level(self._device_id, "manual")
        else:
            # Default to low speed when turning on
            await self.coordinator.async_set_ventilation_level(self._device_id, "low")

        # Refresh live data for this device
        await self.coordinator.async_refresh_device(self._device_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.async_set_ventilation_level(self._device_id, "off")
        # Refresh live data for this device
        await self.coordinator.async_refresh_device(self._device_id)