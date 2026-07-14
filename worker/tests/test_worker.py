import subprocess

from hermes_worker.aider_runner import AiderErgebnis
from hermes_worker.checks import PruefErgebnis
from hermes_worker.worker import Worker

from tests.conftest import KARTE_GUELTIG

INTAKE_UNVOLLSTAENDIG = "# Intake: Neues Projekt\n\n## Domäne (Pflicht)\n\n- [ ] `web`\n"

INTAKE_GUELTIG = """# Intake: Neues Projekt

## Domäne (Pflicht)

- [x] `web`

## Projektname (Pflicht)

homelab-status

## Ziel (Pflicht, 3–5 Sätze)

Erster Satz hier. Zweiter Satz hier. Dritter Satz hier.

## Muss-Funktionen (Pflicht)

- Healthchecks

## Explizit nicht (Pflicht)

- kein Auth

## Nur bei Domäne `web`: Seiten-/Routenliste (Pflicht)

| Route | Zweck |
|---|---|
| `/` | Dashboard |
"""


def _aider(timeout=False, exit_code=0):
    def lauf(konfig, repo, kartentext, dateien, letzte_pruefung=""):
        lauf.aufrufe.append({"kartentext": kartentext, "letzte_pruefung": letzte_pruefung})
        return AiderErgebnis(timeout=timeout, exit_code=exit_code, ausgabe_ende="")
    lauf.aufrufe = []
    return lauf


def _pruefung(gruen=True, ausgabe="1 failed"):
    def lauf(repo, speicher, cpus):
        return PruefErgebnis(gruen=gruen, ausgabe_ende="" if gruen else ausgabe)
    return lauf


def _melde():
    def lauf(telegram_konfig, text):
        lauf.meldungen.append(text)
    lauf.meldungen = []
    return lauf


def _worker(konfig, board, zustand, **kwargs):
    kwargs.setdefault("aider", _aider())
    kwargs.setdefault("pruefung", _pruefung())
    kwargs.setdefault("melde", _melde())
    return Worker(konfig, board, zustand, **kwargs)


# --- Eingang ---------------------------------------------------------------


def test_gueltiger_intake_wandert_nach_architektur(konfig, board, zustand):
    board.lege_an("1", konfig.spalten.eingang, INTAKE_GUELTIG)
    _worker(konfig, board, zustand).tick()
    assert board.spalte_von("1") == konfig.spalten.architektur
    assert board.kommentare == []


def test_unvollstaendiger_intake_wird_genau_einmal_kommentiert(konfig, board, zustand):
    board.lege_an("1", konfig.spalten.eingang, INTAKE_UNVOLLSTAENDIG)
    w = _worker(konfig, board, zustand)
    w.tick()
    w.tick()
    assert board.spalte_von("1") == konfig.spalten.eingang
    assert len(board.kommentare) == 1
    assert "unvollständig" in board.kommentare[0][1]


# --- Coder-Schleife ----------------------------------------------------------


def test_gruener_lauf_wandert_nach_review(konfig, board, zustand, projekt_repo):
    board.lege_an("7", konfig.spalten.bereit, KARTE_GUELTIG, titel="Hauptmodul")
    _worker(konfig, board, zustand).tick()
    assert board.spalte_von("7") == konfig.spalten.review
    branches = subprocess.run(
        ["git", "-C", str(projekt_repo), "branch", "--list", "karte/01-*"],
        capture_output=True, text=True,
    ).stdout
    assert "karte/01-hauptmodul" in branches  # Branch bleibt bis zum Squash-Merge


def test_roter_lauf_geht_zurueck_auf_bereit_und_blockiert_nach_drei(
    konfig, board, zustand, projekt_repo
):
    board.lege_an("7", konfig.spalten.bereit, KARTE_GUELTIG, titel="Hauptmodul")
    melde = _melde()
    w = _worker(konfig, board, zustand, pruefung=_pruefung(gruen=False), melde=melde)

    w.tick()
    assert board.spalte_von("7") == konfig.spalten.bereit
    w.tick()
    assert board.spalte_von("7") == konfig.spalten.bereit
    w.tick()
    assert board.spalte_von("7") == konfig.spalten.blockiert
    assert zustand.versuche("7") == 3
    assert len(melde.meldungen) == 1 and "blockiert" in melde.meldungen[0]
    # Branch bleibt als Beweisstück
    branches = subprocess.run(
        ["git", "-C", str(projekt_repo), "branch"], capture_output=True, text=True
    ).stdout
    assert "karte/01-hauptmodul" in branches


def test_fix_runde_bekommt_letzte_pruefausgabe(konfig, board, zustand, projekt_repo):
    board.lege_an("7", konfig.spalten.bereit, KARTE_GUELTIG, titel="Hauptmodul")
    aider = _aider()
    w = _worker(konfig, board, zustand, aider=aider,
                pruefung=_pruefung(gruen=False, ausgabe="FAILED test_karte_01"))
    w.tick()
    w.tick()
    assert aider.aufrufe[0]["letzte_pruefung"] == ""
    assert "FAILED test_karte_01" in aider.aufrufe[1]["letzte_pruefung"]


def test_timeout_verwirft_branch_und_zaehlt(konfig, board, zustand, projekt_repo):
    board.lege_an("7", konfig.spalten.bereit, KARTE_GUELTIG, titel="Hauptmodul")
    w = _worker(konfig, board, zustand, aider=_aider(timeout=True))
    w.tick()
    assert board.spalte_von("7") == konfig.spalten.bereit
    assert zustand.versuche("7") == 1
    branches = subprocess.run(
        ["git", "-C", str(projekt_repo), "branch"], capture_output=True, text=True
    ).stdout
    assert "karte/" not in branches  # verworfen


def test_kaputtes_kartenformat_blockiert(konfig, board, zustand):
    board.lege_an("7", konfig.spalten.bereit, "Nur Text ohne Front-Matter")
    _worker(konfig, board, zustand).tick()
    assert board.spalte_von("7") == konfig.spalten.blockiert
    assert any("Kartenformat" in text for _, text in board.kommentare)


def test_fehlendes_repo_blockiert(konfig, board, zustand):
    board.lege_an("7", konfig.spalten.bereit, KARTE_GUELTIG)
    _worker(konfig, board, zustand).tick()
    assert board.spalte_von("7") == konfig.spalten.blockiert
    assert any("Repo fehlt" in text for _, text in board.kommentare)


def test_neustart_setzt_laufende_karten_zurueck(konfig, board, zustand, projekt_repo):
    board.lege_an("7", konfig.spalten.in_arbeit, KARTE_GUELTIG)
    zustand.registriere("7", "homelab-status", "karte/01-hauptmodul")
    zustand.setze_laufend("7", True)

    _worker(konfig, board, zustand).bereinige_nach_neustart()

    assert board.spalte_von("7") == konfig.spalten.bereit
    assert zustand.versuche("7") == 1
    assert zustand.laufende_karten() == []
