"""Dünner Client für die Hermes-Kanban-Board-API (Port 9119).

ACHTUNG — Endpunkt-Annahmen: Die genauen Pfade der bestehenden Board-API
sind hier angenommen und müssen beim ersten Test gegen das echte Board
verifiziert werden. Wenn sie abweichen, ist DIESE Datei die einzige
Anpassungsstelle; der Rest des Workers kennt nur die Methoden dieser Klasse.

Angenommene API:
    GET  /api/karten?spalte=<name>       → [{id, titel, beschreibung, spalte}]
    POST /api/karten/<id>/verschieben    {"spalte": "<name>"}
    POST /api/karten/<id>/kommentare     {"text": "…"}
"""

from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class BoardKarte:
    id: str
    titel: str
    beschreibung: str
    spalte: str


class Board:
    def __init__(self, basis_url: str, timeout_s: int = 10):
        self.basis_url = basis_url.rstrip("/")
        self.timeout_s = timeout_s

    def karten_in(self, spalte: str) -> list[BoardKarte]:
        antwort = requests.get(
            f"{self.basis_url}/api/karten",
            params={"spalte": spalte},
            timeout=self.timeout_s,
        )
        antwort.raise_for_status()
        return [
            BoardKarte(
                id=str(k["id"]),
                titel=k.get("titel", ""),
                beschreibung=k.get("beschreibung", ""),
                spalte=k.get("spalte", spalte),
            )
            for k in antwort.json()
        ]

    def verschiebe(self, karten_id: str, spalte: str) -> None:
        antwort = requests.post(
            f"{self.basis_url}/api/karten/{karten_id}/verschieben",
            json={"spalte": spalte},
            timeout=self.timeout_s,
        )
        antwort.raise_for_status()

    def kommentiere(self, karten_id: str, text: str) -> None:
        antwort = requests.post(
            f"{self.basis_url}/api/karten/{karten_id}/kommentare",
            json={"text": text},
            timeout=self.timeout_s,
        )
        antwort.raise_for_status()
