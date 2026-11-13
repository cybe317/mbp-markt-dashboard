# So funktioniert der MBP Marktüberblick

Diese Datei erklärt das Projekt so, dass du jeden Teil im Interview selbst erklären kannst.

## Das Prinzip in einem Satz

Zwei Python-Skripte holen Daten aus dem Internet und schreiben sie in eine JSON-Datei; ein drittes setzt diese Datei in eine HTML-Vorlage ein. Das Ergebnis `dashboard.html` ist eine einzelne Datei, die ohne Server im Browser läuft.

```
konfiguration.json ──┐
Yahoo Finance ───────┼─▶ daten_holen.py ─▶ daten/markt.json ─┐
boersenparkett.org ──┘      (nutzt termine_holen.py)         ├─▶ bauen.py ─▶ dashboard.html
                                              vorlage.html ──┘
```

Der Vorteil dieser Trennung: Holen, Speichern und Anzeigen sind unabhängig. Fällt eine Datenquelle aus, bleibt die letzte `markt.json` bestehen und das Dashboard lässt sich trotzdem bauen.

## Die Dateien

| Datei | Aufgabe |
|---|---|
| `konfiguration.json` | Welche Indizes (Name, Yahoo-Ticker) und von welcher Adresse die Termine kommen. Einzige Stelle für solche Einstellungen. |
| `daten_holen.py` | Holt Kurse und Termine, schreibt `daten/markt.json`. |
| `termine_holen.py` | Liest die Termine aus der Programmseite des MBP. |
| `vorlage.html` | Gestaltung (CSS) und Logik (JavaScript) der Seite, mit einem Platzhalter für die Daten. |
| `bauen.py` | Ersetzt den Platzhalter durch den Inhalt von `markt.json` und schreibt `dashboard.html`. |

## Schritt 1: Kurse holen (`daten_holen.py`)

1. `main()` liest `konfiguration.json`.
2. `indizes_laden()` geht die Indizes einzeln durch und ruft für jeden `echter_verlauf()` auf. Der Aufruf steht in einem `try/except`: Schlägt ein Index fehl, gibt es eine Warnung und die Schleife macht mit `continue` beim nächsten weiter.
3. `echter_verlauf()` fragt über das Paket `yfinance` die Kurse der letzten sechs Monate bei Yahoo Finance ab und behält die letzten 90 Handelstage.
   - Liefert Yahoo nichts zurück (z. B. falscher Ticker), löst die Funktion selbst einen `ValueError` aus. yfinance meldet diesen Fall nämlich nicht als Fehler, sondern gibt eine leere Tabelle zurück.
   - `handelstag_laeuft_noch()` prüft, ob die Börse des Index noch offen ist. Dann wäre der heutige Wert ein laufender Kurs und kein Schlusskurs, und er wird weggelassen. Verglichen wird mit der Uhrzeit am Börsenplatz, deshalb stimmt das für Frankfurt und New York gleichzeitig.
4. Liefert kein einziger Index Daten, bricht das Skript ab, ohne `markt.json` zu überschreiben.

Mit `--beispiel` erzeugt `beispielverlauf()` stattdessen erfundene Kurse (Zufallspfad, pro Ticker immer gleich) und `beispieltermine()` zwei erfundene Termine. Das Dashboard zeigt dann einen gelben Hinweis.

## Schritt 2: Termine von der MBP-Website (`termine_holen.py`)

Die Quelle ist `https://www.boersenparkett.org/events/programm`. Die Seite hat keine Schnittstelle (API), also liest das Skript das HTML der Seite aus. Das nennt man Web Scraping.

**Wie die Seite aufgebaut ist:** Jede Terminkarte ist ein Link (`<a>`). Darin stehen beschriftete Bereiche:

```html
<a href="./events-ws26-27/kpmg">
  <div data-framer-name="Raum">  <p>Workshop</p> </div>
  <div data-framer-name="Title"> <p>KPMG</p> </div>
  <div data-framer-name="Title"> <p>KPMG Office Münster, Am Mittelhafen 16</p> </div>
  <time datetime="2026-11-12T16:30:00.000Z">12. November 2026 um 16:30</time>
</a>
```

**Wie das Skript sie liest:**

