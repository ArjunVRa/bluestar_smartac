"""Switch platform for Blue Star Smart AC."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import BlueStarHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Star switch entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    hub: BlueStarHub = entry_data["hub"] if isinstance(entry_data, dict) else entry_data
    entities = []
    for tid, info in hub.devices.items():
        entities.append(BlueStarDisplaySwitch(hub, tid, info))
        entities.append(BlueStarTurboSwitch(hub, tid, info))
        entities.append(BlueStarBuzzerSwitch(hub, tid, info))
        entities.append(BlueStarHorizontalSwingSwitch(hub, tid, info))
        entities.append(BlueStarEcoSwitch(hub, tid, info))
    async_add_entities(entities)


class _BaseBlueStarSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        self.hub = hub
        self.thing_id = thing_id
        self._device_info = device_info

    async def async_added_to_hass(self) -> None:
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


class BlueStarDisplaySwitch(_BaseBlueStarSwitch):
    _attr_name = "LED Display"
    _attr_icon = "mdi:led-on"

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_display"

    @property
    def is_on(self) -> bool:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        return st.get("display", 1) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"display": 1, "lcmd": "display"}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"display": 0, "lcmd": "display"}
        )


class BlueStarTurboSwitch(_BaseBlueStarSwitch):
    _attr_name = "Turbo Mode"
    _attr_icon = "mdi:turbine"

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_turbo"

    @property
    def is_on(self) -> bool:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        return st.get("turbo", 0) != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"turbo": 3, "lcmd": "turbo"}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"turbo": 0, "lcmd": "turbo"}
        )


class BlueStarBuzzerSwitch(_BaseBlueStarSwitch):
    _attr_name = "Buzzer Beep"
    _attr_icon = "mdi:volume-high"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_buzzer"

    @property
    def is_on(self) -> bool:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        return st.get("m_buz", 1) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"m_buz": 1, "lcmd": "m_buz"}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"m_buz": 0, "lcmd": "m_buz"}
        )


class BlueStarHorizontalSwingSwitch(_BaseBlueStarSwitch):
    _attr_name = "Horizontal Swing"
    _attr_icon = "mdi:arrow-left-right"

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_hswing"

    @property
    def is_on(self) -> bool:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        return st.get("hswing", 0) != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"hswing": 6, "lcmd": "hswing"}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.hub.send_command, self.thing_id, {"hswing": 0, "lcmd": "hswing"}
        )


class BlueStarEcoSwitch(_BaseBlueStarSwitch):
    _attr_name = "Eco Mode"
    _attr_icon = "mdi:leaf"

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_eco"

    @property
    def is_on(self) -> bool:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        eco_raw = st.get("eco", 0)
        eco_val = eco_raw.get("value", 0) if isinstance(eco_raw, dict) else eco_raw
        return eco_val != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        current_fspd = st.get("fspd", 3)
        await self.hass.async_add_executor_job(
            self.hub.send_command,
            self.thing_id,
            {"eco": {"value": 1, "fspd": current_fspd}, "lcmd": "eco"},
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        current_fspd = st.get("fspd", 3)
        await self.hass.async_add_executor_job(
            self.hub.send_command,
            self.thing_id,
            {"eco": {"value": 0, "fspd": current_fspd}, "lcmd": "eco"},
        )

