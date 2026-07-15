"""projekt.yaml — der Architekten-Vertrag (ARCHITEKTUR.md §6).

Validiert werden: Pflichtfelder, Karten-IDs eindeutig, Abhängigkeits-IDs
existent und zyklenfrei, Dateipfade im Skeleton-Namensraum. Validierungs-
fehler gehen gesammelt als eine Rückrunde an den Architekten — deshalb
sammelt ``lade_projekt_yaml`` alle Fehler statt beim ersten abzubrechen.
"""

from __future__ import annotations

import re
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

KARTEN_ID_MUSTER = re.compile(r"^K\d{2,3}$")
PROJEKTNAME_MUSTER = re.compile(r"^[a-z][a-z0-9-]{2,49}$")

# Erlaubte Pfad-Wurzeln je Domäne. Muss zum jeweiligen Skeleton passen —
# wenn sich dort der Zuschnitt ändert, ist dies die einzige Stelle hier.
SKELETON_NAMENSRAUM: dict[str, tuple[str, ...]] = {
    "web": ("app/", "tests/", "deploy.sh", "compose.yaml", "ARCHITEKTUR.md", "README.md"),
    "device-tool": (
        "app/",
        "tests/",
        "device-profiles/",
        ".github/workflows/",
        "ARCHITEKTUR.md",
        "README.md",
    ),
}


class Karte(BaseModel):
    """Eine Karte = ein Aider-Lauf = grob eine Dateigruppe."""

    model_config = ConfigDict(extra="forbid")

    id: str
    titel: str = Field(min_length=3, max_length=100)
    ziel: str = Field(min_length=10, max_length=300, description="Ein Satz.")
    dateien: list[str] = Field(min_length=1)
    akzeptanz: list[str] = Field(min_length=1)
    abhaengig_von: list[str] = Field(default_factory=list)
    test_stub: str = Field(min_length=10, description="Rote Tests, die der Coder grün macht.")

    @field_validator("id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        if not KARTEN_ID_MUSTER.match(v):
            raise ValueError(f"Karten-ID '{v}' entspricht nicht dem Muster K01…K999")
        return v


class Architektur(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: list[str] = Field(min_length=1)
    datenmodell: str = Field(min_length=1)
    routen: list[str] = Field(default_factory=list, description="Nur Domäne web.")
    geraeteprofile: list[str] = Field(default_factory=list, description="Nur Domäne device-tool.")
    ausgeschlossen: list[str] = Field(min_length=1, description="Explizit nicht in v1.")


class ProjektKopf(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    domaene: Literal["web", "device-tool"]
    beschreibung: str = Field(min_length=20)

    @field_validator("name")
    @classmethod
    def _name_format(cls, v: str) -> str:
        if not PROJEKTNAME_MUSTER.match(v):
            raise ValueError(
                f"Projektname '{v}' muss kleinbuchstaben-mit-bindestrich sein (3–50 Zeichen)"
            )
        return v


class ProjektYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projekt: ProjektKopf
    architektur: Architektur
    karten: list[Karte] = Field(min_length=1)


class ProjektValidierungsFehler(Exception):
    """Alle Beanstandungen gesammelt — der Architekt bekommt genau eine Rückrunde."""

    def __init__(self, fehler: list[str]):
        self.fehler = fehler
        super().__init__("; ".join(fehler))

    def als_kommentar(self) -> str:
        zeilen = "\n".join(f"- {f}" for f in self.fehler)
        return f"projekt.yaml nicht valide — bitte in einer Runde beheben:\n{zeilen}"


def _pruefe_abhaengigkeiten(karten: list[Karte]) -> list[str]:
    fehler: list[str] = []
    ids = [k.id for k in karten]
    doppelte = {i for i in ids if ids.count(i) > 1}
    if doppelte:
        fehler.append(f"Karten-IDs mehrfach vergeben: {sorted(doppelte)}")

    bekannte = set(ids)
    for k in karten:
        if k.id in k.abhaengig_von:
            fehler.append(f"{k.id}: hängt von sich selbst ab")
        for dep in k.abhaengig_von:
            if dep not in bekannte:
                fehler.append(f"{k.id}: Abhängigkeit '{dep}' existiert nicht")

    # Zyklensuche per Kahn-Algorithmus (nur über existente Kanten)
    kanten = {k.id: [d for d in k.abhaengig_von if d in bekannte] for k in karten}
    eingrad = {kid: len(deps) for kid, deps in kanten.items()}
    frei = [i for i, g in eingrad.items() if g == 0]
    besucht = 0
    while frei:
        aktuelle = frei.pop()
        besucht += 1
        for kid, deps in kanten.items():
            if aktuelle in deps:
                eingrad[kid] -= 1
                if eingrad[kid] == 0:
                    frei.append(kid)
    if besucht < len(bekannte):
        rest = sorted(i for i, g in eingrad.items() if g > 0)
        fehler.append(f"Abhängigkeiten enthalten einen Zyklus, beteiligt: {rest}")
    return fehler


def _pruefe_dateipfade(domaene: str, karten: list[Karte]) -> list[str]:
    fehler: list[str] = []
    wurzeln = SKELETON_NAMENSRAUM[domaene]
    for k in karten:
        for pfad in k.dateien:
            if pfad.startswith("/") or ".." in pfad.split("/"):
                fehler.append(f"{k.id}: Pfad '{pfad}' ist nicht relativ innerhalb des Repos")
            elif not pfad.startswith(wurzeln):
                fehler.append(
                    f"{k.id}: Pfad '{pfad}' liegt außerhalb des Skeleton-Namensraums "
                    f"{list(wurzeln)} (Domäne {domaene})"
                )
    return fehler


def _pydantic_fehler_lesbar(e: ValidationError) -> list[str]:
    fehler = []
    for f in e.errors():
        ort = ".".join(str(p) for p in f["loc"]) or "(Wurzel)"
        fehler.append(f"{ort}: {f['msg']}")
    return fehler


def lade_projekt_yaml(text: str) -> ProjektYaml:
    """Parst und validiert vollständig; wirft ProjektValidierungsFehler mit ALLEN Beanstandungen."""
    try:
        roh = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ProjektValidierungsFehler([f"YAML nicht parsebar: {e}"]) from e
    if not isinstance(roh, dict):
        raise ProjektValidierungsFehler(["Wurzel muss ein Mapping mit projekt/architektur/karten sein"])

    try:
        projekt = ProjektYaml.model_validate(roh)
    except ValidationError as e:
        raise ProjektValidierungsFehler(_pydantic_fehler_lesbar(e)) from e

    fehler = _pruefe_abhaengigkeiten(projekt.karten)
    fehler += _pruefe_dateipfade(projekt.projekt.domaene, projekt.karten)
    if fehler:
        raise ProjektValidierungsFehler(fehler)
    return projekt
