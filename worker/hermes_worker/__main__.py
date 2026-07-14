"""Einstiegspunkt: `hermes-worker` bzw. `python -m hermes_worker`."""

from __future__ import annotations

import logging
import time

from hermes_worker.board import Board
from hermes_worker.config import lade_konfig
from hermes_worker.state import WorkerZustand
from hermes_worker.worker import Worker


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    log = logging.getLogger("hermes_worker")

    konfig = lade_konfig()
    zustand = WorkerZustand(konfig.datenbank)
    worker = Worker(konfig, Board(konfig.board_url), zustand)

    log.info("start: board=%s poll=%ss", konfig.board_url, konfig.poll_intervall_s)
    worker.bereinige_nach_neustart()

    while True:
        try:
            worker.tick()
        except Exception:
            # Ein kaputter Tick darf den Daemon nicht töten — nächster Poll kommt.
            log.exception("tick fehlgeschlagen")
        time.sleep(konfig.poll_intervall_s)


if __name__ == "__main__":
    main()
