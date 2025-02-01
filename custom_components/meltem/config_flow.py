"""Config flow for Meltem integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    API_HOST,
    API_KEY,
    API_AUTH_ENDPOINT,
    USER_AGENT,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    CONF_SESSION_ID,
)

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meltem."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                _LOGGER.debug("Creating aiohttp session for authentication")
                session = aiohttp.ClientSession()

                headers = {
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "X-API-KEY": API_KEY,
                    "User-Agent": USER_AGENT,
                    "Accept": "*/*",
                    "Accept-Language": "en-GB,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                }

                data = {
                    "username": user_input[CONF_USERNAME],
                    "password": user_input[CONF_PASSWORD],
                    "apiKey": API_KEY,
                }

                auth_url = f"{API_HOST}{API_AUTH_ENDPOINT}"
                _LOGGER.debug("Attempting authentication to %s with headers: %s", auth_url, headers)

                # Authenticate with username and password
                auth_response = await session.post(
                    auth_url,
                    headers=headers,
                    data=data,
                )

                _LOGGER.debug("Authentication response status: %s", auth_response.status)

                try:
                    response_text = await auth_response.text()
                    _LOGGER.debug("Authentication response body: %s", response_text)
                except Exception as e:
                    _LOGGER.error("Failed to read response body: %s", e)
                    response_text = "Unable to read response"

                if auth_response.status == 200:
                    try:
                        auth_data = await auth_response.json()
                        _LOGGER.debug("Authentication successful, received data: %s", auth_data)
                        session_id = auth_data.get("sessionId")

                        if session_id:
                            await session.close()
                            _LOGGER.info("Successfully authenticated user: %s", user_input[CONF_USERNAME])
                            return self.async_create_entry(
                                title=f"Meltem ({user_input[CONF_USERNAME]})",
                                data={
                                    CONF_USERNAME: user_input[CONF_USERNAME],
                                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                                    CONF_SESSION_ID: session_id,
                                },
                            )
                        _LOGGER.error("Authentication response missing sessionId")
                        errors["base"] = ERROR_INVALID_AUTH
                    except Exception as e:
                        _LOGGER.error("Failed to parse authentication response: %s", e)
                        errors["base"] = ERROR_CANNOT_CONNECT
                elif auth_response.status == 401:
                    _LOGGER.error("Authentication failed: Invalid credentials")
                    errors["base"] = ERROR_INVALID_AUTH
                else:
                    _LOGGER.error(
                        "Authentication failed with status %s: %s",
                        auth_response.status,
                        response_text
                    )
                    errors["base"] = ERROR_CANNOT_CONNECT

                await session.close()
                _LOGGER.debug("Closed aiohttp session")

            except aiohttp.ClientError as e:
                _LOGGER.error("Connection error during authentication: %s", e)
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during authentication: %s", e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )