"""Vertragsschicht der Hermes-Pipeline.

Drei Verträge, alle aus ARCHITEKTUR.md abgeleitet:

- ``projekt``: das projekt.yaml-Schema des Architekten (§6)
- ``karte``:   das Kartenformat auf dem Board (Front-Matter + Kartentext)
- ``intake``:  Pflichtfeld-Prüfung der beiden Intake-Vorlagen (§3)
"""

from hermes_schemas.projekt import ProjektYaml, ProjektValidierungsFehler, lade_projekt_yaml
from hermes_schemas.karte import KartenMeta, lade_kartenmeta
from hermes_schemas.intake import IntakeErgebnis, pruefe_intake

__all__ = [
    "ProjektYaml",
    "ProjektValidierungsFehler",
    "lade_projekt_yaml",
    "KartenMeta",
    "lade_kartenmeta",
    "IntakeErgebnis",
    "pruefe_intake",
]
