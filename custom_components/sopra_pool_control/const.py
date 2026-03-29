DOMAIN = "sopra"
PLATFORMS = ["sensor", "binary_sensor", "number", "switch", "text"]

DEFAULT_SCAN_INTERVAL = 10  # seconds

# Fixe Messwertbasis aus deinem lang.xml (Messwerte-Block)
MEASUREMENTS = {
    2000: {"name": "Chlor", "unit": "mg/l"},
    2172: {"name": "pH", "unit": "pH"},
    2344: {"name": "Redox", "unit": "mV"},
    2516: {"name": "Leitfähigkeit", "unit": "µS/cm"},
    2688: {"name": "Temperatur", "unit": "°C"},
}

# aus d8: "22;2;" -> ID 22 ist Alarmlevel
ALARM_ID = 22

# Fallback-Texte aus deiner ajax_dataT_.json (damit es auch klappt, wenn das Gerät die Datei nicht bereitstellt)
DEFAULT_T_LABELS = {
    "1": "Messwerte",
    "2": "Parameter",
    "3": "Sollwert",
    "4": "Regelverstärkung Xp",
    "5": "Nachlaufzeit Tn",
    "6": "Grenzwert I Max",
    "7": "Grenzwert I Min",
    "8": "Grenzwert II Max",
    "9": "Grenzwert II Min",
    "10": "System",
    "11": "Systemname",
    "12": "Datum",
    "13": "Uhrzeit",
    "14": "Software Hauptplatine",
    "15": "Softwarenummer",
    "16": "Up time",
    "17": "Konfiguration IP",
    "18": "Subnetzmaske",
    "19": "Gateway",
    "20": "MAC",
    "21": "IP Passwort",
    "22": "DHCP",
    "23": "Konfiguration Startseite",
    "24": "Konfiguration",
    "25": "Passwort",
    "26": "Konfiguration Benutzerverwaltung",
    "27": "Seriennummer",
    "28": "IP Adresse",
    "29": "Name Verlinkung",
    "30": "IP-Verlinkung",
    "31": "Kommunikation Filtersteuerung",
}