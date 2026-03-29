from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .parser import ParamDef


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for pd in coordinator.param_defs:
        if pd.t == "b":
            entities.append(SopraParamSwitch(coordinator, pd))

    async_add_entities(entities)


class SopraParamSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, pd: ParamDef):
        super().__init__(coordinator)
        self.pd = pd
        self._attr_unique_id = f"sopra_sw_{pd.param_id}"
        self._attr_name = f"Sopra {pd.group_title} {pd.label}"

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
        raw = self.coordinator.get_param_value(self.pd.param_id)
        if raw is None:
            return False
        try:
            # ajax_dataTopt_.json: 1=Aus, 2=Ein
            return int(float(raw)) == 2
        except Exception:
            return False

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.api.set_value(self.pd.wi, self.pd.t, 2)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.api.set_value(self.pd.wi, self.pd.t, 1)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        return {"param_id": self.pd.param_id, "wi": self.pd.wi, "type": self.pd.t}