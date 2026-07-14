"""Ein Aider-Lauf = eine Karte (ARCHITEKTUR.md §2, §4).

Kontext pro Lauf: Kartentext + ARCHITEKTUR.md + AGENTS.md (beide aus dem
Projekt-Repo, read-only). Harter 20-Minuten-Timeout; der Aufrufer behandelt
Timeout wie Abbruch (Branch verwerfen, Karte zurück auf *Bereit*).
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hermes_worker.config import WorkerKonfig


@dataclass(frozen=True)
class AiderErgebnis:
    timeout: bool
    exit_code: int
    ausgabe_ende: str


def fuehre_aider_aus(
    konfig: WorkerKonfig,
    repo: Path,
    kartentext: str,
    dateien: list[str],
    letzte_pruefung: str = "",
) -> AiderErgebnis:
    auftrag = kartentext
    if letzte_pruefung:
        auftrag += (
            "\n\n--- Fix-Runde ---\n"
            "Der letzte Lauf ist an `make check` gescheitert. Behebe die Ursache:\n\n"
            f"{letzte_pruefung}"
        )

    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", prefix="hermes-karte-", delete=False
    ) as f:
        f.write(auftrag)
        auftragsdatei = f.name

    kommando = [
        konfig.aider_bin,
        "--yes-always",
        "--model", konfig.coder_modell,
        "--message-file", auftragsdatei,
        "--read", "ARCHITEKTUR.md",
        "--read", "AGENTS.md",
        *dateien,
    ]
    try:
        lauf = subprocess.run(
            kommando,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=konfig.aider_timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        ende = ((e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""))[-2000:]
        return AiderErgebnis(timeout=True, exit_code=-1, ausgabe_ende=ende)
    finally:
        Path(auftragsdatei).unlink(missing_ok=True)

    ausgabe = (lauf.stdout + "\n" + lauf.stderr)[-2000:]
    return AiderErgebnis(timeout=False, exit_code=lauf.returncode, ausgabe_ende=ausgabe)
