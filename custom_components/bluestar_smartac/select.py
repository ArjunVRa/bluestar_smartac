"""Select platform for Blue Star Smart AC."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BS_TO_ECO, DOMAIN, ECO_OPTIONS, ECO_TO_BS
from .hub import BlueStarHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Star select entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    hub: BlueStarHub = entry_data["hub"] if isinstance(entry_data, dict) else entry_data
    entities = []
    for tid, info in hub.devices.items():
        entities.append(BlueStarEcoSelect(hub, tid, info))
    async_add_entities(entities)


class BlueStarEcoSelect(SelectEntity):
    """Select entity for 5-in-1 / 6-in-1 Convertible Eco Capacity modes."""

    _attr_has_entity_name = True
    _attr_name = "Eco Capacity Mode"
    _attr_icon = "mdi:leaf"
    _attr_options = ECO_OPTIONS

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        self.hub = hub
        self.thing_id = thing_id
        self._device_info = device_info
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_eco_select"

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

    @property
    def current_option(self) -> str | None:
        """Return the currently selected Eco capacity tier."""
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        eco_raw = st.get("eco", 0)
        eco_val = eco_raw.get("value", 0) if isinstance(eco_raw, dict) else eco_raw
        return BS_TO_ECO.get(eco_val, ECO_OPTIONS[0])

    async def async_select_option(self, option: str) -> None:
        """Change the Eco capacity tier."""
        val = ECO_TO_BS.get(option, 0)
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        current_fspd = st.get("fspd", 3)
        await self.hass.async_add_executor_job(
            self.hub.send_command,
            self.thing_id,
            {"eco": {"value": val, "fspd": current_fspd}, "lcmd": "eco"},
        )
