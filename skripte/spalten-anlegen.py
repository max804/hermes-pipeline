#!/usr/bin/env python3
"""Kanban-Spalten anlegen (ARCHITEKTUR.md §3).

Seit hermes-board (`board/`) das Board stellt, ist dieses Skript nur noch
für Sonderfälle nötig — das Board legt die acht Standard-Spalten beim
ersten Start selbst an. Nutzbar z. B. für zusätzliche Spalten:

    python3 skripte/spalten-anlegen.py [board-url]
"""

import sys

import requests

SPALTEN = [
    "Eingang",
    "Architektur",
    "Freigabe",
    "Bereit",
    "In Arbeit",
    "Review",
    "Done",
    "Blockiert",
]


def main() -> int:
    basis = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9119").rstrip("/")
    try:
        vorhandene = {
            s.get("name") for s in requests.get(f"{basis}/api/spalten", timeout=10).json()
        }
    except requests.RequestException as e:
        print(f"Board nicht erreichbar unter {basis}: {e}", file=sys.stderr)
        return 1

    for name in SPALTEN:
        if name in vorhandene:
            print(f"  vorhanden: {name}")
            continue
        antwort = requests.post(f"{basis}/api/spalten", json={"name": name}, timeout=10)
        antwort.raise_for_status()
        print(f"  angelegt:  {name}")
    print("Fertig — Reihenfolge im Board-UI prüfen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
