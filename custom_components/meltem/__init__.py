"""The Meltem integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_SESSION_ID
from .coordinator import MeltemCoordinator
from .device import async_setup_devices

PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.NUMBER, Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meltem from a config entry."""
    coordinator = MeltemCoordinator(
        hass,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session_id=entry.data[CONF_SESSION_ID],
    )

    # Get initial data
    await coordinator.async_config_entry_first_refresh()

    # Set up devices in registry
    async_setup_devices(
        hass,
        entry.entry_id,
        coordinator.data["bridges"],
        coordinator.data["devices"],
    )

    # Store coordinator for platforms to access
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
    return unload_ok