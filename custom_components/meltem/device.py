"""Device management for Meltem integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, DEVICE_TYPE_BRIDGE, DEVICE_TYPE_VENTILATION


def async_setup_devices(
    hass: HomeAssistant,
    entry_id: str,
    bridges: dict,
    devices: dict,
) -> None:
    """Set up Meltem bridges and devices in the device registry."""
    device_registry = dr.async_get(hass)

    # Register bridges
    for bridge_id, bridge in bridges.items():
        device_registry.async_get_or_create(
            config_entry_id=entry_id,
            identifiers={(DOMAIN, bridge_id)},
            name=bridge.get("name", "Meltem Bridge"),
            manufacturer="Meltem",
            model="Bridge",
            sw_version=bridge.get("firmwareVersion"),
        )

    # Register ventilation units
    for device_id, device in devices.items():
        bridge_id = device.get("bridge_id")
        device_registry.async_get_or_create(
            config_entry_id=entry_id,
            identifiers={(DOMAIN, device_id)},
            name=device.get("name", "Meltem Ventilation"),
            manufacturer="Meltem",
            model=f"Ventilation Unit ({device.get('productId', 'Unknown')})",
            suggested_area=device.get("zoneId"),
            via_device=(DOMAIN, bridge_id) if bridge_id else None,
        )