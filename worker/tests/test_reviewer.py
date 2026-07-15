import subprocess

import pytest

from hermes_worker.reviewer import ReviewErgebnis, parse_urteil
from hermes_worker.worker import Worker

from tests.conftest import KARTE_GUELTIG


# --- Urteils-Parser -----------------------------------------------------------


def test_parse_ok():
    ergebnis = parse_urteil("Analyse …\n\nURTEIL: OK — Karte sauber umgesetzt.")
    assert ergebnis.urteil == "ok"


def test_parse_fix_mit_befunden():
    ausgabe = "Denkprozess …\nURTEIL: FIX\n1. app/x.py: Farbe erfunden — Katalog nutzen"
    ergebnis = parse_urteil(ausgabe)
    assert ergebnis.urteil == "fix"
    assert "Katalog nutzen" in ergebnis.befunde


def test_parse_letztes_urteil_gewinnt():
    ausgabe = "Wenn es schlecht wäre, würde ich URTEIL: FIX sagen.\n\nURTEIL: OK — passt."
    assert parse_urteil(ausgabe).urteil == "ok"


def test_parse_ohne_urteil_ist_unklar():
    assert parse_urteil("Ich bin nur ein Sprachmodell.").urteil == "unklar"


# --- Review-Fluss im Worker ----------------------------------------------------


@pytest.fixture
def review_konfig(konfig):
    konfig.reviewer_modell = "ollama_chat/zweitmodell"
    return konfig


@pytest.fixture
def karte_in_review(review_konfig, board, zustand, projekt_repo):
    """Karte 7 liegt in Review, ihr Branch trägt einen Commit."""
    subprocess.run(
        ["git", "-C", str(projekt_repo), "checkout", "-q", "-b", "karte/01-hauptmodul"],
        check=True,
    )
    (projekt_repo / "app.py").write_text("print('hallo')\n")
    subprocess.run(["git", "-C", str(projekt_repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(projekt_repo), "commit", "-qm", "wip"], check=True)
    subprocess.run(["git", "-C", str(projekt_repo), "checkout", "-q", "main"], check=True)

    board.lege_an("7", review_konfig.spalten.review, KARTE_GUELTIG, titel="[K01] Hauptmodul")
    zustand.registriere("7", "homelab-status", "karte/01-hauptmodul")
    return projekt_repo


def _worker_mit_urteil(konfig, board, zustand, urteil, befunde="1. app/x.py: kaputt"):
    def review(konfig_, repo_, branch, kartentext):
        return ReviewErgebnis(urteil=urteil, befunde=befunde if urteil == "fix" else "", ausgabe_ende="")
    melde = []
    w = Worker(konfig, board, zustand, review=review, melde=lambda _, text: melde.append(text))
    return w, melde


def test_review_ok_squash_merged_nach_done(review_konfig, board, zustand, karte_in_review):
    w, _ = _worker_mit_urteil(review_konfig, board, zustand, "ok")
    w._verarbeite_review()
    assert board.spalte_von("7") == review_konfig.spalten.done

    log = subprocess.run(
        ["git", "-C", str(karte_in_review), "log", "--oneline", "main"],
        capture_output=True, text=True,
    ).stdout
    assert "[K01] Hauptmodul" in log
    assert (karte_in_review / "app.py").exists()
    branches = subprocess.run(
        ["git", "-C", str(karte_in_review), "branch"], capture_output=True, text=True
    ).stdout
    assert "karte/" not in branches  # Branch nach Merge gelöscht


def test_review_fix_geht_als_rueckläufer_nach_bereit(review_konfig, board, zustand, karte_in_review):
    w, _ = _worker_mit_urteil(review_konfig, board, zustand, "fix")
    w._verarbeite_review()
    assert board.spalte_von("7") == review_konfig.spalten.bereit
    assert zustand.versuche("7") == 1
    assert "kaputt" in zustand.letzte_pruefung("7")
    assert any("Fix-Rückläufer" in text for _, text in board.kommentare)


def test_review_fix_blockiert_ab_drittem_versuch(review_konfig, board, zustand, karte_in_review):
    zustand.erhoehe_versuche("7")
    zustand.erhoehe_versuche("7")
    w, melde = _worker_mit_urteil(review_konfig, board, zustand, "fix")
    w._verarbeite_review()
    assert board.spalte_von("7") == review_konfig.spalten.blockiert
    assert melde and "blockiert" in melde[0]


def test_review_unklar_eskaliert(review_konfig, board, zustand, karte_in_review):
    w, melde = _worker_mit_urteil(review_konfig, board, zustand, "unklar")
    w._verarbeite_review()
    assert board.spalte_von("7") == review_konfig.spalten.blockiert
    assert melde and "unklar" in melde[0]


def test_ohne_reviewer_modell_bleibt_review_beim_menschen(konfig, board, zustand, projekt_repo):
    board.lege_an("7", konfig.spalten.review, KARTE_GUELTIG, titel="[K01] Hauptmodul")
    Worker(konfig, board, zustand, melde=lambda *a: None).tick()
    assert board.spalte_von("7") == konfig.spalten.review
    assert board.kommentare == []


def test_menschliche_karte_in_review_wird_nicht_angefasst(review_konfig, board, zustand):
    board.lege_an("9", review_konfig.spalten.review, "Notiz ohne Front-Matter")
    w, _ = _worker_mit_urteil(review_konfig, board, zustand, "ok")
    w.tick()
    assert board.spalte_von("9") == review_konfig.spalten.review


def test_gesperrtes_projekt_startet_keine_neue_karte(
    review_konfig, board, zustand, karte_in_review
):
    """K02 darf nicht starten, solange K01 in Review oder Blockiert hängt —
    sie würde auf einem main ohne K01 aufbauen."""
    naechste = KARTE_GUELTIG.replace("karte: K01", "karte: K02")
    board.lege_an("8", review_konfig.spalten.bereit, naechste, titel="[K02] Nächste")

    def aider(*a, **kw):
        raise AssertionError("Coder darf für gesperrtes Projekt nicht starten")

    # Runde 1: K01 in Review (Reviewer aus, bleibt liegen) → K02 wartet
    review_konfig.reviewer_modell = ""
    w = Worker(review_konfig, board, zustand, aider=aider, melde=lambda *a: None)
    w.tick()
    assert board.spalte_von("8") == review_konfig.spalten.bereit

    # Runde 2: K01 nach Blockiert verschoben (z. B. Review-Eskalation) → K02 wartet weiter
    board.verschiebe("7", review_konfig.spalten.blockiert)
    w.tick()
    assert board.spalte_von("8") == review_konfig.spalten.bereit

    # Runde 3: K01 erledigt → K02 darf starten (Aider-Fake schlägt an)
    board.verschiebe("7", review_konfig.spalten.done)
    with pytest.raises(AssertionError, match="gesperrtes Projekt"):
        w.tick()