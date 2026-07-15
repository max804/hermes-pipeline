"""Materialisierung (ARCHITEKTUR.md §3, Schritt 4).

Nach der Freigabe deterministisch — kein LLM-Lauf nötig, denn die
projekt.yaml enthält bereits alles (Begründung: DECISIONS.md im Meta-Repo):

1. Projekt-Repo per Copier instanziieren (entfällt bei Change-Projekten)
2. projekt.yaml ins Repo (die Historie beginnt mit ihrem eigenen Bauplan)
3. ARCHITEKTUR.md aus der projekt.yaml rendern (nur wenn noch Platzhalter)
4. Test-Stubs als tests/test_karten/test_karte_<nr>.py.wartend — scharf
   geschaltet erst beim Start der jeweiligen Karte (repo.aktiviere_test_stub),
   damit `make check` nie an den roten Stubs SPÄTERER Karten scheitert
5. Commit auf main
6. Karten in topologischer Reihenfolge via Board-API nach *Bereit*
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from hermes_schemas.karte import KartenMeta, baue_kartenbeschreibung
from hermes_schemas.projekt import Karte, ProjektYaml, lade_projekt_yaml

from hermes_worker import repo as git
from hermes_worker.config import WorkerKonfig

log = logging.getLogger(__name__)

_YAML_ZAUN = re.compile(r"```ya?ml\n(?P<yaml>.*?)```", re.DOTALL)


class MaterialisierungsFehler(Exception):
    pass


def extrahiere_projekt_yaml(beschreibung: str) -> str | None:
    """Freigabe-Karten tragen die projekt.yaml als ```yaml-Block (oder roh).
    Liefert den YAML-Text oder None, wenn die Karte keiner ist."""
    treffer = _YAML_ZAUN.search(beschreibung)
    text = treffer.group("yaml") if treffer else beschreibung
    if "projekt:" in text and "karten:" in text:
        return text
    return None


def _topologisch(karten: list[Karte]) -> list[Karte]:
    """Stabile topologische Sortierung (Schema garantiert Zyklenfreiheit)."""
    erledigt: set[str] = set()
    offen = list(karten)
    reihenfolge: list[Karte] = []
    while offen:
        rest = []
        for k in offen:
            if all(d in erledigt for d in k.abhaengig_von):
                reihenfolge.append(k)
                erledigt.add(k.id)
            else:
                rest.append(k)
        if len(rest) == len(offen):  # nur bei invalidem Input erreichbar
            raise MaterialisierungsFehler(f"Abhängigkeiten unauflösbar: {[k.id for k in rest]}")
        offen = rest
    return reihenfolge


def _instanziiere(konfig: WorkerKonfig, projekt: ProjektYaml, ziel: Path) -> None:
    quelle = konfig.template_quellen.get(projekt.projekt.domaene)
    if not quelle:
        raise MaterialisierungsFehler(
            f"Keine Template-Quelle für Domäne '{projekt.projekt.domaene}' konfiguriert"
        )
    lauf = subprocess.run(
        [
            konfig.copier_bin, "copy", "--trust", "--defaults",
            "--data", f"projektname={projekt.projekt.name}",
            "--data", f"beschreibung={projekt.projekt.beschreibung.strip()}",
            str(Path(quelle).expanduser()), str(ziel),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if lauf.returncode != 0:
        raise MaterialisierungsFehler(f"copier copy fehlgeschlagen:\n{lauf.stderr[-2000:]}")
    for kommando in (
        ["git", "init", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "[K00] Skeleton instanziiert"],
    ):
        subprocess.run(kommando, cwd=ziel, check=True, capture_output=True, timeout=120)


def _rendere_architektur(projekt: ProjektYaml) -> str:
    a = projekt.architektur
    zeilen = [
        f"# ARCHITEKTUR — {projekt.projekt.name}",
        "",
        projekt.projekt.beschreibung.strip(),
        "",
        "## Module",
        *[f"- {m}" for m in a.module],
        "",
        "## Datenmodell",
        a.datenmodell.strip(),
    ]
    if a.routen:
        zeilen += ["", "## Routen", *[f"- {r}" for r in a.routen]]
    if a.geraeteprofile:
        zeilen += ["", "## Geräteprofile", *[f"- {g}" for g in a.geraeteprofile]]
    zeilen += [
        "",
        "## Explizit ausgeschlossen",
        *[f"- {x}" for x in a.ausgeschlossen],
        "",
        "## Karten",
        "| ID | Titel | Dateien |",
        "|---|---|---|",
        *[f"| {k.id} | {k.titel} | {', '.join(k.dateien)} |" for k in projekt.karten],
        "",
    ]
    return "\n".join(zeilen)


def _stub_pfad(karten_id: str) -> str:
    return f"tests/test_karten/test_karte_{karten_id.lstrip('K')}.py"


def _kartentext(karte: Karte) -> str:
    akzeptanz = "\n".join(f"- {a}" for a in karte.akzeptanz)
    return (
        f"{karte.ziel}\n\n"
        f"Akzeptanzkriterien:\n{akzeptanz}\n\n"
        f"Der Test {_stub_pfad(karte.id)} ist der Vertrag dieser Karte: "
        f"grün machen, nicht editieren (AGENTS.md)."
    )


def materialisiere(konfig: WorkerKonfig, board, yaml_text: str) -> ProjektYaml:
    """Wirft ProjektValidierungsFehler / MaterialisierungsFehler; sonst fertig."""
    projekt = lade_projekt_yaml(yaml_text)
    ziel = konfig.projekte_verzeichnis / projekt.projekt.name

    neuprojekt = not (ziel / ".git").is_dir()
    if neuprojekt:
        log.info("materialisierung: instanziiere %s nach %s", projekt.projekt.name, ziel)
        _instanziiere(konfig, projekt, ziel)

    (ziel / "projekt.yaml").write_text(yaml_text.strip() + "\n")

    architektur = ziel / "ARCHITEKTUR.md"
    if neuprojekt or "Noch nicht materialisiert" in architektur.read_text():
        architektur.write_text(_rendere_architektur(projekt))
    # Bei Change-Projekten bleibt ARCHITEKTUR.md unangetastet — ihre
    # Aktualisierung ist Akzeptanzkriterium der Change-Karten selbst.

    stub_verzeichnis = ziel / "tests" / "test_karten"
    stub_verzeichnis.mkdir(parents=True, exist_ok=True)
    for karte in projekt.karten:
        wartend = ziel / (_stub_pfad(karte.id) + ".wartend")
        wartend.write_text(karte.test_stub)

    git.commit_alle(ziel, f"Materialisierung: projekt.yaml, ARCHITEKTUR.md, {len(projekt.karten)} Test-Stubs")

    for karte in _topologisch(projekt.karten):
        meta = KartenMeta(
            projekt=projekt.projekt.name,
            karte=karte.id,
            dateien=karte.dateien,
            nur_lesen=[_stub_pfad(karte.id)],
        )
        board.karte_anlegen(
            titel=f"[{karte.id}] {karte.titel}",
            beschreibung=baue_kartenbeschreibung(meta, _kartentext(karte)),
            spalte=konfig.spalten.bereit,
        )
    log.info("materialisierung: %d karten nach '%s' angelegt", len(projekt.karten), konfig.spalten.bereit)
    return projekt
