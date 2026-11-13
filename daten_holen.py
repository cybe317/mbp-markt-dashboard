"""Holt die Kursverläufe aller Indizes und schreibt daten/markt.json.

Aufruf:
    python daten_holen.py             echte Kurse über yfinance
    python daten_holen.py --beispiel  erfundene Kurse (ohne Internet)
"""
import argparse
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from termine_holen import termine_laden

WURZEL = Path(__file__).parent
KONFIG_PFAD = WURZEL / "konfiguration.json"
AUSGABE_PFAD = WURZEL / "daten" / "markt.json"
HANDELSTAGE = 90


def warnen(meldung: str) -> None:
    """Warnungen gehen nach stderr, damit sie von der normalen Ausgabe getrennt bleiben."""
    print(f"Warnung: {meldung}", file=sys.stderr)


def letzte_handelstage(ende: date, anzahl: int) -> list[date]:
    """Die letzten `anzahl` Wochentage bis einschließlich `ende`."""
    tage = []
    tag = ende
    while len(tage) < anzahl:
        if tag.weekday() < 5:
            tage.append(tag)
        tag -= timedelta(days=1)
    return tage[::-1]


def beispielverlauf(index: dict) -> list[dict]:
    """Zufallspfad mit festem Startwert, pro Ticker immer gleich."""
    zufall = random.Random(index["ticker"])
    kurs = index["beispiel_start"]
    verlauf = []
    for tag in letzte_handelstage(date.today(), HANDELSTAGE):
        kurs *= 1 + zufall.gauss(0.0004, 0.009)
        verlauf.append({"datum": tag.isoformat(), "schluss": round(kurs, 2)})
    return verlauf


def handelstag_laeuft_noch(letzter_tag, metadaten: dict) -> bool:
    """Wahr, wenn `letzter_tag` der heutige Handelstag ist und die Börse noch nicht geschlossen hat."""
    handelsschluss = metadaten["currentTradingPeriod"]["regular"]["end"]
    jetzt = datetime.now(handelsschluss.tzinfo)  # Uhrzeit am Börsenplatz, nicht am eigenen Rechner
    return letzter_tag.date() == handelsschluss.date() and jetzt < handelsschluss


def echter_verlauf(index: dict) -> list[dict]:
    """Schlusskurse der letzten Handelstage von Yahoo Finance."""
    import yfinance  # erst hier, damit --beispiel ohne das Paket läuft

    wertpapier = yfinance.Ticker(index["ticker"])
    kurse = wertpapier.history(period="6mo")["Close"].dropna()
    if kurse.empty:
        raise ValueError("keine Kurse erhalten (Ticker falsch oder nicht mehr gelistet?)")
    if handelstag_laeuft_noch(kurse.index[-1], wertpapier.history_metadata):
        kurse = kurse.iloc[:-1]  # laufender Kurs von heute ist noch kein Schlusskurs
    return [
        {"datum": zeitpunkt.date().isoformat(), "schluss": round(float(schluss), 2)}
        for zeitpunkt, schluss in kurse.tail(HANDELSTAGE).items()
    ]


def indizes_laden(indizes: list[dict], verlauf_holen) -> list[dict]:
    """Holt jeden Index einzeln; ein Fehler überspringt nur diesen einen Index."""
    geladen = []
    for index in indizes:
        try:
            verlauf = verlauf_holen(index)
        except Exception as fehler:  # yfinance wirft je nach Ursache verschiedene Fehlertypen
            warnen(f"{index['name']} ({index['ticker']}) übersprungen: {fehler}")
            continue
        geladen.append({"name": index["name"], "einheit": index["einheit"], "verlauf": verlauf})
    return geladen


def beispieltermine() -> list[dict]:
    """Zwei erfundene Termine in den nächsten Wochen (ohne Internet)."""
    return [
        {
            "datum": (date.today() + timedelta(days=tage)).isoformat(), "uhrzeit": "18:00",
            "art": "Beispiel", "titel": titel, "ort": "Beispielort", "link": "",
        }
        for tage, titel in [(7, "Beispielvortrag"), (14, "Beispielworkshop")]
    ]


def echte_termine(seiten_adresse: str) -> list[dict]:
    """Termine von der MBP-Website; bei einem Fehler eine Warnung und eine leere Liste."""
    try:
        return termine_laden(seiten_adresse)
    except Exception as fehler:  # Netzwerkfehler oder geänderter Seitenaufbau
        warnen(f"Termine nicht geladen ({seiten_adresse}): {fehler}")
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beispiel", action="store_true", help="erfundene Kurse erzeugen")
    argumente = parser.parse_args()

    konfig = json.loads(KONFIG_PFAD.read_text(encoding="utf-8"))
    verlauf_holen = beispielverlauf if argumente.beispiel else echter_verlauf

    indizes = indizes_laden(konfig["indizes"], verlauf_holen)
    if not indizes:
        sys.exit(f"Fehler: Kein Index lieferte Daten, {AUSGABE_PFAD} bleibt unverändert.")

    markt = {
        "stand": date.today().isoformat(),
        "beispieldaten": argumente.beispiel,
        "indizes": indizes,
        "termine": beispieltermine() if argumente.beispiel else echte_termine(konfig["termine_quelle"]),
    }
    AUSGABE_PFAD.parent.mkdir(exist_ok=True)
    AUSGABE_PFAD.write_text(json.dumps(markt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(indizes)} von {len(konfig['indizes'])} Indizes und {len(markt['termine'])} Termine geschrieben nach {AUSGABE_PFAD}")


if __name__ == "__main__":
    main()
