"""Support for Meltem ventilation level selection."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VENTILATION_LEVELS,
    VENTILATION_STATUS_REGISTER,
    VENTILATION_VALUE_MAP,
)
from .coordinator import MeltemCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Meltem ventilation level select."""
    coordinator: MeltemCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data["devices"].items():
        entities.append(
            MeltemVentilationLevelSelect(
                coordinator,
                device_id,
                device,
            )
        )

    async_add_entities(entities)


class MeltemVentilationLevelSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Meltem ventilation level select."""

    def __init__(
        self,
        coordinator: MeltemCoordinator,
        device_id: str,
        device_info: dict,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_info = device_info

        # Entity properties
        self._attr_name = "Ventilation Preset"
        self._attr_unique_id = f"{device_id}_ventilation_level"
        self._attr_options = [level.capitalize() for level in VENTILATION_LEVELS.keys()]
        self._attr_icon = "mdi:fan-speed"
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
    def current_option(self) -> str | None:
        """Return the current ventilation level."""
        if not self.coordinator.data or not self.coordinator.data.get("data"):
            return None

        device_data = self.coordinator.data["data"].get(self._device_id, {})
        register_data = device_data.get(VENTILATION_STATUS_REGISTER)

        if not register_data or "value" not in register_data:
            return None

        value = register_data.get("value")
        level = VENTILATION_VALUE_MAP.get(value)
        return level.capitalize() if level else None

    async def async_select_option(self, option: str) -> None:
        """Set the ventilation level."""
        await self.coordinator.async_set_ventilation_level(self._device_id, option.lower())