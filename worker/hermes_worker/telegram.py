"""Telegram-Meldungen — Observability neben dem Logfile (ARCHITEKTUR.md §4).

Unkonfiguriert ist der Versand ein No-op; der Worker darf daran nie scheitern.
"""

from __future__ import annotations

import logging

import requests

from hermes_worker.config import TelegramKonfig

log = logging.getLogger(__name__)


def sende(konfig: TelegramKonfig, text: str) -> None:
    if not konfig.token_datei or not konfig.chat_id:
        log.info("telegram unkonfiguriert, meldung nur im log: %s", text)
        return
    try:
        token = konfig.token_datei.read_text().strip()
        antwort = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": konfig.chat_id, "text": text},
            timeout=10,
        )
        antwort.raise_for_status()
    except Exception:
        log.exception("telegram-versand fehlgeschlagen (weiter ohne)")
