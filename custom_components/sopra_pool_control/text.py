from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .parser import ParamDef


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for pd in coordinator.param_defs:
        if pd.t in ("s", "wp"):
            entities.append(SopraParamText(coordinator, pd))

    async_add_entities(entities)


class SopraParamText(CoordinatorEntity, TextEntity):
    def __init__(self, coordinator, pd: ParamDef):
        super().__init__(coordinator)
        self.pd = pd
        self._attr_unique_id = f"sopra_txt_{pd.param_id}"
        self._attr_name = f"Sopra {pd.group_title} {pd.label}"

        if pd.t == "wp":
            self._attr_mode = TextMode.PASSWORD

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
        # Passwordfelder nicht als State anzeigen
        if self.pd.t == "wp":
            return None
        return self.coordinator.get_param_value(self.pd.param_id)

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.api.set_value(self.pd.wi, self.pd.t, value)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        return {"param_id": self.pd.param_id, "wi": self.pd.wi, "type": self.pd.t}