1. `termine_laden()` lädt die Seite mit `urllib` aus der Python-Standardbibliothek (keine neue Abhängigkeit).
2. `TerminLeser` erbt von `HTMLParser` (ebenfalls Standardbibliothek). Der Parser geht das HTML von vorn nach hinten durch und ruft dabei drei Methoden auf:
   - `handle_starttag`: Bei einem `<a>` beginnt eine neue Karte. Bei einem `<div data-framer-name="...">` merkt sich der Leser, in welchem Bereich er gerade ist. Bei `<time>` übernimmt er das Attribut `datetime`.
   - `handle_data`: Kommt Text, während der Leser in „Raum“ oder „Title“ ist, wird er in der Karte gespeichert.
   - `handle_endtag`: Bei `</a>` ist die Karte zu Ende. `karte_abschliessen()` macht daraus einen Termin, aber nur, wenn Titel und Zeitpunkt vorhanden sind. So werden normale Links (Menü, Fußzeile) aussortiert.
3. Datum und Uhrzeit werden aus dem `datetime`-Attribut geschnitten: Zeichen 0 bis 10 sind das Datum, Zeichen 11 bis 16 die Uhrzeit. Das ist robuster als den deutschen Text „12. November 2026 um 16:30“ zu zerlegen.
4. `ohne_doppelte()` entfernt Dopplungen. Die Website liefert jede Karte mehrfach aus (je eine Fassung für Handy, Tablet und Desktop). Ein Wörterbuch mit dem Schlüssel (Datum, Titel) behält jede nur einmal.
5. Findet das Skript gar keinen Termin, löst es einen Fehler aus. `echte_termine()` in `daten_holen.py` fängt ihn ab: Es gibt eine Warnung, die Terminliste bleibt leer, die Kurse werden trotzdem geschrieben.

**Was du dazu wissen solltest:**

- Die Seite enthält auch vergangene Termine. Das Skript speichert alle; welche „kommend“ sind, entscheidet nur eine Stelle, nämlich `kommendeTermine()` in der Vorlage (DRY).
- Die Texte werden unverändert übernommen. Steht auf der Website ein Tippfehler (aktuell „Votrag“ beim Termin bpr x audalis), steht er auch im Dashboard.
- Schwachstelle von Web Scraping: Ändert das MBP den Aufbau der Seite, findet das Skript nichts mehr. Genau dafür gibt es die Warnung „keine Termine gefunden (Aufbau der Seite geändert?)“.
- Die `robots.txt` der Website erlaubt das Auslesen aller Seiten, und das Skript ruft pro Lauf genau eine Seite ab.

## Schritt 3: Die Datei `daten/markt.json`

```json
{
  "stand": "2026-11-12",
  "beispieldaten": false,
  "indizes": [{"name": "DAX", "einheit": "Punkte", "verlauf": [{"datum": "2026-11-11", "schluss": 26663.0}]}],
  "termine": [{"datum": "2026-11-12", "uhrzeit": "16:30", "art": "Workshop", "titel": "KPMG", "ort": "…", "link": "https://…"}]
}
```

Sie enthält nur Rohdaten: Schlusskurse und Termine. Prozentwerte stehen bewusst nicht darin.

## Schritt 4: Bauen (`bauen.py`)

`vorlage.html` enthält die Stelle `/*MARKTDATEN*/` in einem `<script type="application/json">`. `bauen.py` ersetzt sie durch den Text von `markt.json` und schreibt `dashboard.html`. Dabei wird `</` zu `<\/` umgeschrieben, damit ein Text wie `</script>` in den Daten die Seite nicht vorzeitig beendet.

## Schritt 5: Anzeige im Browser (`vorlage.html`)

Beim Öffnen liest das JavaScript die eingebetteten Daten mit `JSON.parse` und zeichnet alles:

