"""Kartenformat auf dem Board.

Der Materialisierungs-Schritt erzeugt aus der projekt.yaml Board-Karten.
Damit der Worker eine Karte maschinell einem Repo, Branch und Aider-Lauf
zuordnen kann, beginnt jede Kartenbeschreibung mit YAML-Front-Matter:

    ---
    projekt: homelab-status
    karte: K07
    dateien: [app/routen/status.py, tests/test_karte_07.py]
    ---
    Ziel: …

    Akzeptanzkriterien:
    - …

Nach dem Front-Matter folgt der Kartentext, den Aider als Auftrag bekommt.
"""

from __future__ import annotations

import re

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class KartenMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projekt: str = Field(min_length=3)
    karte: str = Field(pattern=r"^K\d{2,3}$")
    dateien: list[str] = Field(min_length=1)
    # Read-only-Kontext für den Aider-Lauf (z. B. der Test-Stub der Karte)
    nur_lesen: list[str] = Field(default_factory=list)


class KartenFormatFehler(Exception):
    pass


def lade_kartenmeta(beschreibung: str) -> tuple[KartenMeta, str]:
    """Zerlegt eine Kartenbeschreibung in (Meta, Kartentext für Aider)."""
    treffer = _FRONT_MATTER.match(beschreibung.lstrip())
    if not treffer:
        raise KartenFormatFehler(
            "Karte hat kein YAML-Front-Matter (---\\nprojekt: …\\nkarte: …\\n---)"
        )
    try:
        roh = yaml.safe_load(treffer.group(1))
        meta = KartenMeta.model_validate(roh)
    except (yaml.YAMLError, ValidationError) as e:
        raise KartenFormatFehler(f"Front-Matter nicht valide: {e}") from e
    kartentext = beschreibung.lstrip()[treffer.end() :].strip()
    if not kartentext:
        raise KartenFormatFehler("Karte enthält keinen Auftragstext nach dem Front-Matter")
    return meta, kartentext


def baue_kartenbeschreibung(meta: KartenMeta, kartentext: str) -> str:
    """Gegenstück für die Materialisierung: Meta + Text → Kartenbeschreibung."""
    front = yaml.safe_dump(
        meta.model_dump(), allow_unicode=True, sort_keys=False, default_flow_style=None
    ).strip()
    return f"---\n{front}\n---\n{kartentext.strip()}\n"
