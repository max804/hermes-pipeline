import subprocess
from pathlib import Path

import pytest

from hermes_worker.board import BoardKarte
from hermes_worker.config import WorkerKonfig
from hermes_worker.state import WorkerZustand


class FakeBoard:
    """In-Memory-Board mit derselben Schnittstelle wie hermes_worker.board.Board."""

    def __init__(self):
        self.karten: dict[str, BoardKarte] = {}
        self.kommentare: list[tuple[str, str]] = []

    def lege_an(self, karten_id: str, spalte: str, beschreibung: str, titel: str = "") -> None:
        self.karten[karten_id] = BoardKarte(karten_id, titel, beschreibung, spalte)

    def karten_in(self, spalte: str) -> list[BoardKarte]:
        return [k for k in self.karten.values() if k.spalte == spalte]

    def verschiebe(self, karten_id: str, spalte: str) -> None:
        alt = self.karten[karten_id]
        self.karten[karten_id] = BoardKarte(alt.id, alt.titel, alt.beschreibung, spalte)

    def kommentiere(self, karten_id: str, text: str) -> None:
        self.kommentare.append((karten_id, text))

    def spalte_von(self, karten_id: str) -> str:
        return self.karten[karten_id].spalte


@pytest.fixture
def board():
    return FakeBoard()


@pytest.fixture
def zustand(tmp_path):
    z = WorkerZustand(tmp_path / "worker.db")
    yield z
    z.schliesse()


@pytest.fixture
def konfig(tmp_path):
    return WorkerKonfig(
        projekte_verzeichnis=tmp_path / "projekte",
        datenbank=tmp_path / "worker.db",
    )


@pytest.fixture
def projekt_repo(konfig) -> Path:
    """Echtes Wegwerf-Git-Repo als Projekt 'homelab-status' mit main-Branch."""
    repo = konfig.projekte_verzeichnis / "homelab-status"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("test\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


KARTE_GUELTIG = """---
projekt: homelab-status
karte: K01
dateien: [app/main.py]
---
Ziel: Hauptmodul anlegen.
"""
