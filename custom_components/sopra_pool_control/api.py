from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import xml.etree.ElementTree as ET


def split_semicolon(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = raw.split(";")
    # Antworten enden oft mit ';' -> letzter Eintrag leer
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def parse_pairs(raw: str | None) -> dict[int, str]:
    """
    d3/d8 sind typischerweise: "ID;VALUE;ID;VALUE;..."
    """
    parts = split_semicolon(raw)
    out: dict[int, str] = {}
    i = 0
    while i + 1 < len(parts):
        try:
            k = int(parts[i])
            v = parts[i + 1]
            out[k] = v
        except Exception:
            pass
        i += 2
    return out


def parse_d6_units(raw: str | None) -> dict[int, str]:
    """
    Beispiel: "2;6000;%;6001;min;"
    -> {6000:"%", 6001:"min"}
    """
    parts = split_semicolon(raw)
    out: dict[int, str] = {}
    if not parts:
        return out
    i = 1  # erstes Feld ist meist Anzahl
    while i + 1 < len(parts):
        try:
            uid = int(parts[i])
            unit = parts[i + 1]
            out[uid] = unit
        except Exception:
            pass
        i += 2
    return out


def parse_int_list(raw: str | None) -> list[int]:
    parts = split_semicolon(raw)
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except Exception:
            pass
    return out


def alarm_level_from_d8(d8_raw: str | None, alarm_id: int) -> int:
    pairs = parse_pairs(d8_raw)
    try:
        return int(pairs.get(alarm_id, "0"))
    except Exception:
        return 0


def alarm_text(level: int) -> str:
    # nach deiner Logik: 0 ok, 1 warn, 2 alarm
    if level >= 2:
        return "alarm"
    if level == 1:
        return "warnung"
    return "ok"


@dataclass(frozen=True)
class ParamDef:
    group_title: str          # z.B. "Chlor" oder "System"
    label: str                # z.B. "Sollwert"
    param_id: int             # z.B. 4500 (Wert kommt aus d3)
    wi: int                   # z.B. 450  (Write-Index)
    t: str                    # f2/i/b/s/wp/xv/uc...
    unit_id: Optional[int]
    rng: Optional[tuple[float, float]]
    decimals: Optional[int]
    step: Optional[float]


def parse_lang_xml(
    xml_text: str,
    t_labels: dict[str, str],
    measurement_names: dict[int, str],
) -> list[ParamDef]:
    """
    Liest aus lang.xml alle writebaren Parameter:
      <in w="..." t="...">PARAM_ID</in>
    und erzeugt ParamDef.
    """
    root = ET.fromstring(xml_text)
    out: list[ParamDef] = []

    for no in root.findall(".//no"):
        na = no.find("na")
        if na is None:
            continue

        t_group = na.get("T_")           # z.B. "2" Parameter
        txt_measure = na.get("txt")      # z.B. "2000" -> Chlor (Gruppe)

        group_title: str | None = None
        if txt_measure:
            try:
                mid = int(txt_measure)
                group_title = measurement_names.get(mid, f"Messwert {mid}")
            except Exception:
                group_title = txt_measure

        if group_title is None:
            group_title = t_labels.get(t_group or "", f"T_{t_group}") if t_group else "Sopra"

        for va in no.findall("va"):
            vn = va.find("vn")
            in_el = va.find("in")
            un_el = va.find("un")

            if in_el is None:
                continue

            w = in_el.get("w")
            t = in_el.get("t")
            if not w or not t:
                continue

            try:
                wi = int(w)
            except Exception:
                continue

            try:
                param_id = int((in_el.text or "").strip())
            except Exception:
                continue

            label = "Parameter"
            if vn is not None:
                t_label = vn.get("T_")
                if t_label:
                    label = t_labels.get(t_label, f"T_{t_label}")
                elif vn.text and vn.text.strip():
                    label = vn.text.strip()

            unit_id = None
            if un_el is not None and un_el.text and un_el.text.strip().isdigit():
                unit_id = int(un_el.text.strip())

            rng = None
            g = in_el.get("g")
            if g and ";" in g:
                try:
                    lo, hi = g.split(";", 1)
                    rng = (float(lo), float(hi))
                except Exception:
                    rng = None

            decimals = None
            d = in_el.get("d")
            if d and d.isdigit():
                decimals = int(d)

            step = None
            if t in ("f", "f2"):
                if decimals is not None:
                    step = 10 ** (-decimals)
                elif t == "f2":
                    step = 0.01
                else:
                    step = 0.1
            elif t in ("i", "uc", "xv"):
                step = 1

            out.append(
                ParamDef(
                    group_title=group_title,
                    label=label,
                    param_id=param_id,
                    wi=wi,
                    t=t,
                    unit_id=unit_id,
                    rng=rng,
                    decimals=decimals,
                    step=step,
                )
            )

    return out