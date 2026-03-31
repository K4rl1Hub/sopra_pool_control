from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlencode

from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SopraEndpoints:
    """
    Central place for endpoint names.
    According to your setup:
      - ajax_data.json is available directly under the root of the device.
      - input.cgi is available directly under the root as well.
      - lang.xml is available directly under the root as well.
    """
    ajax_data: str = "ajax_data.json"
    lang_xml: str = "lang.xml"
    input_cgi: str = "input.cgi"
    ajax_dataT: tuple[str, ...] = ("ajax_dataT_.json", "ajax_dataT.json")  # optional


def _build_url(host: str, path: str) -> str:
    """Build URL for device resources (root based)."""
    return f"http://{host}/{path.lstrip('/')}"


async def http_get_json(hass, host: str, path: str, timeout: int = 10) -> dict[str, Any]:
    """
    Low-level helper: GET JSON from http://<host>/<path>.
    """
    session = async_get_clientsession(hass)
    url = _build_url(host, path)
    _LOGGER.debug("GET JSON %s", url)
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.json()


async def http_get_text(hass, host: str, path: str, timeout: int = 10) -> str:
    """
    Low-level helper: GET text from http://<host>/<path>.
    """
    session = async_get_clientsession(hass)
    url = _build_url(host, path)
    _LOGGER.debug("GET TEXT %s", url)
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.text()


async def http_get_bytes(hass, host: str, path: str, timeout: int = 10) -> bytes:
    """
    Low-level helper: GET raw bytes from http://<host>/<path>.
    """
    session = async_get_clientsession(hass)
    url = _build_url(host, path)
    _LOGGER.debug("GET BYTES %s", url)
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.read()


async def write_input_cgi(
    hass,
    host: str,
    wi: int,
    t: str,
    value: str | int | float,
    timeout: int = 10,
) -> None:
    """
    Write a value via input.cgi.

    The Sopra web UI uses a query style like:
      /input.cgi?wi=<wi>&<t>=<value>

    Examples:
      /input.cgi?wi=450&f2=1.20
      /input.cgi?wi=111&b=2
      /input.cgi?wi=22&s=sopra-test
    """
    session = async_get_clientsession(hass)
    params = {"wi": str(wi), t: str(value)}
    url = _build_url(host, SopraEndpoints().input_cgi) + "?" + urlencode(params)

    _LOGGER.debug("WRITE %s", url)
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        # Some devices return a small body, some return empty -> just read to finish the request.
        await resp.read()


# ---------------------------------------------------------------------------
# Functional (non-class) high level helpers
# ---------------------------------------------------------------------------

async def fetch_ajax_data(hass, host: str, timeout: int = 10) -> dict[str, Any]:
    """Fetch the main data payload from ajax_data.json."""
    ep = SopraEndpoints()
    return await http_get_json(hass, host, ep.ajax_data, timeout=timeout)


async def fetch_lang_xml(hass, host: str, timeout: int = 10) -> str:
    """Fetch lang.xml (configuration/mapping)."""
    ep = SopraEndpoints()
    return await http_get_text(hass, host, ep.lang_xml, timeout=timeout)


async def try_fetch_labels(hass, host: str, timeout: int = 10) -> Optional[dict[str, Any]]:
    """
    Try to fetch optional label mappings from ajax_dataT_.json or ajax_dataT.json.
    Returns the JSON dict if found, else None.
    """
    ep = SopraEndpoints()
    for candidate in ep.ajax_dataT:
        try:
            return await http_get_json(hass, host, candidate, timeout=timeout)
        except Exception as err:
            _LOGGER.debug("Optional labels %s not available: %s", candidate, err)
    return None


async def set_value(hass, host: str, wi: int, t: str, value: str | int | float, timeout: int = 10) -> None:
    """Convenience wrapper around write_input_cgi."""
    await write_input_cgi(hass, host, wi, t, value, timeout=timeout)


# ---------------------------------------------------------------------------
# Class-based API wrapper (for Coordinator / ConfigFlow compatibility)
# ---------------------------------------------------------------------------

class SopraApi:
    """
    Thin OO wrapper so the integration can do:
        from .api import SopraApi
        api = SopraApi(hass, host)
        await api.get_json("ajax_data.json")
        await api.set_value(wi, t, value)

    This fixes the HA import error when other modules expect SopraApi to exist.
    """

    def __init__(self, hass, host: str, endpoints: SopraEndpoints | None = None):
        self.hass = hass
        self.host = host
        self.endpoints = endpoints or SopraEndpoints()

    def url(self, path: str) -> str:
        return _build_url(self.host, path)

    async def get_json(self, path: str, timeout: int = 10) -> dict[str, Any]:
        return await http_get_json(self.hass, self.host, path, timeout=timeout)

    async def get_text(self, path: str, timeout: int = 10) -> str:
        return await http_get_text(self.hass, self.host, path, timeout=timeout)

    async def fetch_ajax_data(self, timeout: int = 10) -> dict[str, Any]:
        return await fetch_ajax_data(self.hass, self.host, timeout=timeout)

    async def fetch_lang_xml(self, timeout: int = 10) -> str:
        return await fetch_lang_xml(self.hass, self.host, timeout=timeout)

    async def try_fetch_labels(self, timeout: int = 10) -> Optional[dict[str, Any]]:
        return await try_fetch_labels(self.hass, self.host, timeout=timeout)

    async def set_value(self, wi: int, t: str, value: str | int | float, timeout: int = 10) -> None:
        await write_input_cgi(self.hass, self.host, wi, t, value, timeout=timeout)