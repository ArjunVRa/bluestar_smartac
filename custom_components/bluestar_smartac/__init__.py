"""Setup and entry point for Blue Star Smart AC integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_AUTH_ID, CONF_IS_EMAIL, CONF_PASSWORD, DOMAIN
from .hub import BlueStarHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blue Star Smart AC from a config entry."""
    auth_id = entry.data[CONF_AUTH_ID]
    password = entry.data[CONF_PASSWORD]
    is_email = entry.data.get(CONF_IS_EMAIL, False)

    hub = BlueStarHub(auth_id, password, is_email)

    success = await hass.async_add_executor_job(hub.login)
    if not success:
        _LOGGER.error("Failed to login to Blue Star Cloud")
        return False

    await hass.async_add_executor_job(hub.fetch_devices)
    await hass.async_add_executor_job(hub.init_aws_mqtt)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hub: BlueStarHub = hass.data[DOMAIN].pop(entry.entry_id)
        if hub.aws_mqtt_conn:
            try:
                hub.aws_mqtt_conn.disconnect()
            except Exception:
                pass
    return unload_ok
