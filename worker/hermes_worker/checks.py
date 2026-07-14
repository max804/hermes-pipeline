"""Die harte Wahrheit: `make check` im Container (ARCHITEKTUR.md §7).

Sandbox-Kontrakt wörtlich aus dem Entwurf: kein Netz, kein Home-Verzeichnis,
harte Ressourcengrenzen. Das Image kommt aus Dockerfile.check des Skeletons.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PruefErgebnis:
    gruen: bool
    ausgabe_ende: str


def make_check(repo: Path, speicher: str = "8g", cpus: str = "4") -> PruefErgebnis:
    bild = f"hermes-check-{repo.name}"
    bau = subprocess.run(
        ["docker", "build", "-q", "-f", "Dockerfile.check", "-t", bild, "."],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if bau.returncode != 0:
        return PruefErgebnis(False, "Docker-Build fehlgeschlagen:\n" + bau.stderr[-2000:])

    lauf = subprocess.run(
        [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", speicher,
            "--cpus", cpus,
            "-v", f"{repo}:/work",
            "-w", "/work",
            bild,
            "make", "check",
        ],
        capture_output=True,
        text=True,
        timeout=1800,
    )
    ausgabe = (lauf.stdout + "\n" + lauf.stderr)[-2000:]
    return PruefErgebnis(gruen=lauf.returncode == 0, ausgabe_ende=ausgabe)
