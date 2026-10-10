"""Setup and entry point for Blue Star Smart AC integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_AUTH_ID, CONF_IS_EMAIL, CONF_PASSWORD, DOMAIN
from .hub import BlueStarHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SWITCH,
]

SCAN_INTERVAL = timedelta(seconds=30)


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

    # Periodic background refresh to guarantee fresh temperature readings even if AC is quiet
    async def _async_poll_devices(now=None) -> None:
        await hass.async_add_executor_job(hub.fetch_devices)

    unsub_interval = async_track_time_interval(hass, _async_poll_devices, SCAN_INTERVAL)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "hub": hub,
        "unsub_interval": unsub_interval,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        if unsub := entry_data.get("unsub_interval"):
            unsub()
        hub: BlueStarHub = entry_data["hub"]
        if hub.aws_mqtt_conn:
            try:
                hub.aws_mqtt_conn.disconnect()
            except Exception:
                pass
    return unload_ok
