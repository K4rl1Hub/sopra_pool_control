from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MEASUREMENTS
from .parser import ParamDef


NUM_TYPES = {"f", "f2", "i", "uc", "xv"}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for pd in coordinator.param_defs:
        if pd.t in NUM_TYPES:
            entities.append(SopraParamNumber(coordinator, pd))

    async_add_entities(entities)


class SopraParamNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, pd: ParamDef):
        super().__init__(coordinator)
        self.pd = pd

        self._attr_unique_id = f"sopra_num_{pd.param_id}"
        self._attr_name = f"Sopra {pd.group_title} {pd.label}"

        unit = coordinator.get_unit(pd.unit_id)
        if unit is None:
            for _, meta in MEASUREMENTS.items():
                if meta["name"] == pd.group_title:
                    unit = meta["unit"]
                    break
        self._attr_native_unit_of_measurement = unit

        if pd.rng:
            self._attr_native_min_value = pd.rng[0]
            self._attr_native_max_value = pd.rng[1]
        if pd.step:
            self._attr_native_step = pd.step

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
    def native_value(self):
        raw = self.coordinator.get_param_value(self.pd.param_id)
        if raw is None:
            return None
        try:
            if self.pd.t in ("i", "uc", "xv"):
                return int(float(raw))
            return float(raw)
        except Exception:
            return None

    async def async_set_native_value(self, value: float) -> None:
        if self.pd.t in ("i", "uc", "xv"):
            value_to_send = int(round(value))
        else:
            value_to_send = value

        await self.coordinator.api.set_value(self.pd.wi, self.pd.t, value_to_send)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        return {
            "param_id": self.pd.param_id,
            "wi": self.pd.wi,
            "type": self.pd.t,
            "unit_id": self.pd.unit_id,
            "range": self.pd.rng,
            "decimals": self.pd.decimals,
        }