# MBP Marktüberblick

Prototyp eines Markt-Dashboards für das Münsteraner Börsenparkett (MBP): Indizes, Wochenveränderung, anstehende Termine und ein fertiger Text für Newsletter und Social Media.

## Aufbau
- `konfiguration.json`: Indizes (Name, Yahoo-Ticker) und die Adresse der Terminquelle (`termine_quelle`). Neue Indizes nur hier eintragen.
- `daten_holen.py`: holt Schlusskurse (yfinance) und Termine und schreibt `daten/markt.json`. Mit `--beispiel` entstehen erfundene Kurse und Termine ohne Internet.
- `termine_holen.py`: liest die Termine aus der Programmseite des MBP (boersenparkett.org), nur mit der Standardbibliothek.
- `ERKLAERUNG.md`: ausführliche Erklärung des ganzen Ablaufs.
- `vorlage.html`: Seite mit Gestaltung und Logik. Alle Kennzahlen (Tag, Woche, Zeitraum) werden im Browser aus dem Verlauf berechnet.
- `bauen.py`: setzt `daten/markt.json` in die Vorlage ein und schreibt `dashboard.html`.

## Befehle
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python daten_holen.py            # echte Kurse und MBP-Termine
python daten_holen.py --beispiel # Beispieldaten
python bauen.py                  # dashboard.html erzeugen
```

## Konventionen
- Deutsche Namen für Variablen, Funktionen und Dateien.
- DRY: Kennzahlen nur an einer Stelle berechnen (`veraenderung` in `vorlage.html`).
- Beispieldaten immer sichtbar kennzeichnen (`beispieldaten: true` blendet den Hinweis ein).

## Stand
- Der Abruf echter Kurse funktioniert (getestet am 10.11.2026 mit yfinance 1.8.0): alle sechs Ticker liefern Daten.
- Fehler werden pro Ticker abgefangen (`indizes_laden`): ein Index ohne Daten wird mit einer Warnung übersprungen. Liefert kein Index Daten, bricht das Skript ab und lässt `daten/markt.json` unverändert.
- Läuft das Skript während der Handelszeit, wird der laufende Kurs des Tages weggelassen (`handelstag_laeuft_noch`); der Verlauf endet dann beim Schlusskurs des Vortags.
- Termine kommen ausschließlich von der MBP-Programmseite (getestet am 12.11.2026). Schlägt der Abruf fehl oder ändert sich der Aufbau der Seite, gibt es eine Warnung und die Terminliste bleibt leer.
- Texte von außen werden in `vorlage.html` mit `sicher()` entschärft, bevor sie ins HTML kommen.
- Veröffentlichung: `.github/workflows/veroeffentlichen.yml` holt täglich um 05:30 UTC Kurse und Termine, baut das Dashboard und stellt es über GitHub Pages als Startseite bereit. `daten/` und `dashboard.html` sind erzeugte Dateien und stehen in `.gitignore`.

## Nächste Schritte
1. Newsletter-Text als Datei ausgeben oder per Mail versenden.
