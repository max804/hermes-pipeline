"""`hermes-validiere <projekt.yaml>` — Validierung außerhalb des Workers.

Für den Architekten (Selbstprüfung vor Abgabe) und den Menschen am
Freigabe-Gate. Exit-Code 0 = valide, 1 = Beanstandungen, 2 = Bedienfehler.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hermes_schemas.projekt import ProjektValidierungsFehler, lade_projekt_yaml


def main() -> int:
    if len(sys.argv) != 2:
        print("Aufruf: hermes-validiere <projekt.yaml>", file=sys.stderr)
        return 2
    pfad = Path(sys.argv[1])
    if not pfad.is_file():
        print(f"Datei nicht gefunden: {pfad}", file=sys.stderr)
        return 2
    try:
        projekt = lade_projekt_yaml(pfad.read_text())
    except ProjektValidierungsFehler as fehler:
        print(fehler.als_kommentar())
        return 1
    print(
        f"OK: {projekt.projekt.name} ({projekt.projekt.domaene}), "
        f"{len(projekt.karten)} Karten, Abhängigkeiten zyklenfrei."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
