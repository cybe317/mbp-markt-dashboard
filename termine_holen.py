"""Liest die Termine von der Programmseite des MBP (boersenparkett.org).

Jede Terminkarte der Seite ist ein Link (<a>), der vier beschriftete Bereiche enthält:
    data-framer-name="Raum"   Art des Termins, z. B. "Workshop"
    data-framer-name="Title"  zuerst der Titel, danach der Ort
    <time datetime="...">     Datum und Uhrzeit

Aufruf zum Ausprobieren:
    python termine_holen.py https://www.boersenparkett.org/events/programm
"""
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ZEITLIMIT_SEKUNDEN = 20


class TerminLeser(HTMLParser):
    """Geht das HTML Stück für Stück durch und sammelt pro Terminkarte die Angaben."""

    def __init__(self, seiten_adresse: str):
        super().__init__()
        self.seiten_adresse = seiten_adresse
        self.termine = []
        self.karte = None  # Angaben der Karte, in der wir uns gerade befinden
        self.bereich = None  # Name des Bereichs, dessen Text als Nächstes kommt

    def handle_starttag(self, tag, attribute):
        attribute = dict(attribute)
        if tag == "a":
            self.karte = {"link": urljoin(self.seiten_adresse, attribute.get("href", "")), "Raum": [], "Title": []}
            self.bereich = None
        elif self.karte is None:
            return
        elif tag == "div" and "data-framer-name" in attribute:
            self.bereich = attribute["data-framer-name"]
        elif tag == "time" and "zeitpunkt" not in self.karte:
            self.karte["zeitpunkt"] = attribute.get("datetime", "")

    def handle_data(self, text):
        text = text.strip()
        if self.karte is not None and text and self.bereich in ("Raum", "Title"):
            self.karte[self.bereich].append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self.karte is not None:
            self.karte_abschliessen(self.karte)
            self.karte = None

    def karte_abschliessen(self, karte: dict) -> None:
        """Übernimmt die Karte als Termin, wenn Titel und Zeitpunkt vorhanden sind."""
        zeitpunkt = karte.get("zeitpunkt", "")
        if not karte["Title"] or len(zeitpunkt) < 16:
            return  # gewöhnlicher Link, keine Terminkarte
        titel, *rest = karte["Title"]
        self.termine.append({
            "datum": zeitpunkt[:10],  # "2026-11-12T16:30:00.000Z" -> "2026-11-12"
            "uhrzeit": zeitpunkt[11:16],  # -> "16:30"
            "art": karte["Raum"][0] if karte["Raum"] else "Event",
            "titel": titel,
            "ort": rest[0] if rest else "",
            "link": karte["link"],
        })


def ohne_doppelte(termine: list[dict]) -> list[dict]:
    """Die Seite enthält jede Karte mehrfach (Handy, Tablet, Desktop); jede soll nur einmal bleiben."""
    eindeutig = {(termin["datum"], termin["titel"]): termin for termin in termine}
    return sorted(eindeutig.values(), key=lambda termin: (termin["datum"], termin["uhrzeit"]))


def termine_laden(seiten_adresse: str) -> list[dict]:
    """Lädt die Programmseite und gibt alle Termine nach Datum sortiert zurück."""
    anfrage = Request(seiten_adresse, headers={"User-Agent": "mbp-markt-dashboard"})
    with urlopen(anfrage, timeout=ZEITLIMIT_SEKUNDEN) as antwort:
        seite = antwort.read().decode("utf-8")
    leser = TerminLeser(seiten_adresse)
    leser.feed(seite)
    termine = ohne_doppelte(leser.termine)
    if not termine:
        raise ValueError("keine Termine gefunden (Aufbau der Seite geändert?)")
    return termine


if __name__ == "__main__":
    for termin in termine_laden(sys.argv[1]):
        print(termin["datum"], termin["uhrzeit"], "|", termin["art"], "|", termin["titel"], "|", termin["ort"])