- **`veraenderung(verlauf, tage)`** ist die einzige Stelle, an der Prozentwerte berechnet werden: letzter Schlusskurs geteilt durch den Schlusskurs vor `tage` Handelstagen, minus 1, mal 100. Tag = 1, Woche = 5, Zeitraum = 21 oder 63 Handelstage.
- **`kennzahlen(index)`** sammelt pro Index Stand, Tag, Woche, Zeitraum und den Ausschnitt für das Diagramm.
- **`verlaufZeichnen()`** rechnet jeden Kurs in eine x- und y-Position um und baut daraus einen SVG-Pfad. Die Linie ist grün, wenn der Index im gewählten Zeitraum gestiegen ist, sonst rot. Fährt man mit der Maus darüber, zeigt die Zeile darunter Datum und Kurs.
- **`termineZeichnen()`** zeigt die nächsten fünf Termine mit Kalenderblatt, Art, Uhrzeit und Ort; der Titel führt zur Eventseite des MBP. Der nächste Termin ist hervorgehoben und bekommt „heute“, „morgen“ oder „in N Tagen“.
- **`newsletterText()`** baut aus denselben Kennzahlen und Terminen den Text zum Kopieren.
- **`sicher()`** ersetzt Sonderzeichen wie `<` und `&`, bevor Texte von außen ins HTML eingesetzt werden. Ohne das könnte ein Titel auf der Website fremden Code ins Dashboard einschleusen.
- Die Knöpfe „1 Monat“ und „3 Monate“ ändern nur `zeitraumTage` und rufen `allesZeichnen()` erneut auf.

## Gestaltung

- Farben und Schriften stehen als CSS-Variablen ganz oben (`--marke`, `--auf`, `--ab` …). Das Blau `#004e78` ist die Hauptfarbe der MBP-Website.
- Für den dunklen Modus werden dieselben Variablen neu belegt; der Rest des CSS bleibt gleich.
- Das Raster (`grid` mit `auto-fill`) ordnet die Kacheln je nach Bildschirmbreite in ein bis drei Spalten an, deshalb funktioniert die Seite auch auf dem Handy.

## Befehle

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python daten_holen.py     # echte Kurse und echte MBP-Termine
python bauen.py           # dashboard.html erzeugen
```

## Veröffentlichung (GitHub Pages)

Die Datei `.github/workflows/veroeffentlichen.yml` ist ein Ablaufplan für GitHub Actions. GitHub führt ihn auf eigenen Servern aus:

- **Wann:** täglich um 05:30 UTC (`cron`), bei jedem Hochladen auf den Zweig `main` und auf Knopfdruck im Reiter „Actions“.
- **Was:** Python einrichten, `pip install -r requirements.txt`, `python daten_holen.py`, `python bauen.py`, dann `dashboard.html` als `index.html` in den Ordner `_site` kopieren. GitHub Pages zeigt `index.html` als Startseite.
- **Wohin:** Der zweite Auftrag `veroeffentlichen` stellt den Ordner `_site` online.
- **Fehlerfall:** Liefert kein Index Daten, endet `daten_holen.py` mit einem Fehler, der Lauf bricht ab und die Seite vom Vortag bleibt online.

`daten/markt.json` und `dashboard.html` stehen in `.gitignore`. Sie werden bei jedem Lauf neu erzeugt und gehören deshalb nicht ins Repository, genauso wie die virtuelle Umgebung `.venv`.

## Mögliche Interviewfragen

- **Warum eine JSON-Datei dazwischen?** Holen und Anzeigen sind entkoppelt; man kann die Seite neu bauen, ohne das Internet zu brauchen, und die Daten prüfen, bevor sie angezeigt werden.
- **Warum werden Kennzahlen im Browser berechnet?** Der Zeitraum ist umschaltbar. Würde Python die Prozentwerte vorberechnen, gäbe es dieselbe Formel an zwei Stellen.
- **Warum `HTMLParser` statt BeautifulSoup?** Keine zusätzliche Abhängigkeit; für eine Seite mit klar beschrifteten Bereichen reicht die Standardbibliothek.
- **Was passiert, wenn Yahoo oder die MBP-Seite ausfällt?** Ein fehlender Index oder fehlende Termine führen zu einer Warnung, der Rest wird geschrieben. Nur wenn gar kein Index Daten liefert, bricht das Skript ab und lässt die alte Datei stehen.
- **Was ist die größte Schwäche?** Beide Quellen sind inoffiziell: yfinance nutzt keine garantierte Schnittstelle, und das Auslesen der MBP-Seite hängt an ihrem HTML-Aufbau.
