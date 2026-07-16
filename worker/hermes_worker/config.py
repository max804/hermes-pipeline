"""Konfiguration des Workers.

Geladen aus YAML; Pfad kommt aus $HERMES_WORKER_CONFIG, sonst
``~/.config/hermes-worker/config.yaml``. Beispiel: ``config.beispiel.yaml``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


def _copier_standard() -> str:
    """copier liegt im selben venv wie der Worker (Laufzeit-Abhängigkeit);
    unter systemd enthält PATH das venv nicht — deshalb absoluter Pfad."""
    kandidat = Path(sys.executable).parent / "copier"
    return str(kandidat) if kandidat.exists() else "copier"


class Spalten(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eingang: str = "Eingang"
    architektur: str = "Architektur"
    freigabe: str = "Freigabe"
    bereit: str = "Bereit"
    in_arbeit: str = "In Arbeit"
    review: str = "Review"
    done: str = "Done"
    blockiert: str = "Blockiert"


class TelegramKonfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Token liegt in einer Datei (nie Klartext in Config oder Repo)
    token_datei: Path | None = None
    chat_id: str | None = None


class WorkerKonfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    board_url: str = "http://127.0.0.1:9119"
    poll_intervall_s: int = 30
    projekte_verzeichnis: Path = Path("~/projekte")
    datenbank: Path = Path("~/worker.db")

    aider_bin: str = "aider"
    coder_modell: str = "ollama_chat/qwen3-coder"
    # Leer = Reviewer aus, Karten bleiben in Review beim Menschen.
    # Modellwahl empirisch per Bug-Diff-Test; muss architektonisch
    # verschieden vom Coder sein (ARCHITEKTUR.md §2/§10).
    reviewer_modell: str = ""
    aider_timeout_s: int = Field(default=1200, description="20 Minuten, harte Regel")
    max_versuche: int = 3

    docker_speicher: str = "8g"
    docker_cpus: str = "4"

    # Copier-Template-Quellen je Domäne (lokaler Pfad oder gh:owner/repo).
    # Nach der Skeleton-Abspaltung auf die Repo-URLs umstellen.
    copier_bin: str = Field(default_factory=_copier_standard)
    template_quellen: dict[str, str] = {
        "web": "~/hermes/hermes-pipeline/templates/skeleton-web",
    }

    spalten: Spalten = Spalten()
    telegram: TelegramKonfig = TelegramKonfig()

    def model_post_init(self, __context) -> None:
        self.projekte_verzeichnis = self.projekte_verzeichnis.expanduser()
        self.datenbank = self.datenbank.expanduser()
        if self.telegram.token_datei:
            self.telegram.token_datei = self.telegram.token_datei.expanduser()


def lade_konfig(pfad: Path | None = None) -> WorkerKonfig:
    if pfad is None:
        umgebung = os.environ.get("HERMES_WORKER_CONFIG")
        pfad = Path(umgebung) if umgebung else Path("~/.config/hermes-worker/config.yaml")
    pfad = pfad.expanduser()
    if not pfad.exists():
        return WorkerKonfig()
    roh = yaml.safe_load(pfad.read_text()) or {}
    return WorkerKonfig.model_validate(roh)
