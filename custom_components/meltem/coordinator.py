"""Data update coordinator for Meltem integration."""
from datetime import timedelta
import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_HOST,
    API_KEY,
    API_AUTH_ENDPOINT,
    API_BRIDGES_ENDPOINT,
    API_BRIDGE_DEVICES_ENDPOINT,
    API_LIVE_DATA_ENDPOINT,
    API_SET_DATA_ENDPOINT,
    USER_AGENT,
    DEFAULT_UPDATE_INTERVAL,
    REGISTER_DEFINITIONS,
    ADDITIONAL_REGISTERS,
    VENTILATION_REGISTER,
    VENTILATION_LEVELS,
    VENTILATION_MANUAL_MIN,
    VENTILATION_MANUAL_MAX,
    VENTILATION_MANUAL_REGISTER,
    calculate_manual_value,
)

_LOGGER = logging.getLogger(__name__)

ALL_REGISTERS = list({
    *REGISTER_DEFINITIONS.keys(),
    *ADDITIONAL_REGISTERS.keys(),
})

class MeltemCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Meltem data."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        session_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Meltem",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self._username = username
        self._password = password
        self._session_id = session_id
        self._session = aiohttp.ClientSession()
        self.bridges = {}
        self.devices = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meltem API."""
        try:
            # First, get the list of bridges
            bridges = await self._fetch_bridges()

            # Then get devices for each bridge
            all_devices = {}
            device_data = {}

            for bridge_id in bridges:
                devices = await self._fetch_devices(bridge_id)
                all_devices.update(devices)

                # Get live data for each device
                for device_id in devices:
                    data = await self._fetch_live_data(device_id)
                    device_data[device_id] = data

            return {
                "bridges": bridges,
                "devices": all_devices,
                "data": device_data,
            }

        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise UpdateFailed(f"Error communicating with API: {error}")

    async def _fetch_bridges(self) -> dict[str, Any]:
        """Fetch list of bridges."""
        headers = self._get_headers()
        params = {
            "apiKey": API_KEY,
            "sessionId": self._session_id,
        }

        async with async_timeout.timeout(10):
            async with self._session.get(
                f"{API_HOST}{API_BRIDGES_ENDPOINT}",
                headers=headers,
                params=params,
            ) as response:
                if response.status == 401:
                    await self._refresh_session()
                    params["sessionId"] = self._session_id
                    async with self._session.get(
                        f"{API_HOST}{API_BRIDGES_ENDPOINT}",
                        headers=headers,
                        params=params,
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                else:
                    response.raise_for_status()
                    data = await response.json()

                bridges = {}
                for bridge in data.get("bridges", []):
                    bridge_id = bridge.get("bridgeId")
                    if bridge_id:
                        bridges[bridge_id] = bridge
                return bridges

    async def _fetch_devices(self, bridge_id: str) -> dict[str, Any]:
        """Fetch devices for a specific bridge."""
        headers = self._get_headers()
        params = {
            "apiKey": API_KEY,
            "sessionId": self._session_id,
            "bridgeId": bridge_id,
        }

        async with async_timeout.timeout(10):
            async with self._session.get(
                f"{API_HOST}{API_BRIDGE_DEVICES_ENDPOINT}",
                headers=headers,
                params=params,
            ) as response:
                if response.status == 401:
                    await self._refresh_session()
                    params["sessionId"] = self._session_id
                    async with self._session.get(
                        f"{API_HOST}{API_BRIDGE_DEVICES_ENDPOINT}",
                        headers=headers,
                        params=params,
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                else:
                    response.raise_for_status()
                    data = await response.json()

                devices = {}
                for device in data.get("devices", []):
                    device_id = device.get("deviceId")
                    if device_id:
                        device["bridge_id"] = bridge_id
                        devices[device_id] = device
                return devices

    async def _fetch_live_data(self, device_id: str) -> dict[str, Any]:
        """Fetch live data for a specific device."""
        headers = self._get_headers()
        params = {
            "apiKey": API_KEY,
            "sessionId": self._session_id,
            "deviceId": device_id,
            "registers": ",".join(str(reg) for reg in ALL_REGISTERS),
        }

        async with async_timeout.timeout(10):
            async with self._session.get(
                f"{API_HOST}{API_LIVE_DATA_ENDPOINT}",
                headers=headers,
                params=params,
            ) as response:
                if response.status == 401:
                    await self._refresh_session()
                    params["sessionId"] = self._session_id
                    async with self._session.get(
                        f"{API_HOST}{API_LIVE_DATA_ENDPOINT}",
                        headers=headers,
                        params=params,
                    ) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                else:
                    response.raise_for_status()
                    data = await response.json()

                formatted_data = {}
                for item in data.get("data", []):
                    address = item.get("address")
                    if address is not None:
                        # Check if the item has a status code
                        if "status" in item:
                            status = item.get("status")
                            _LOGGER.debug(
                                "Register %s returned status code: %s",
                                address,
                                status
                            )
                            # Skip registers with error status codes
                            if status == 1001:
                                continue
                            formatted_data[address] = {
                                "value": None,
                                "status": status,
                                "last_update": item.get("lastUpdate")
                            }
                        else:
                            value = item.get("value")
                            # Handle special values
                            if value == "NaN":
                                _LOGGER.debug(
                                    "Register %s returned NaN value",
                                    address
                                )
                                continue
                            if isinstance(value, (int, float)) and value == 32767:
                                _LOGGER.debug(
                                    "Register %s returned max value (32767), treating as invalid",
                                    address
                                )
                                continue
                            # Check for humidity values above 100%
                            if address in [41002, 41004] and isinstance(value, (int, float)) and value > 100:
                                _LOGGER.debug(
                                    "Register %s returned humidity value above 100%% (%s), treating as invalid",
                                    address,
                                    value
                                )
                                continue
                            formatted_data[address] = {
                                "value": value,
                                "last_update": item.get("lastUpdate")
                            }
                return formatted_data

    def _get_headers(self) -> dict[str, str]:
        """Get common headers for API requests."""
        return {
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }

    async def _refresh_session(self) -> None:
        """Refresh the session ID by re-authenticating."""
        async with self._session.post(
            f"{API_HOST}{API_AUTH_ENDPOINT}",
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            },
            data={
                "apiKey": API_KEY,
                "username": self._username,
                "password": self._password,
            },
        ) as response:
            response.raise_for_status()
            data = await response.json()
            self._session_id = data["sessionId"]

    async def async_refresh_device(self, device_id: str) -> None:
        """Refresh live data for a specific device."""
        try:
            data = await self._fetch_live_data(device_id)
            self.data["data"][device_id] = data
            self.async_set_updated_data(self.data)
        except Exception as error:
            _LOGGER.error("Error refreshing device %s: %s", device_id, error)

    async def async_set_ventilation_level(self, device_id: str, level: str) -> None:
        """Set the ventilation level for a device."""
        if level not in VENTILATION_LEVELS:
            raise ValueError(f"Invalid ventilation level: {level}")

        max_retries = 100
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                headers = {
                    **self._get_headers(),
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                }
                params = {
                    "apiKey": API_KEY,
                    "sessionId": self._session_id,
                    "deviceId": device_id,
                    "register": VENTILATION_REGISTER,
                    "values": ",".join(str(v) for v in VENTILATION_LEVELS[level]),
                }

                async with async_timeout.timeout(10):
                    async with self._session.post(
                        f"{API_HOST}{API_SET_DATA_ENDPOINT}",
                        headers=headers,
                        data=params,
                    ) as response:
                        if response.status == 401:
                            await self._refresh_session()
                            params["sessionId"] = self._session_id
                            async with self._session.post(
                                f"{API_HOST}{API_SET_DATA_ENDPOINT}",
                                headers=headers,
                                data=params,
                            ) as retry_response:
                                retry_response.raise_for_status()
                        else:
                            response.raise_for_status()

                        # If we get here, the request was successful
                        # If switching to manual mode, set an initial speed
                        if level == "manual":
                            _LOGGER.debug("Setting initial manual speed to minimum value")
                            await self.async_set_manual_speed(device_id, VENTILATION_MANUAL_MIN)
                        else:
                            # Refresh live data for this device
                            await self.async_refresh_device(device_id)

                        # Success - exit the retry loop
                        return

            except (aiohttp.ClientError, asyncio.TimeoutError) as error:
                last_error = error
                retry_count += 1
                if retry_count < max_retries:
                    _LOGGER.warning(
                        "Failed to set ventilation level (attempt %d/%d): %s. Retrying in 2 seconds...",
                        retry_count,
                        max_retries,
                        error
                    )
                    await asyncio.sleep(2)
                continue

        # If we get here, all retries failed
        raise UpdateFailed(f"Error setting ventilation level after {max_retries} attempts: {last_error}")

    async def async_set_manual_speed(self, device_id: str, percentage: int) -> None:
        """Set the manual ventilation speed for a device."""
        if not VENTILATION_MANUAL_MIN <= percentage <= VENTILATION_MANUAL_MAX:
            raise ValueError(
                f"Invalid ventilation speed percentage. Must be between "
                f"{VENTILATION_MANUAL_MIN} and {VENTILATION_MANUAL_MAX}"
            )

        try:
            headers = {
                **self._get_headers(),
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            }
            value = calculate_manual_value(percentage)
            params = {
                "apiKey": API_KEY,
                "sessionId": self._session_id,
                "deviceId": device_id,
                "register": VENTILATION_MANUAL_REGISTER,
                "values": str(value),
            }

            async with async_timeout.timeout(10):
                async with self._session.post(
                    f"{API_HOST}{API_SET_DATA_ENDPOINT}",
                    headers=headers,
                    data=params,
                ) as response:
                    if response.status == 401:
                        await self._refresh_session()
                        params["sessionId"] = self._session_id
                        async with self._session.post(
                            f"{API_HOST}{API_SET_DATA_ENDPOINT}",
                            headers=headers,
                            data=params,
                        ) as retry_response:
                            retry_response.raise_for_status()
                    else:
                        response.raise_for_status()

                    # Refresh live data for this device
                    await self.async_refresh_device(device_id)

        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise UpdateFailed(f"Error setting manual ventilation speed: {error}")

    async def async_close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()