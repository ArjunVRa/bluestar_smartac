"""Climate platform for Blue Star Smart AC."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BS_TO_HA_FAN, BS_TO_HA_MODE, DOMAIN, HA_TO_BS_FAN, HA_TO_BS_MODE
from .hub import BlueStarHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Star climate entities from config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    hub: BlueStarHub = entry_data["hub"] if isinstance(entry_data, dict) else entry_data
    entities = []
    for tid, info in hub.devices.items():
        entities.append(BlueStarClimate(hub, tid, info))
    async_add_entities(entities)


class BlueStarClimate(ClimateEntity):
    """Representation of a Blue Star Air Conditioner."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 30.0
    _attr_target_temperature_step = 1.0
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
    ]
    _attr_fan_modes = ["auto", "low", "medium", "high", "turbo"]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        self.hub = hub
        self.thing_id = thing_id
        self._device_info = device_info
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_climate"

    async def async_added_to_hass(self) -> None:
        """Register listener for real-time telemetry updates."""
        def _update(thing_id: str):
            if thing_id == self.thing_id:
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

        self.hub.register_listener(_update)

    @property
    def device_info(self) -> DeviceInfo:
        name = self._device_info.get("name") or f"AC-{self.thing_id[-4:]}"
        return DeviceInfo(
            identifiers={(DOMAIN, self.thing_id)},
            name=name.strip(),
            manufacturer="Blue Star",
            model="Inverter Smart AC",
            sw_version=self._device_info.get("version", "v0.5.7"),
        )

    @property
    def available(self) -> bool:
        st = self.hub.cached_states.get(self.thing_id, {})
        return st.get("connected", True)

    @property
    def hvac_mode(self) -> HVACMode:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        if st.get("pow", 0) == 0:
            return HVACMode.OFF
        mode_val = st.get("mode", 2)
        ha_m = BS_TO_HA_MODE.get(mode_val, "cool")
        return HVACMode(ha_m)

    @property
    def current_temperature(self) -> float | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        try:
            return float(st.get("ctemp", 25.0))
        except (ValueError, TypeError):
            return None

    @property
    def target_temperature(self) -> float | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        try:
            return float(st.get("stemp", 24.0))
        except (ValueError, TypeError):
            return None

    @property
    def fan_mode(self) -> str | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        fspd = st.get("fspd", 7)
        return BS_TO_HA_FAN.get(fspd, "auto")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode with exact firmware constraints."""
        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(
                self.hub.send_command, self.thing_id, {"pow": 0, "lcmd": "pow"}
            )
            return

        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        current_stemp = str(st.get("stemp", "24.0"))
        current_fspd = st.get("fspd", 7)

        pow_v, mode_v = HA_TO_BS_MODE.get(hvac_mode.value, (1, 2))
        fspd_v = current_fspd
        if mode_v == 3:  # Dry requires fan speed 2
            fspd_v = 2
        elif mode_v == 4:  # Auto requires fan speed 7
            fspd_v = 7

        mode_obj = {
            "value": mode_v,
            "stemp": current_stemp,
            "fspd": fspd_v,
        }
        await self.hass.async_add_executor_job(
            self.hub.send_command,
            self.thing_id,
            {"pow": 1, "mode": mode_obj, "lcmd": "mode"},
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get("temperature")
        if temp is None:
            return
        await self.hass.async_add_executor_job(
            self.hub.send_command,
            self.thing_id,
            {"stemp": f"{float(temp):.1f}", "lcmd": "stemp"},
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        fspd = HA_TO_BS_FAN.get(fan_mode, 7)
        await self.hass.async_add_executor_job(
            self.hub.send_command,
            self.thing_id,
            {"fspd": fspd, "lcmd": "fspd"},
        )

    async def async_turn_on(self) -> None:
        """Turn on AC in cool mode."""
        await self.async_set_hvac_mode(HVACMode.COOL)

    async def async_turn_off(self) -> None:
        """Turn off AC."""
        await self.async_set_hvac_mode(HVACMode.OFF)
