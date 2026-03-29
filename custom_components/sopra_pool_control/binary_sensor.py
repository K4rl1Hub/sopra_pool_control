from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ALARM_ID
from .parser import alarm_level_from_d8


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SopraAlarmBinarySensor(coordinator)])


class SopraAlarmBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_name = "Sopra Alarm"
    _attr_unique_id = "sopra_alarm"
    _attr_device_class = "problem"

    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def device_info(self):
        fields = self.coordinator.get_device_info_fields()
        serial = fields.get("serial") or self.coordinator.api.host
        return {
            "identifiers": {(DOMAIN, serial)},
            "name": fields.get("systemname") or f"Sopra {self.coordinator.api.host}",
            "manufacturer": "Sopra",
            "model": "Pool Controller",
            "sw_version": fields.get("sw_version"),
        }

    @property
    def is_on(self) -> bool:
        level = alarm_level_from_d8(self.coordinator.data.get("d8", ""), alarm_id=ALARM_ID)
        return level >= 1

    @property
    def extra_state_attributes(self):
        level = alarm_level_from_d8(self.coordinator.data.get("d8", ""), alarm_id=ALARM_ID)
        return {"raw_level": level, "alarm_id": ALARM_ID}
