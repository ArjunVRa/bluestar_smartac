"""Sensor platform for Blue Star Smart AC."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, SignalStrength, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import BlueStarHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Star sensor entities."""
    hub: BlueStarHub = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for tid, info in hub.devices.items():
        entities.append(BlueStarRoomTempSensor(hub, tid, info))
        entities.append(BlueStarTargetTempSensor(hub, tid, info))
        entities.append(BlueStarCompressorHoursSensor(hub, tid, info))
        entities.append(BlueStarRssiSensor(hub, tid, info))
    async_add_entities(entities)


class _BaseBlueStarSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        self.hub = hub
        self.thing_id = thing_id
        self._device_info = device_info

    async def async_added_to_hass(self) -> None:
        def _update(thing_id: str):
            if thing_id == self.thing_id:
                self.schedule_update_ha_state()

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


class BlueStarRoomTempSensor(_BaseBlueStarSensor):
    _attr_name = "Room Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_room_temp"

    @property
    def native_value(self) -> float | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        try:
            return float(st.get("ctemp", 25.0))
        except (ValueError, TypeError):
            return None


class BlueStarTargetTempSensor(_BaseBlueStarSensor):
    _attr_name = "Target Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_target_temp"

    @property
    def native_value(self) -> float | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        try:
            return float(st.get("stemp", 24.0))
        except (ValueError, TypeError):
            return None


class BlueStarCompressorHoursSensor(_BaseBlueStarSensor):
    _attr_name = "Compressor Run Hours"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:counter"

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_compressor_hours"

    @property
    def native_value(self) -> int | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        return st.get("c_runhour", 0)


class BlueStarRssiSensor(_BaseBlueStarSensor):
    _attr_name = "WiFi Signal"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SignalStrength.DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub: BlueStarHub, thing_id: str, device_info: dict[str, Any]) -> None:
        super().__init__(hub, thing_id, device_info)
        self._attr_unique_id = f"bluestar_{thing_id.lower()}_wifi_rssi"

    @property
    def native_value(self) -> int | None:
        st = self.hub.cached_states.get(self.thing_id, {}).get("state", {})
        return st.get("rssi", 0)
