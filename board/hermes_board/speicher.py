"""SQLite-Speicher des Boards — langweilig und debugbar (Anti-Fehler-D).

Eine Verbindung pro Operation, WAL-Modus: verträgt Worker-Polling und
UI-Zugriffe gleichzeitig ohne Locking-Akrobatik.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Die Spalten aus ARCHITEKTUR.md §3 — beim ersten Start angelegt.
STANDARD_SPALTEN = [
    "Eingang",
    "Architektur",
    "Freigabe",
    "Bereit",
    "In Arbeit",
    "Review",
    "Done",
    "Blockiert",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS spalten (
    name      TEXT PRIMARY KEY,
    position  INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS karten (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titel        TEXT NOT NULL,
    beschreibung TEXT NOT NULL DEFAULT '',
    spalte       TEXT NOT NULL REFERENCES spalten(name),
    angelegt     TEXT NOT NULL,
    aktualisiert TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kommentare (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    karten_id INTEGER NOT NULL REFERENCES karten(id),
    text      TEXT NOT NULL,
    zeit      TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Karte:
    id: int
    titel: str
    beschreibung: str
    spalte: str
    angelegt: str
    aktualisiert: str


@dataclass(frozen=True)
class Kommentar:
    id: int
    karten_id: int
    text: str
    zeit: str


class KarteNichtGefunden(Exception):
    pass


class SpalteNichtGefunden(Exception):
    pass


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Speicher:
    def __init__(self, pfad: Path | str):
        self.pfad = str(pfad)
        with self._verbindung() as db:
            db.executescript(_SCHEMA)
        if not self.spalten():
            for name in STANDARD_SPALTEN:
                self.spalte_anlegen(name)

    def _verbindung(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.pfad, timeout=10)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        db.row_factory = sqlite3.Row
        return db

    # --- Spalten -------------------------------------------------------------

    def spalten(self) -> list[str]:
        with self._verbindung() as db:
            return [z["name"] for z in db.execute("SELECT name FROM spalten ORDER BY position")]

    def spalte_anlegen(self, name: str) -> None:
        with self._verbindung() as db:
            vorhanden = db.execute("SELECT 1 FROM spalten WHERE name=?", (name,)).fetchone()
            if vorhanden:
                return
            naechste = db.execute("SELECT COALESCE(MAX(position),0)+1 FROM spalten").fetchone()[0]
            db.execute("INSERT INTO spalten (name, position) VALUES (?,?)", (name, naechste))

    def _pruefe_spalte(self, db: sqlite3.Connection, name: str) -> None:
        if not db.execute("SELECT 1 FROM spalten WHERE name=?", (name,)).fetchone():
            raise SpalteNichtGefunden(name)

    # --- Karten --------------------------------------------------------------

    def karten(self, spalte: str | None = None) -> list[Karte]:
        """Reihenfolge = Anlage-Reihenfolge (der Vertrag, auf den sich die
        topologische Karten-Erzeugung der Materialisierung verlässt)."""
        with self._verbindung() as db:
            if spalte is None:
                zeilen = db.execute("SELECT * FROM karten ORDER BY id")
            else:
                zeilen = db.execute("SELECT * FROM karten WHERE spalte=? ORDER BY id", (spalte,))
            return [Karte(**dict(z)) for z in zeilen]

    def karte(self, karten_id: int) -> Karte:
        with self._verbindung() as db:
            zeile = db.execute("SELECT * FROM karten WHERE id=?", (karten_id,)).fetchone()
        if zeile is None:
            raise KarteNichtGefunden(str(karten_id))
        return Karte(**dict(zeile))

    def karte_anlegen(self, titel: str, beschreibung: str, spalte: str) -> int:
        with self._verbindung() as db:
            self._pruefe_spalte(db, spalte)
            cursor = db.execute(
                "INSERT INTO karten (titel, beschreibung, spalte, angelegt, aktualisiert) "
                "VALUES (?,?,?,?,?)",
                (titel, beschreibung, spalte, _jetzt(), _jetzt()),
            )
            return int(cursor.lastrowid)

    def verschiebe(self, karten_id: int, spalte: str) -> None:
        with self._verbindung() as db:
            self._pruefe_spalte(db, spalte)
            geaendert = db.execute(
                "UPDATE karten SET spalte=?, aktualisiert=? WHERE id=?",
                (spalte, _jetzt(), karten_id),
            ).rowcount
        if geaendert == 0:
            raise KarteNichtGefunden(str(karten_id))

    def beschreibung_setzen(self, karten_id: int, titel: str, beschreibung: str) -> None:
        with self._verbindung() as db:
            geaendert = db.execute(
                "UPDATE karten SET titel=?, beschreibung=?, aktualisiert=? WHERE id=?",
                (titel, beschreibung, _jetzt(), karten_id),
            ).rowcount
        if geaendert == 0:
            raise KarteNichtGefunden(str(karten_id))

    # --- Kommentare ----------------------------------------------------------

    def kommentiere(self, karten_id: int, text: str) -> int:
        self.karte(karten_id)  # wirft bei unbekannter Karte
        with self._verbindung() as db:
            cursor = db.execute(
                "INSERT INTO kommentare (karten_id, text, zeit) VALUES (?,?,?)",
                (karten_id, text, _jetzt()),
            )
            return int(cursor.lastrowid)

    def kommentare(self, karten_id: int) -> list[Kommentar]:
        with self._verbindung() as db:
            zeilen = db.execute(
                "SELECT * FROM kommentare WHERE karten_id=? ORDER BY id", (karten_id,)
            )
            return [Kommentar(**dict(z)) for z in zeilen]
