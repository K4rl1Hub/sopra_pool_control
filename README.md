# Sopra Pool Control – Home Assistant Custom Integration

> **Status:** Custom Component (hacs install) • **IoT Class:** `local_polling` • **Login:** not required  
> This integration reads data from `ajax_data.json` and writes parameters via `input.cgi`.

---

## Overview

This custom integration connects a **Sopra Test Premium** (or a compatible device with the same web interface) to Home Assistant. Tested with Sopra Test Premium 17

- **Read (polling):** `http://<host>/ajax_data.json`
- **Write (control):** `http://<host>/input.cgi?wi=<w>&<t>=<value>`
- **Automatic entity creation:**
  - Alarm status from `d8`
  - Operating mode / status flags from `d0` / `d1`
  - Control entities from `lang.xml` (`number` / `switch` / `text`)

> Current implementation without login and `ajax_data.json` served from the **root** of the device (no subfolder).

---

## Features

✅ **Alarm integration (d8)**
- `sensor` with human-readable state (`ok` / `warning` / `alarm`)
- `binary_sensor` for automations (on when warning/alarm)

✅ **Operating mode & status flags (d0/d1)**
- Operating mode exposed as a numeric code (debug-friendly)
- Raw and parsed values exposed as attributes

✅ **All control functions (generic from lang.xml)**
- Automatically generates entities from `lang.xml`
- Writes via `input.cgi` without login
- Min/Max, step size, and units when available

✅ **Device Info**
- Device appears as a proper Home Assistant device (name/serial/software where available in `d3`)

---

## Supported Endpoints

| Endpoint | Type | Purpose |
|---|---|---|
| `/ajax_data.json` | JSON | Live data (d0…d9), including d3 (ID/value), d6 (units), d8 (alarm) |
| `/lang.xml` | XML | Metadata & mapping of writable parameters (write index, type, range, unit) |
| `/input.cgi` | CGI (GET) | Writes parameters: `?wi=<w>&<t>=<value>` |

Optional (if present on the device):
- `/ajax_dataT_.json` or `/ajax_dataT.json` (label texts). Fallback labels are built into the integration.

---

## Entities (Home Assistant)

### Alarm (d8)

Example from `ajax_data.json`:

```json
"d8": "22;2;"
```

Interpretation:
- `22` = alarm ID
- `0` = ok
- `1` = warning
- `2` = alarm

**Entities:**

- `sensor.sopra_alarm_status`
  - values: `ok`, `warning`, `alarm`
  - attributes: `raw_level`, `alarm_id`

- `binary_sensor.sopra_alarm`
  - `on` when warning or alarm (`raw_level >= 1`)
  - attributes: `raw_level`, `alarm_id`


### Operating mode (d0/d1)

The integration currently exposes operating mode as a **numeric code**.

- `sensor.sopra_operating_mode`
  - state: `d0[0]` (primary code)
  - attributes:
    - `d0_raw`, `d1_raw`
    - `d0_parsed`, `d1_parsed`


### Control functions (lang.xml → number/switch/text)

All writable parameters described in `lang.xml` are created as entities.

XML example:

```xml
<in w="450" t="f2" gi="2000;2000;2006">4500</in>
<un>2006</un>
```

- `param_id` = `4500` → the current value is read from `d3`
- `wi` = `450` → write index for `input.cgi`
- `t` = `f2` → parameter type/encoding
- `un` = `2006` → unit ID (resolved via `d6` when available)

**Type mapping (`t` attribute):**
- `f`, `f2`, `i`, `uc`, `xv` → `number.*`
- `b` → `switch.*` (1=Off, 2=On)
- `s` → `text.*`
- `wp` → `text.*` in password mode (state is not displayed)

---

## Installation

1) Install via HACS or copy the component folder into your Home Assistant config:

```text
<HA config>/custom_components/sopra_pool_control/
```

Example structure:

```text
custom_components/sopra_pool_control/
├── __init__.py
├── api.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── parser.py
├── sensor.py
├── binary_sensor.py
├── number.py
├── switch.py
└── text.py
```

2) Restart Home Assistant:
- **Settings → System → Restart**

3) Add the integration:
- **Settings → Devices & Services → Add Integration**
- Search for **"Sopra Pool Control"**
- Enter the host/IP (e.g., `192.168.200.11`)

---

## Configuration

### Config Flow
When adding the integration:
- `host` (IP/hostname)

### Options
- `scan_interval` (polling interval in seconds, default: `10`)

---

## Writing / Control (Examples)

When you change a value, the integration sends requests like:

```text
http://<host>/input.cgi?wi=450&f2=1.20
http://<host>/input.cgi?wi=111&b=2
http://<host>/input.cgi?wi=22&s=sopra-test
```

---

## Safety Notes

- Changes take effect **immediately** on the controller (regulation/dosing). Test with “harmless” parameters first.
- Password fields (`t="wp"`) are not shown as clear-text states in Home Assistant.

---

## Troubleshooting

**No entities show up**
- Verify in a browser:
  - `http://<host>/ajax_data.json`
  - `http://<host>/lang.xml`
- Check Home Assistant logs: **Settings → System → Logs**

**Writing does not work**
- Test manually in a browser:
  - `http://<host>/input.cgi?wi=<wi>&<t>=<value>`
- Ensure the parameter is writable (only items with `w="..."` in `lang.xml` are created).

---

## Roadmap / Possible Enhancements

- Human-readable operating mode mapping (`d0/d1`) → `select`
- Enums (e.g., `xv`) as `select` instead of `number` (with an options mapping)
- Additional sensors from `d2` (measurements like chlorine/pH/temperature) including limit attributes

---

## License

Private project / custom integration. If you plan to publish it, consider an OSS license (e.g., MIT).
