"""End-to-end: echte Copier-Instanziierung aus templates/skeleton-web,
Fake-Board für die Karten. Läuft nur mit installiertem copier (dev-Umgebung)."""

import subprocess


from hermes_schemas.karte import lade_kartenmeta
from hermes_worker import materialisierung
from hermes_worker.worker import Worker
from hermes_worker.aider_runner import AiderErgebnis
from hermes_worker.checks import PruefErgebnis

from tests.conftest import REPO_WURZEL

BEISPIEL_YAML = (REPO_WURZEL / "schemas" / "beispiele" / "projekt.beispiel.yaml").read_text()

FREIGABE_KARTE = f"# Freigegeben\n\n```yaml\n{BEISPIEL_YAML}```\n"


def test_extrahiere_projekt_yaml_aus_zaun():
    assert materialisierung.extrahiere_projekt_yaml(FREIGABE_KARTE) is not None
    assert materialisierung.extrahiere_projekt_yaml("nur text") is None
    roh = materialisierung.extrahiere_projekt_yaml(BEISPIEL_YAML)
    assert roh is not None  # rohes YAML ohne Zaun geht auch


def test_materialisierung_erzeugt_repo_stubs_und_karten(konfig, board):
    projekt = materialisierung.materialisiere(konfig, board, BEISPIEL_YAML)
    repo = konfig.projekte_verzeichnis / "homelab-status"

    # Repo per Copier instanziiert und git-initialisiert auf main
    assert (repo / ".git").is_dir()
    assert (repo / "AGENTS.md").exists() and (repo / "BLAUPAUSE.md").exists()
    branch = subprocess.run(
        ["git", "-C", str(repo), "branch", "--show-current"], capture_output=True, text=True
    ).stdout.strip()
    assert branch == "main"

    # Bauplan und Wahrheit liegen im Repo
    assert (repo / "projekt.yaml").read_text().strip() == BEISPIEL_YAML.strip()
    architektur = (repo / "ARCHITEKTUR.md").read_text()
    assert "homelab-status" in architektur and "kein Auth in v1" in architektur

    # Stubs wartend, nicht scharf
    for nr in ("01", "02", "03"):
        assert (repo / "tests" / "test_karten" / f"test_karte_{nr}.py.wartend").exists()
        assert not (repo / "tests" / "test_karten" / f"test_karte_{nr}.py").exists()

    # Arbeitsbaum sauber committet
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True
    ).stdout
    assert status == ""

    # Karten in topologischer Reihenfolge in Bereit, mit Front-Matter
    karten = board.karten_in(konfig.spalten.bereit)
    assert [k.titel for k in karten] == [
        "[K01] Healthcheck-Modul",
        "[K02] Status-Seite mit Kachel-Grid",
        "[K03] Deploy-Karte",
    ]
    meta, text = lade_kartenmeta(karten[0].beschreibung)
    assert meta.projekt == "homelab-status"
    assert meta.nur_lesen == ["tests/test_karten/test_karte_01.py"]
    assert "Akzeptanzkriterien:" in text
    assert projekt.projekt.domaene == "web"


def test_worker_materialisiert_freigabekarte_und_startet_coder(konfig, board, zustand):
    board.lege_an("42", konfig.spalten.bereit, FREIGABE_KARTE, titel="Freigabe homelab-status")

    aufrufe = []

    def aider(konfig_, repo_, kartentext, dateien, letzte_pruefung="", nur_lesen=None):
        aufrufe.append({"dateien": dateien, "nur_lesen": nur_lesen})
        return AiderErgebnis(timeout=False, exit_code=0, ausgabe_ende="")

    def pruefung(repo_, speicher, cpus):
        return PruefErgebnis(gruen=True, ausgabe_ende="")

    w = Worker(konfig, board, zustand, aider=aider, pruefung=pruefung, melde=lambda *a: None)

    w.tick()  # materialisiert
    assert board.spalte_von("42") == konfig.spalten.done
    assert len(board.karten_in(konfig.spalten.bereit)) == 3

    w.tick()  # arbeitet K01 ab
    repo = konfig.projekte_verzeichnis / "homelab-status"
    karten_branches = subprocess.run(
        ["git", "-C", str(repo), "branch", "--list", "karte/*"], capture_output=True, text=True
    ).stdout
    assert "karte/01-" in karten_branches
    assert aufrufe[0]["nur_lesen"] == ["tests/test_karten/test_karte_01.py"]

    # Stub der Karte 01 wurde auf dem Branch scharfgeschaltet und committet
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", karten_branches.strip().lstrip("* ")], check=True)
    assert (repo / "tests" / "test_karten" / "test_karte_01.py").exists()
    assert not (repo / "tests" / "test_karten" / "test_karte_01.py.wartend").exists()
    log = subprocess.run(
        ["git", "-C", str(repo), "log", "--oneline"], capture_output=True, text=True
    ).stdout
    assert "[K01] Test-Stub aktiviert" in log


def test_invalide_projekt_yaml_blockiert(konfig, board, zustand):
    kaputt = FREIGABE_KARTE.replace("abhaengig_von: [K01]", "abhaengig_von: [K99]")
    board.lege_an("42", konfig.spalten.bereit, kaputt)
    Worker(konfig, board, zustand, melde=lambda *a: None).tick()
    assert board.spalte_von("42") == konfig.spalten.blockiert
    assert any("K99" in text for _, text in board.kommentare)


def test_change_projekt_ohne_neuinstanziierung(konfig, board):
    """Existiert das Repo schon, bleibt ARCHITEKTUR.md unangetastet (Change-Fall)."""
    materialisierung.materialisiere(konfig, board, BEISPIEL_YAML)
    repo = konfig.projekte_verzeichnis / "homelab-status"
    (repo / "ARCHITEKTUR.md").write_text("# Von Menschen gepflegte Wahrheit\n")
    subprocess.run(["git", "-C", str(repo), "commit", "-qam", "wahrheit"], check=True)

    materialisierung.materialisiere(konfig, board, BEISPIEL_YAML)
    assert (repo / "ARCHITEKTUR.md").read_text() == "# Von Menschen gepflegte Wahrheit\n"
