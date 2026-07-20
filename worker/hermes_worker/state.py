"""Worker-Zustand: eine winzige SQLite (ARCHITEKTUR.md §4).

Karte ↔ laufender Prozess ↔ Versuchszähler — damit überlebt der Worker den
eigenen Neustart sauber. Dazu ein Duplikatschutz für Intake-Kommentare,
damit eine unvollständige Karte nicht alle 30 Sekunden neu kommentiert wird.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS karten (
    karten_id     TEXT PRIMARY KEY,
    projekt       TEXT NOT NULL,
    branch        TEXT NOT NULL,
    versuche      INTEGER NOT NULL DEFAULT 0,
    laeuft        INTEGER NOT NULL DEFAULT 0,
    letzte_pruefung TEXT NOT NULL DEFAULT '',
    aktualisiert  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS intake_kommentare (
    karten_id    TEXT NOT NULL,
    inhalt_hash  TEXT NOT NULL,
    PRIMARY KEY (karten_id, inhalt_hash)
);
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class WorkerZustand:
    def __init__(self, pfad: Path | str):
        self._db = sqlite3.connect(str(pfad))
        self._db.executescript(_SCHEMA)
        self._db.commit()

    def schliesse(self) -> None:
        self._db.close()

    # --- Karten / Versuche -------------------------------------------------

    def registriere(self, karten_id: str, projekt: str, branch: str) -> None:
        self._db.execute(
            "INSERT INTO karten (karten_id, projekt, branch, aktualisiert) VALUES (?,?,?,?) "
            "ON CONFLICT(karten_id) DO UPDATE SET projekt=excluded.projekt, "
            "branch=excluded.branch, aktualisiert=excluded.aktualisiert",
            (karten_id, projekt, branch, _jetzt()),
        )
        self._db.commit()

    def branch_von(self, karten_id: str) -> str | None:
        zeile = self._db.execute(
            "SELECT branch FROM karten WHERE karten_id=?", (karten_id,)
        ).fetchone()
        return zeile[0] if zeile else None

    def versuche(self, karten_id: str) -> int:
        zeile = self._db.execute(
            "SELECT versuche FROM karten WHERE karten_id=?", (karten_id,)
        ).fetchone()
        return zeile[0] if zeile else 0

    def setze_versuche(self, karten_id: str, wert: int) -> None:
        self._db.execute(
            "UPDATE karten SET versuche=?, aktualisiert=? WHERE karten_id=?",
            (wert, _jetzt(), karten_id),
        )
        self._db.commit()

    def erhoehe_versuche(self, karten_id: str) -> int:
        self._db.execute(
            "UPDATE karten SET versuche=versuche+1, aktualisiert=? WHERE karten_id=?",
            (_jetzt(), karten_id),
        )
        self._db.commit()
        return self.versuche(karten_id)

    def setze_laufend(self, karten_id: str, laeuft: bool) -> None:
        self._db.execute(
            "UPDATE karten SET laeuft=?, aktualisiert=? WHERE karten_id=?",
            (1 if laeuft else 0, _jetzt(), karten_id),
        )
        self._db.commit()

    def laufende_karten(self) -> list[tuple[str, str, str]]:
        """(karten_id, projekt, branch) aller als laufend markierten Karten."""
        return list(
            self._db.execute("SELECT karten_id, projekt, branch FROM karten WHERE laeuft=1")
        )

    def setze_letzte_pruefung(self, karten_id: str, ausgabe: str) -> None:
        self._db.execute(
            "UPDATE karten SET letzte_pruefung=?, aktualisiert=? WHERE karten_id=?",
            (ausgabe, _jetzt(), karten_id),
        )
        self._db.commit()

    def letzte_pruefung(self, karten_id: str) -> str:
        zeile = self._db.execute(
            "SELECT letzte_pruefung FROM karten WHERE karten_id=?", (karten_id,)
        ).fetchone()
        return zeile[0] if zeile else ""

    # --- Intake-Kommentar-Duplikatschutz ------------------------------------

    def intake_bereits_kommentiert(self, karten_id: str, inhalt_hash: str) -> bool:
        zeile = self._db.execute(
            "SELECT 1 FROM intake_kommentare WHERE karten_id=? AND inhalt_hash=?",
            (karten_id, inhalt_hash),
        ).fetchone()
        return zeile is not None

    def merke_intake_kommentar(self, karten_id: str, inhalt_hash: str) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO intake_kommentare (karten_id, inhalt_hash) VALUES (?,?)",
            (karten_id, inhalt_hash),
        )
        self._db.commit()
