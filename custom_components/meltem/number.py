"""Support for Meltem manual ventilation speed control."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VENTILATION_MANUAL_MIN,
    VENTILATION_MANUAL_MAX,
    VENTILATION_SPEED_REGISTER,
    VENTILATION_STATUS_REGISTER,
)
from .coordinator import MeltemCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Meltem manual ventilation speed control."""
    coordinator: MeltemCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data["devices"].items():
        entities.append(
            MeltemManualSpeedControl(
                coordinator,
                device_id,
                device,
            )
        )

    async_add_entities(entities)


class MeltemManualSpeedControl(CoordinatorEntity, NumberEntity):
    """Representation of a Meltem manual ventilation speed control."""

    def __init__(
        self,
        coordinator: MeltemCoordinator,
        device_id: str,
        device_info: dict,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_info = device_info

        # Entity properties
        self._attr_name = "Ventilation Speed"
        self._attr_unique_id = f"{device_id}_ventilation_speed"
        self._attr_native_min_value = float(VENTILATION_MANUAL_MIN)
        self._attr_native_max_value = float(VENTILATION_MANUAL_MAX)
        self._attr_native_step = 1.0
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:fan-speed-3"
        self._attr_native_unit_of_measurement = "%"
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
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        device_data = self.coordinator.data["data"].get(self._device_id, {})
        status_data = device_data.get(VENTILATION_STATUS_REGISTER)

        if not status_data or "value" not in status_data:
            return False

        # Available as long as we have valid status data
        return True

    @property
    def native_value(self) -> float | None:
        """Return the current ventilation speed percentage."""
        if not self.coordinator.data or not self.coordinator.data.get("data"):
            return None

        device_data = self.coordinator.data["data"].get(self._device_id, {})
        speed_data = device_data.get(VENTILATION_SPEED_REGISTER)

        if not speed_data or "value" not in speed_data:
            return None

        value = speed_data.get("value")

        # Convert register value to percentage
        if value == 0:
            return 0
        return round(value * 100 / 41385)

    async def async_set_native_value(self, value: float) -> None:
        """Set the manual speed percentage."""
        await self.coordinator.async_set_manual_speed(self._device_id, int(value))