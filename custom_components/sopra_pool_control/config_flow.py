from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class SopraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            schema = vol.Schema({
                vol.Required("host"): str,
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        await self.async_set_unique_id(user_input["host"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=f"Sopra {user_input['host']}", data=user_input)


class SopraOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is None:
            schema = vol.Schema({
                vol.Optional(
                    "scan_interval",
                    default=self.config_entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                ): vol.Coerce(int),
            })
            return self.async_show_form(step_id="init", data_schema=schema)

        return self.async_create_entry(title="", data=user_input)


async def async_get_options_flow(config_entry):
    return SopraOptionsFlowHandler(config_entry)