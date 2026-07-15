"""Einstiegspunkt: `hermes-board` — Uvicorn auf Port 9119 (ARCHITEKTUR.md §3)."""

import os

import uvicorn

from hermes_board.app import erzeuge_app


def main() -> None:
    uvicorn.run(
        erzeuge_app(),
        host=os.environ.get("HERMES_BOARD_HOST", "0.0.0.0"),
        port=int(os.environ.get("HERMES_BOARD_PORT", "9119")),
    )


if __name__ == "__main__":
    main()
