"""Ableitung der Karten-Anzeige aus den echten Feldern.

Das Board hat keine Agenten-/Fortschritts-Daten wie die Design-Vorlage —
diese Funktionen leiten aus dem, was da ist (Titel, Spalte, Zeitstempel,
Kommentarzahl, Beschreibung), tragfähige Anzeigewerte ab. Reine Logik,
ohne FastAPI/DB, damit sie getestet werden kann.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

# Statuskategorie je Spalte → (Text-Akzent, Balken-/Punkt-Hintergrund).
# Unbekannte Spalten (frei angelegte) bekommen einen neutralen Ton.
AKZENTE: dict[str, tuple[str, str]] = {
    "Eingang": ("text-slate-300", "bg-slate-500"),
    "Architektur": ("text-sky-400", "bg-sky-500"),
    "Freigabe": ("text-amber-400", "bg-amber-500"),
    "Bereit": ("text-slate-200", "bg-slate-400"),
    "In Arbeit": ("text-sky-400", "bg-sky-500"),
    "Review": ("text-violet-400", "bg-violet-500"),
    "Done": ("text-emerald-400", "bg-emerald-500"),
    "Blockiert": ("text-red-400", "bg-red-500"),
}
_NEUTRAL = ("text-slate-300", "bg-slate-500")

_CHIP = re.compile(r"^\s*\[([^\]]{1,12})\]\s*(.*)$", re.DOTALL)


def akzent(spalte: str) -> tuple[str, str]:
    return AKZENTE.get(spalte, _NEUTRAL)


def chip_und_titel(karten_id: int, titel: str) -> tuple[str, str]:
    """'[K01] Healthcheck' → ('K01', 'Healthcheck'); sonst ('#id', titel)."""
    treffer = _CHIP.match(titel)
    if treffer:
        return treffer.group(1), treffer.group(2).strip() or titel
    return f"#{karten_id}", titel.strip()


def art_tag(beschreibung: str) -> str | None:
    """Kleiner Chip aus dem Inhalt: Bauplan (projekt.yaml) erkennen."""
    if "projekt:" in beschreibung and "karten:" in beschreibung:
        return "Bauplan"
    return None


def relativzeit(iso_zeit: str, *, jetzt: datetime | None = None) -> str:
    try:
        wann = datetime.fromisoformat(iso_zeit)
    except ValueError:
        return ""
    if wann.tzinfo is None:
        wann = wann.replace(tzinfo=timezone.utc)
    jetzt = jetzt or datetime.now(timezone.utc)
    sekunden = int((jetzt - wann).total_seconds())
    if sekunden < 60:
        return "gerade eben"
    minuten = sekunden // 60
    if minuten < 60:
        return f"vor {minuten} Min"
    stunden = minuten // 60
    if stunden < 24:
        return f"vor {stunden} Std"
    tage = stunden // 24
    return f"vor {tage} Tag" + ("en" if tage != 1 else "")


@dataclass(frozen=True)
class KartenAnsicht:
    id: int
    chip: str
    titel: str
    zeit: str
    kommentare: int
    tag: str | None
    punkt: str  # bg-Klasse des Status-Punkts


def baue_ansicht(karte, kommentar_anzahl: int, *, jetzt: datetime | None = None) -> KartenAnsicht:
    chip, titel = chip_und_titel(karte.id, karte.titel)
    _, punkt = akzent(karte.spalte)
    return KartenAnsicht(
        id=karte.id,
        chip=chip,
        titel=titel,
        zeit=relativzeit(karte.aktualisiert, jetzt=jetzt),
        kommentare=kommentar_anzahl,
        tag=art_tag(karte.beschreibung),
        punkt=punkt,
    )
