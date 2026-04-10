from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import xml.etree.ElementTree as ET


def split_semicolon(raw: Optional[str]) -> list[str]:
    if raw is None:
        return []
    parts = raw.split(";")
    # manche Antworten enden mit ';' -> letzter Eintrag leer
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def parse_pairs(raw: Optional[str]) -> dict[int, str]:
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


def parse_d6_units(raw: Optional[str]) -> dict[int, str]:
    """
    Beispiel: "2;6000;%;6001;min;"
    """
    parts = split_semicolon(raw)
    out: dict[int, str] = {}
    if not parts:
        return out
    # erstes Feld ist oft die Anzahl (kann man ignorieren)
    i = 1
    while i + 1 < len(parts):
        try:
            uid = int(parts[i])
            unit = parts[i + 1]
            out[uid] = unit
        except Exception:
            pass
        i += 2
    return out


def parse_d0(raw: Optional[str]) -> list[int]:
    return parse_int_list(raw)


def parse_d1(raw: Optional[str]) -> list[int]:
    return parse_int_list(raw)


def alarm_level_from_d8(d8_raw: str, alarm_id: int = 22) -> int:
    pairs = parse_pairs(d8_raw)
    try:
        return int(pairs.get(alarm_id, "0"))
    except Exception:
        return 0


def alarm_text(level: int) -> str:
    # 0 ok, 1 warn, 2 alarm (nach deiner d8-Logik)
    if level >= 2:
        return "alarm"
    if level == 1:
        return "warnung"
    return "ok"


@dataclass(frozen=True)
class ParamDef:
    """
    Definition eines schreibbaren Parameters aus lang.xml
    """
    group_title: str          # z.B. "Chlor"
    label: str                # z.B. "Sollwert"
    param_id: int             # z.B. 4500 (Wert kommt aus d3)
    wi: int                   # z.B. 450  (write-index für input.cgi)
    t: str                    # z.B. "f2", "i", "b", "s", "wp", ...
    unit_id: Optional[int]    # z.B. 2006 oder 6000
    rng: Optional[tuple[float, float]]  # aus g="min;max"
    decimals: Optional[int]   # aus d="1"
    step: Optional[float]     # abgeleitet


def parse_lang_xml(
    xml_text: str,
    t_labels: dict[str, str],
    measurement_names: dict[int, str],
) -> list[ParamDef]:
    """
    Liest aus lang.xml alle <in ... w="...">...</in>-Einträge und erzeugt ParamDef.
    Nutzt t_labels (ajax_dataT_.json) um z.B. T_="3" -> "Sollwert" zu machen.
    measurement_names: 2000->"Chlor" etc.
    """
    root = ET.fromstring(xml_text)
    out: list[ParamDef] = []

    # lang.xml Struktur:
    # <no> ... <na T_="2" txt="2000"/> ... <va><vn T_="3"/><in w="450" t="f2">4500</in><un>2006</un></va>
    for no in root.findall(".//no"):
        na = no.find("na")
        if na is None:
            continue

        t_group = na.get("T_")  # z.B. "2" für Parametergruppe (Chlor)
        txt_measure = na.get("txt")  # z.B. "2000" -> Messwert-ID

        group_title = None
        if txt_measure:
            try:
                mid = int(txt_measure)
                group_title = measurement_names.get(mid, f"Messwert {mid}")
            except Exception:
                group_title = txt_measure

        # Wenn es keine Messwertgruppe ist (System/Config), group_title aus T_ ableiten
        if group_title is None:
            if t_group:
                group_title = t_labels.get(t_group, f"T_{t_group}")
            else:
                group_title = "Sopra"

        for va in no.findall("va"):
            vn = va.find("vn")
            in_el = va.find("in")
            un_el = va.find("un")

            if in_el is None:
                continue

            w = in_el.get("w")
            t = in_el.get("t")

            # nur writeable wenn w vorhanden
            if not w or not t:
                continue

            try:
                wi = int(w)
            except Exception:
                continue

            # param_id ist der Textinhalt von <in> (z.B. 4500)
            try:
                param_id = int((in_el.text or "").strip())
            except Exception:
                continue

            # label aus vn: vn hat entweder T_="3" oder Text
            label = "Parameter"
            if vn is not None:
                t_label = vn.get("T_")
                if t_label:
                    label = t_labels.get(t_label, f"T_{t_label}")
                else:
                    # manchmal steht Text im vn selbst
                    if vn.text and vn.text.strip():
                        label = vn.text.strip()

            unit_id = None
            if un_el is not None and un_el.text and un_el.text.strip().isdigit():
                unit_id = int(un_el.text.strip())

            # Range aus g="min;max"
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

def parse_int_list(raw: Optional[str]) -> list[int]:
    """
    Parse 'd0' / 'd1' style values like: '1;0;' -> [1, 0]
    Ignores non-numeric parts gracefully.
    """
    out: list[int] = []
    for p in split_semicolon(raw):
        try:
            out.append(int(p))
        except Exception:
            # ignore invalid fragments
            continue
    return out
