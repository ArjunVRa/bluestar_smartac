"""Config Flow for Blue Star Smart AC."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_AUTH_ID, CONF_IS_EMAIL, CONF_PASSWORD, DOMAIN
from .hub import BlueStarHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AUTH_ID): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_IS_EMAIL, default=False): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blue Star Smart AC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_id = user_input[CONF_AUTH_ID].strip()
            password = user_input[CONF_PASSWORD].strip()
            is_email = user_input.get(CONF_IS_EMAIL, False)

            hub = BlueStarHub(auth_id, password, is_email)
            success = await self.hass.async_add_executor_job(hub.login)

            if success:
                await self.async_set_unique_id(auth_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Blue Star ({auth_id})",
                    data=user_input,
                )
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
