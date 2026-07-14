"""Intake-Validierung (ARCHITEKTUR.md §3, Schritt 1).

Prüft Karten in *Eingang* gegen die Pflichtfelder der beiden Vorlagen in
``intake-vorlagen/``. Unvollständige Karten weist der Worker mit dem
Kommentar aus ``IntakeErgebnis.als_kommentar()`` zurück.

Die Prüfung ist bewusst tolerant beim Parsen (Überschriften werden
normalisiert verglichen), aber streng bei den Pflichtinhalten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

_HTML_KOMMENTAR = re.compile(r"<!--.*?-->", re.DOTALL)
_CHECKBOX = re.compile(r"^[-*]\s*\[(?P<mark>[xX ])\]\s*(?P<text>.+)$", re.MULTILINE)
_AUFZAEHLUNG = re.compile(r"^[-*]\s+(?P<text>\S.*)$", re.MULTILINE)
_CODEBLOCK = re.compile(r"```[a-zA-Z]*\n(?P<code>.*?)```", re.DOTALL)


@dataclass
class IntakeErgebnis:
    art: Literal["neu", "aenderung", "unbekannt"]
    domaene: str | None = None
    beanstandungen: list[str] = field(default_factory=list)

    @property
    def gueltig(self) -> bool:
        return not self.beanstandungen

    def als_kommentar(self) -> str:
        zeilen = "\n".join(f"- {b}" for b in self.beanstandungen)
        return (
            "Intake unvollständig — Karte bleibt in *Eingang*, bitte nachtragen:\n"
            f"{zeilen}\n\nVorlagen: `intake-vorlagen/` im Repo hermes-pipeline."
        )


def _normalisiere(ueberschrift: str) -> str:
    """'## Ziel (Pflicht, 3–5 Sätze)' → 'ziel'"""
    t = re.sub(r"\(.*?\)", "", ueberschrift)
    t = re.sub(r"[^a-zäöüß/\- ]", "", t.lower())
    return t.strip()


def _abschnitte(text: str) -> dict[str, str]:
    """Zerlegt Markdown an '## '-Überschriften; Schlüssel normalisiert."""
    ohne_kommentare = _HTML_KOMMENTAR.sub("", text)
    ergebnis: dict[str, str] = {}
    aktueller: str | None = None
    zeilen: list[str] = []
    for zeile in ohne_kommentare.splitlines():
        if zeile.startswith("## "):
            if aktueller is not None:
                ergebnis[aktueller] = "\n".join(zeilen).strip()
            aktueller = _normalisiere(zeile[3:])
            zeilen = []
        elif aktueller is not None:
            zeilen.append(zeile)
    if aktueller is not None:
        ergebnis[aktueller] = "\n".join(zeilen).strip()
    return ergebnis


def _finde(abschnitte: dict[str, str], *stichworte: str) -> str | None:
    """Findet den ersten Abschnitt, dessen Schlüssel alle Stichworte enthält."""
    for schluessel, inhalt in abschnitte.items():
        if all(s in schluessel for s in stichworte):
            return inhalt
    return None


def _aufzaehlungspunkte(inhalt: str) -> list[str]:
    punkte = []
    for m in _AUFZAEHLUNG.finditer(inhalt):
        text = m.group("text").strip()
        if not text.startswith("["):  # Checkboxen sind keine Inhaltspunkte
            punkte.append(text)
    return punkte


def _angekreuzt(inhalt: str) -> list[str]:
    return [
        m.group("text").strip()
        for m in _CHECKBOX.finditer(inhalt)
        if m.group("mark").lower() == "x"
    ]


def _tabellenzeilen(inhalt: str) -> list[list[str]]:
    """Datenzeilen einer Markdown-Tabelle (ohne Kopf und Trennzeile), nur nicht-leere."""
    zeilen = []
    for zeile in inhalt.splitlines():
        zeile = zeile.strip()
        if not zeile.startswith("|"):
            continue
        zellen = [z.strip() for z in zeile.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", z) for z in zellen if z):
            continue  # Trennzeile
        zeilen.append(zellen)
    # erste Pipe-Zeile ist der Kopf
    daten = zeilen[1:] if zeilen else []
    return [z for z in daten if any(z)]


def _satzzahl(text: str) -> int:
    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])


def _pruefe_ziel(abschnitte: dict[str, str], schluesselwort: str, fehler: list[str]) -> None:
    ziel = _finde(abschnitte, schluesselwort)
    if ziel is None or not ziel.strip():
        fehler.append("Pflichtfeld **Ziel** fehlt oder ist leer")
    elif _satzzahl(ziel) < 3:
        fehler.append("**Ziel** braucht 3–5 Sätze (aktuell zu knapp)")


def _pruefe_liste(
    abschnitte: dict[str, str], name: str, fehler: list[str], *stichworte: str
) -> None:
    inhalt = _finde(abschnitte, *stichworte)
    if inhalt is None or not _aufzaehlungspunkte(inhalt):
        fehler.append(f"Pflichtfeld **{name}** fehlt oder enthält keinen Aufzählungspunkt")


def pruefe_intake(beschreibung: str) -> IntakeErgebnis:
    """Validiert eine Eingang-Karte gegen die passende Intake-Vorlage."""
    kopf = beschreibung.strip().splitlines()[0] if beschreibung.strip() else ""
    if "änderung" in kopf.lower() or "aenderung" in kopf.lower():
        return _pruefe_aenderung(beschreibung)
    if "neues projekt" in kopf.lower() or "neuprojekt" in kopf.lower():
        return _pruefe_neu(beschreibung)
    return IntakeErgebnis(
        art="unbekannt",
        beanstandungen=[
            "Karte beginnt nicht mit einer der Intake-Vorlagen "
            "(`# Intake: Neues Projekt` oder `# Intake: Änderung an Projekt X`)"
        ],
    )


def _pruefe_neu(beschreibung: str) -> IntakeErgebnis:
    a = _abschnitte(beschreibung)
    fehler: list[str] = []

    domaene: str | None = None
    domaenen_abschnitt = _finde(a, "domäne") if _finde(a, "domäne") is not None else _finde(a, "domaene")
    angekreuzt = _angekreuzt(domaenen_abschnitt or "")
    if len(angekreuzt) != 1:
        fehler.append("Pflichtfeld **Domäne**: genau eine Option ankreuzen (`- [x]`)")
    else:
        text = angekreuzt[0].lower()
        domaene = "device-tool" if "device-tool" in text else "web" if "web" in text else None
        if domaene is None:
            fehler.append("Pflichtfeld **Domäne**: angekreuzte Option ist weder web noch device-tool")

    name = _finde(a, "projektname")
    if not name or not name.strip():
        fehler.append("Pflichtfeld **Projektname** fehlt oder ist leer")

    _pruefe_ziel(a, "ziel", fehler)
    _pruefe_liste(a, "Muss-Funktionen", fehler, "muss-funktionen")
    _pruefe_liste(a, "Explizit nicht", fehler, "explizit nicht")

    if domaene == "web":
        routen = _finde(a, "seiten", "routenliste") or _finde(a, "routenliste")
        if routen is None or not _tabellenzeilen(routen):
            fehler.append("Domäne web: **Seiten-/Routenliste** braucht mindestens eine Datenzeile")
    elif domaene == "device-tool":
        registermap = _finde(a, "registermap")
        code = _CODEBLOCK.search(registermap or "")
        if not code or not code.group("code").strip():
            fehler.append("Domäne device-tool: **Rohe Registermap** (Codeblock) fehlt oder ist leer")

    return IntakeErgebnis(art="neu", domaene=domaene, beanstandungen=fehler)


def _pruefe_aenderung(beschreibung: str) -> IntakeErgebnis:
    a = _abschnitte(beschreibung)
    fehler: list[str] = []

    projekt = _finde(a, "projekt")
    if not projekt or not projekt.strip():
        fehler.append("Pflichtfeld **Projekt** fehlt oder ist leer")

    _pruefe_ziel(a, "ziel", fehler)
    _pruefe_liste(a, "Muss-Funktionen / Muss-Verhalten", fehler, "muss")
    _pruefe_liste(a, "Explizit nicht", fehler, "explizit nicht")

    architektur = _finde(a, "berührt", "architektur") or _finde(a, "beruehrt", "architektur")
    if architektur is None or len(_angekreuzt(architektur)) != 1:
        fehler.append(
            "Pflichtfeld **Berührt die Änderung die Architektur?**: genau eine Option ankreuzen"
        )

    return IntakeErgebnis(art="aenderung", beanstandungen=fehler)
