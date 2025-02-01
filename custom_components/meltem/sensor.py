"""Support for Meltem sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REGISTER_DEFINITIONS,
    ADDITIONAL_REGISTERS,
    convert_voc_ppm_to_ugm3,
)
from .coordinator import MeltemCoordinator

_LOGGER = logging.getLogger(__name__)
ALL_REGISTERS = {**REGISTER_DEFINITIONS, **ADDITIONAL_REGISTERS}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Meltem sensors."""
    coordinator: MeltemCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create entities for each device and register
    for device_id, device in coordinator.data["devices"].items():
        for register_id, register_info in ALL_REGISTERS.items():
            if register_id in coordinator.data["data"].get(device_id, {}):
                try:
                    # Convert entity_category string to enum if present
                    if "entity_category" in register_info:
                        if register_info["entity_category"] == "diagnostic":
                            register_info["entity_category"] = EntityCategory.DIAGNOSTIC
                        elif register_info["entity_category"] == "config":
                            register_info["entity_category"] = EntityCategory.CONFIG

                    entities.append(
                        MeltemSensor(
                            coordinator,
                            device_id,
                            register_id,
                            register_info,
                            device,
                        )
                    )
                except ValueError as err:
                    _LOGGER.error(
                        "Error creating sensor for register %s: %s",
                        register_id,
                        err
                    )
                    continue

    if not entities:
        _LOGGER.warning(
            "No valid sensors were created for device(s): %s",
            ", ".join(coordinator.data["devices"].keys())
        )
        return

    async_add_entities(entities)


class MeltemSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Meltem sensor."""

    def __init__(
        self,
        coordinator: MeltemCoordinator,
        device_id: str,
        register_id: int,
        register_info: dict,
        device: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        # Validate required attributes
        if not register_info.get("name"):
            raise ValueError(f"Register {register_id} is missing required name attribute")

        self._device_id = device_id
        self._register_id = register_id
        self._register_info = register_info
        self._device = device

        # Entity properties
        self._attr_name = register_info["name"]
        self._attr_unique_id = f"{device_id}_{register_id}"
        self._attr_native_unit_of_measurement = register_info.get("unit")
        self._attr_device_class = register_info.get("device_class")
        self._attr_state_class = register_info.get("state_class")
        self._attr_icon = register_info.get("icon")
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_entity_registry_enabled_default = register_info.get("entity_registry_enabled_default", True)
        self._attr_entity_category = register_info.get("entity_category")
        self._attr_suggested_display_precision = register_info.get("suggested_display_precision")

        # Link to device
        device_name = device.get("name")
        if not device_name:
            device_name = "Meltem Ventilation"
            _LOGGER.warning(
                "Device %s is missing name attribute, using default: %s",
                device_id,
                device_name
            )

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Meltem",
            "model": f"Ventilation Unit ({device.get('productId', 'Unknown')})",
            "via_device": (DOMAIN, device.get("bridge_id")) if device.get("bridge_id") else None,
        }

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("data"):
            _LOGGER.debug(
                "No data available for sensor %s (register %s)",
                self._attr_name,
                self._register_id,
            )
            return None

        device_data = self.coordinator.data["data"].get(self._device_id, {})
        register_data = device_data.get(self._register_id)

        _LOGGER.debug(
            "Raw data for sensor %s (register %s): %s",
            self._attr_name,
            self._register_id,
            register_data,
        )

        if not register_data or "value" not in register_data:
            return None

        value = register_data["value"]

        # Check for error values
        if value == 1001:
            _LOGGER.warning(
                "Received error value 1001 for sensor %s (register %s). This might indicate a communication error or invalid reading.",
                self._attr_name,
                self._register_id,
            )
            return None

        # Convert VOC values from ppm to µg/m³
        if (
            self._register_id == 41013  # Supply Air VOC register
            and self._attr_device_class == "volatile_organic_compounds"
            and isinstance(value, (int, float))
        ):
            converted_value = convert_voc_ppm_to_ugm3(float(value))
            _LOGGER.debug(
                "Converted VOC value for sensor %s: %s ppm -> %s µg/m³",
                self._attr_name,
                value,
                converted_value,
            )
            return converted_value

        # Handle value mapping if defined
        if "value_map" in self._register_info:
            mapped_value = self._register_info["value_map"].get(value, value)
            _LOGGER.debug(
                "Mapped value for sensor %s: %s -> %s",
                self._attr_name,
                value,
                mapped_value,
            )
            return mapped_value

        # Handle value transformation if defined
        if "value_transform" in self._register_info and callable(self._register_info["value_transform"]):
            transformed_value = self._register_info["value_transform"](value)
            _LOGGER.debug(
                "Transformed value for sensor %s: %s -> %s",
                self._attr_name,
                value,
                transformed_value,
            )
            return transformed_value

        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        device_data = self.coordinator.data["data"].get(self._device_id, {})
        register_data = device_data.get(self._register_id)

        if not register_data:
            return False

        value = register_data.get("value")

        # Consider the entity unavailable if the value is NaN or 1001
        if value in ["NaN", 1001]:
            _LOGGER.debug(
                "Sensor %s (register %s) is unavailable due to value: %s",
                self._attr_name,
                self._register_id,
                value,
            )
            return False

        return True