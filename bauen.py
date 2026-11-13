"""Setzt daten/markt.json in vorlage.html ein und schreibt dashboard.html.

Aufruf:
    python bauen.py             vollständige HTML-Datei zum Öffnen im Browser
    python bauen.py --fragment  nur der Seiteninhalt (für die Veröffentlichung als Artifact)
"""
import argparse
from pathlib import Path

WURZEL = Path(__file__).parent
PLATZHALTER = "/*MARKTDATEN*/"
GERUEST = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
{inhalt}
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragment", action="store_true", help="ohne HTML-Gerüst ausgeben")
    argumente = parser.parse_args()

    vorlage = (WURZEL / "vorlage.html").read_text(encoding="utf-8")
    marktdaten = (WURZEL / "daten" / "markt.json").read_text(encoding="utf-8")
    inhalt = vorlage.replace(PLATZHALTER, marktdaten.replace("</", "<\\/"))

    ausgabe = WURZEL / "dashboard.html"
    ausgabe.write_text(inhalt if argumente.fragment else GERUEST.format(inhalt=inhalt), encoding="utf-8")
    print(f"Geschrieben: {ausgabe}")


if __name__ == "__main__":
    main()
