"""Der Test, der die frühere „Endpunkt-Annahme" beerdigt: der ECHTE
Worker-Client (requests) spricht über HTTP mit dem ECHTEN hermes-board.
Übersprungen, wenn hermes-board nicht installiert ist."""

import socket
import threading
import time

import pytest

hermes_board = pytest.importorskip("hermes_board")

import uvicorn  # noqa: E402

from hermes_board.app import erzeuge_app  # noqa: E402
from hermes_worker.board import Board  # noqa: E402
from hermes_worker.worker import Worker  # noqa: E402
from tests.test_worker import INTAKE_GUELTIG, INTAKE_UNVOLLSTAENDIG  # noqa: E402


@pytest.fixture
def live_board_url(tmp_path):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            erzeuge_app(tmp_path / "board.db"), host="127.0.0.1", port=port, log_level="warning"
        )
    )
    faden = threading.Thread(target=server.run, daemon=True)
    faden.start()
    frist = time.time() + 10
    while not server.started:
        assert time.time() < frist, "Board-Server startet nicht"
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    faden.join(timeout=5)


def test_worker_client_roundtrip_gegen_echtes_board(live_board_url):
    board = Board(live_board_url)
    karten_id = board.karte_anlegen("[K01] Echt", "---\nx\n---", "Bereit")

    karten = board.karten_in("Bereit")
    assert [k.id for k in karten] == [karten_id]
    assert karten[0].titel == "[K01] Echt"

    board.verschiebe(karten_id, "Review")
    assert board.karten_in("Bereit") == []
    assert [k.id for k in board.karten_in("Review")] == [karten_id]

    board.kommentiere(karten_id, "grün")  # wirft bei != 2xx


def test_worker_tick_gegen_echtes_board(live_board_url, konfig, zustand):
    """Intake-Validierung end-to-end über HTTP: gültig wandert, ungültig
    bekommt genau einen Kommentar."""
    board = Board(live_board_url)
    gut = board.karte_anlegen("Intake gut", INTAKE_GUELTIG, konfig.spalten.eingang)
    schlecht = board.karte_anlegen("Intake schlecht", INTAKE_UNVOLLSTAENDIG, konfig.spalten.eingang)

    worker = Worker(konfig, board, zustand, melde=lambda *a: None)
    worker.tick()
    worker.tick()

    architektur = {k.id for k in board.karten_in(konfig.spalten.architektur)}
    eingang = {k.id for k in board.karten_in(konfig.spalten.eingang)}
    assert gut in architektur
    assert schlecht in eingang
