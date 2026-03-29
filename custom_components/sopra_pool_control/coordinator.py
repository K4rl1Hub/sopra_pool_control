from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SopraApi
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_T_LABELS, MEASUREMENTS
from .parser import (
    parse_pairs,
    parse_d6_units,
    parse_int_list,
    parse_lang_xml,
)

_LOGGER = logging.getLogger(__name__)


class SopraCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass, api: SopraApi, scan_interval: int = DEFAULT_SCAN_INTERVAL):
        self.api = api
        self.t_labels: dict[str, str] = dict(DEFAULT_T_LABELS)

        self.units: dict[int, str] = {}
        self.d3: dict[int, str] = {}
        self.d8: dict[int, str] = {}
        self.d0: list[int] = []
        self.d1: list[int] = []

        self.param_defs = []  # list[ParamDef]

        super().__init__(
            hass,
            _LOGGER,
            name="sopra",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_load_metadata(self) -> None:
        # optional: falls Gerät ajax_dataT_.json bereitstellt, nutzen wir es
        # wir versuchen ein paar Varianten robust
        for candidate in ("ajax_dataT_.json", "ajax_dataT.json"):
            try:
                data = await self.api.get_json(candidate)
                # keys sind "1","2",... -> direkt nutzbar
                self.t_labels.update(data)
                break
            except Exception:
                continue

        # lang.xml ist entscheidend für "alle Steuerfunktionen"
        xml_text = await self.api.get_text("lang.xml")
        measurement_names = {mid: meta["name"] for mid, meta in MEASUREMENTS.items()}
        self.param_defs = parse_lang_xml(xml_text, self.t_labels, measurement_names)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.get_json("ajax_data.json")

            self.d3 = parse_pairs(data.get("d3", ""))
            self.d8 = parse_pairs(data.get("d8", ""))
            self.units = parse_d6_units(data.get("d6", ""))

            self.d0 = parse_int_list(data.get("d0", ""))
            self.d1 = parse_int_list(data.get("d1", ""))

            return data
        except Exception as err:
            raise UpdateFailed(f"Sopra update failed: {err}") from err

    def get_param_value(self, param_id: int) -> str | None:
        return self.d3.get(param_id)

    def get_unit(self, unit_id: int | None) -> str | None:
        if unit_id is None:
            return None
        return self.units.get(unit_id)

    def get_device_info_fields(self) -> dict[str, str | None]:
        """
        Ableitung aus deinem d3-Beispiel / lang.xml:
          104 Systemname
          500 Software Hauptplatine
          510 Softwarenummer
          751 Seriennummer
          518 MAC
        """
        return {
            "systemname": self.d3.get(104),
            "mainboard_sw": self.d3.get(500),
            "sw_version": self.d3.get(510),
            "serial": self.d3.get(751),
            "mac": self.d3.get(518),
        }