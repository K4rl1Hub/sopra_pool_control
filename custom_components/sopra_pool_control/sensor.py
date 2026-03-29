from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ALARM_ID
from .parser import alarm_level_from_d8, alarm_text


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SopraAlarmStatusSensor(coordinator),
        SopraOperatingModeSensor(coordinator),
    ])


class SopraBase(CoordinatorEntity):
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


class SopraAlarmStatusSensor(SopraBase, SensorEntity):
    _attr_name = "Sopra Alarm Status"
    _attr_unique_id = "sopra_alarm_status"

    @property
    def native_value(self):
        level = alarm_level_from_d8(self.coordinator.data.get("d8", ""), alarm_id=ALARM_ID)
        return alarm_text(level)

    @property
    def extra_state_attributes(self):
        level = alarm_level_from_d8(self.coordinator.data.get("d8", ""), alarm_id=ALARM_ID)
        return {"raw_level": level, "alarm_id": ALARM_ID}


class SopraOperatingModeSensor(SopraBase, SensorEntity):
    _attr_name = "Sopra Betriebsmodus"
    _attr_unique_id = "sopra_operating_mode"

    @property
    def native_value(self):
        # Ohne verlässliche Mapping-Tabelle liefern wir den numerischen Code.
        # In vielen UIs steht der relevante Modus in d0[0] oder d0[1].
        if not self.coordinator.d0:
            return None
        # Wir nehmen d0[0] als Hauptcode, geben alles weitere in Attributes
        return self.coordinator.d0[0]

    @property
    def extra_state_attributes(self):
        return {
            "d0_raw": self.coordinator.data.get("d0"),
            "d1_raw": self.coordinator.data.get("d1"),
            "d0_parsed": self.coordinator.d0,
            "d1_parsed": self.coordinator.d1,
        }