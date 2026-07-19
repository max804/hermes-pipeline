"""Die Poll-Schleife (ARCHITEKTUR.md §3–§4).

Pro Tick zwei Aufgaben:

1. *Eingang* validieren: vollständige Intakes wandern nach *Architektur*,
   unvollständige bekommen genau einen Kommentar (Duplikatschutz per Hash).
2. Genau EINE Karte aus *Bereit* abarbeiten (keine Parallelität in v1):
   Branch → Aider-Lauf (20-min-Timeout) → `make check` im Container.

Ausgänge der Coder-Schleife:
- grün            → Karte nach *Review*
- rot             → Branch bleibt (Beweisstück/Fix-Grundlage), Karte zurück
                    auf *Bereit*, Zähler +1; ab 3 Versuchen → *Blockiert* + Ping
- Timeout/Abbruch → Branch verwerfen, Karte zurück auf *Bereit*, Zähler +1

Aider-Lauf und `make check` sind injizierbar (Tests laufen mit Fakes).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Callable, Protocol

from hermes_schemas.intake import pruefe_intake
from hermes_schemas.karte import KartenFormatFehler, lade_kartenmeta
from hermes_schemas.projekt import ProjektValidierungsFehler

from hermes_worker import materialisierung
from hermes_worker import repo as git
from hermes_worker.aider_runner import AiderErgebnis, fuehre_aider_aus
from hermes_worker.board import BoardKarte
from hermes_worker.checks import PruefErgebnis, make_check
from hermes_worker.config import WorkerKonfig
from hermes_worker.reviewer import ReviewErgebnis, fuehre_review_aus
from hermes_worker.state import WorkerZustand
from hermes_worker import telegram

log = logging.getLogger(__name__)


class BoardSchnittstelle(Protocol):
    def karten_in(self, spalte: str) -> list[BoardKarte]: ...
    def karte_anlegen(self, titel: str, beschreibung: str, spalte: str) -> str: ...
    def verschiebe(self, karten_id: str, spalte: str) -> None: ...
    def kommentiere(self, karten_id: str, text: str) -> None: ...


class Worker:
    def __init__(
        self,
        konfig: WorkerKonfig,
        board: BoardSchnittstelle,
        zustand: WorkerZustand,
        aider: Callable[..., AiderErgebnis] = fuehre_aider_aus,
        pruefung: Callable[..., PruefErgebnis] = make_check,
        review: Callable[..., ReviewErgebnis] = fuehre_review_aus,
        melde: Callable[..., None] = telegram.sende,
    ):
        self.konfig = konfig
        self.board = board
        self.zustand = zustand
        self._aider = aider
        self._pruefung = pruefung
        self._review = review
        self._melde = melde

    # --- Neustart-Aufräumen --------------------------------------------------

    def bereinige_nach_neustart(self) -> None:
        """Als laufend markierte Karten stammen aus einem gestorbenen Worker:
        wie Abbruch behandeln — Branch verwerfen, zurück auf *Bereit*, Zähler +1."""
        for karten_id, projekt, branch in self.zustand.laufende_karten():
            log.warning("neustart: karte %s war als laufend markiert, setze zurueck", karten_id)
            repo_pfad = self.konfig.projekte_verzeichnis / projekt
            if repo_pfad.is_dir():
                git.verwerfe_branch(repo_pfad, branch)
            self.zustand.erhoehe_versuche(karten_id)
            self.zustand.setze_laufend(karten_id, False)
            self._verschiebe_still(karten_id, self.konfig.spalten.bereit)

    def _verschiebe_still(self, karten_id: str, spalte: str) -> None:
        try:
            self.board.verschiebe(karten_id, spalte)
        except Exception:
            log.exception("board nicht erreichbar beim verschieben von %s", karten_id)

    # --- Tick ---------------------------------------------------------------

    def tick(self) -> None:
        self._pruefe_eingang()
        self._verarbeite_review()
        self._verarbeite_bereit()

    # --- 1) Eingang ----------------------------------------------------------

    def _pruefe_eingang(self) -> None:
        for karte in self.board.karten_in(self.konfig.spalten.eingang):
            ergebnis = pruefe_intake(karte.beschreibung)
            if ergebnis.gueltig:
                log.info("intake %s vollstaendig -> %s", karte.id, self.konfig.spalten.architektur)
                self.board.verschiebe(karte.id, self.konfig.spalten.architektur)
                continue
            inhalt_hash = hashlib.sha256(karte.beschreibung.encode()).hexdigest()
            if self.zustand.intake_bereits_kommentiert(karte.id, inhalt_hash):
                continue  # unverändert unvollständig — nicht erneut kommentieren
            log.info("intake %s unvollstaendig: %d beanstandungen", karte.id, len(ergebnis.beanstandungen))
            self.board.kommentiere(karte.id, ergebnis.als_kommentar())
            self.zustand.merke_intake_kommentar(karte.id, inhalt_hash)

    # --- 2) Reviewer-Schleife ---------------------------------------------------

    def _gesperrte_projekte(self) -> set[str]:
        """Projekte mit Karte in Review, In Arbeit oder Blockiert: dort darf
        keine neue Karte starten — sie würde auf einem main aufbauen, dem der
        ungemergte Vorgänger fehlt. Blockiert löst nur der Mensch auf."""
        projekte = set()
        for spalte in (
            self.konfig.spalten.review,
            self.konfig.spalten.in_arbeit,
            self.konfig.spalten.blockiert,
        ):
            for karte in self.board.karten_in(spalte):
                try:
                    meta, _ = lade_kartenmeta(karte.beschreibung)
                    projekte.add(meta.projekt)
                except KartenFormatFehler:
                    continue
        return projekte

    def _verarbeite_review(self) -> None:
        if not self.konfig.reviewer_modell:
            return  # Review bleibt beim Menschen, bis das Zweitmodell gewählt ist
        karten = self.board.karten_in(self.konfig.spalten.review)
        if not karten:
            return
        karte = karten[0]  # sequenziell, eine pro Tick

        try:
            meta, kartentext = lade_kartenmeta(karte.beschreibung)
        except KartenFormatFehler:
            return  # menschliche Karte in Review — nicht anfassen

        repo_pfad = self.konfig.projekte_verzeichnis / meta.projekt
        branch = self.zustand.branch_von(karte.id) or git.branch_name(
            meta.karte, karte.titel or meta.karte
        )
        log.info("review von karte %s (%s) auf %s", karte.id, meta.karte, branch)
        ergebnis = self._review(self.konfig, repo_pfad, branch, kartentext)

        if ergebnis.urteil == "ok":
            titel = karte.titel.removeprefix(f"[{meta.karte}]").strip() or meta.karte
            try:
                git.squash_merge(repo_pfad, branch, f"[{meta.karte}] {titel}")
            except git.GitFehler as e:
                self.board.kommentiere(karte.id, f"Review OK, aber Squash-Merge scheitert: {e}")
                self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
                self._melde(
                    self.konfig.telegram,
                    f"Hermes: Merge-Konflikt bei {meta.karte} ({meta.projekt}) — blockiert.",
                )
                return
            self.board.kommentiere(
                karte.id, f"Review OK — squash-merged nach `main` als `[{meta.karte}] {titel}`."
            )
            self.board.verschiebe(karte.id, self.konfig.spalten.done)
            log.info("karte %s done, branch %s gemergt", karte.id, branch)
            return

        if ergebnis.urteil == "fix":
            # Fix-Rückläufer: dieselbe Karte geht mit den Befunden zurück —
            # das einzige Erzeugnis, das dem Reviewer zusteht (DECISIONS.md).
            self.zustand.setze_letzte_pruefung(karte.id, ergebnis.befunde)
            versuche = self.zustand.erhoehe_versuche(karte.id)
            if versuche >= self.konfig.max_versuche:
                self.board.kommentiere(
                    karte.id,
                    f"Review FIX, Versuch {versuche}/{self.konfig.max_versuche} — blockiert. "
                    f"Branch `{branch}` bleibt als Beweisstück.\n\n{ergebnis.befunde}",
                )
                self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
                self._melde(
                    self.konfig.telegram,
                    f"Hermes: Karte {meta.karte} ({meta.projekt}) nach Review-FIX blockiert.",
                )
            else:
                self.board.kommentiere(
                    karte.id,
                    f"Review FIX, Versuch {versuche}/{self.konfig.max_versuche} — "
                    f"Fix-Rückläufer:\n\n{ergebnis.befunde}",
                )
                self.board.verschiebe(karte.id, self.konfig.spalten.bereit)
            log.info("karte %s review-fix, versuch %d", karte.id, versuche)
            return

        # unklar: Reviewer-Fehlfunktion — sichtbar eskalieren statt endlos wiederholen
        self.board.kommentiere(
            karte.id,
            "Reviewer-Urteil unparsebar oder Lauf gescheitert — bitte manuell "
            f"reviewen (zurück nach Review = erneuter Versuch).\n```\n{ergebnis.ausgabe_ende}\n```",
        )
        self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
        self._melde(
            self.konfig.telegram,
            f"Hermes: Reviewer-Lauf für {meta.karte} ({meta.projekt}) unklar — blockiert.",
        )

    # --- 3) Coder-Schleife -----------------------------------------------------

    def _verarbeite_bereit(self) -> None:
        karten = self.board.karten_in(self.konfig.spalten.bereit)
        gesperrt = self._gesperrte_projekte()
        karte = None
        for kandidat in karten:
            try:
                meta_probe, _ = lade_kartenmeta(kandidat.beschreibung)
            except KartenFormatFehler:
                karte = kandidat  # Freigabe-/Fehlformat-Karten behandeln wie bisher
                break
            if meta_probe.projekt in gesperrt:
                log.info(
                    "karte %s wartet: projekt %s hat karte in review",
                    kandidat.id, meta_probe.projekt,
                )
                continue
            karte = kandidat
            break
        if karte is None:
            return

        try:
            meta, kartentext = lade_kartenmeta(karte.beschreibung)
        except KartenFormatFehler as e:
            # Keine Coder-Karte — vielleicht eine freigegebene projekt.yaml?
            yaml_text = materialisierung.extrahiere_projekt_yaml(karte.beschreibung)
            if yaml_text is not None:
                self._materialisiere(karte, yaml_text)
                return
            self.board.kommentiere(karte.id, f"Kartenformat ungültig: {e}")
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            return

        repo_pfad = self.konfig.projekte_verzeichnis / meta.projekt
        if not (repo_pfad / ".git").is_dir():
            self.board.kommentiere(
                karte.id, f"Projekt-Repo fehlt unter {repo_pfad} — Materialisierung prüfen."
            )
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            return

        branch = git.branch_name(meta.karte, karte.titel or meta.karte)
        self.zustand.registriere(karte.id, meta.projekt, branch)
        self.board.verschiebe(karte.id, self.konfig.spalten.in_arbeit)
        self.zustand.setze_laufend(karte.id, True)
        log.info("karte %s (%s) startet auf branch %s", karte.id, meta.karte, branch)

        try:
            git.beginne_karte(repo_pfad, branch)
            git.aktiviere_test_stub(repo_pfad, meta.karte)
            ergebnis = self._aider(
                self.konfig,
                repo_pfad,
                kartentext,
                meta.dateien,
                letzte_pruefung=self.zustand.letzte_pruefung(karte.id),
                nur_lesen=meta.nur_lesen,
            )
            if ergebnis.timeout:
                self._nach_abbruch(karte, meta.projekt, repo_pfad, branch, "20-Minuten-Timeout")
                return
            pruefung = self._pruefung(
                repo_pfad, self.konfig.docker_speicher, self.konfig.docker_cpus
            )
        except git.GitFehler as e:
            self._nach_abbruch(karte, meta.projekt, repo_pfad, branch, f"Git-Fehler: {e}")
            return
        finally:
            self.zustand.setze_laufend(karte.id, False)

        if pruefung.gruen:
            self.zustand.setze_letzte_pruefung(karte.id, "")
            self.board.kommentiere(karte.id, f"`make check` grün auf `{branch}`.")
            self.board.verschiebe(karte.id, self.konfig.spalten.review)
            log.info("karte %s gruen -> %s", karte.id, self.konfig.spalten.review)
            return

        # rot: Branch bleibt als Fix-Grundlage bzw. Beweisstück
        self.zustand.setze_letzte_pruefung(karte.id, pruefung.ausgabe_ende)
        versuche = self.zustand.erhoehe_versuche(karte.id)
        if versuche >= self.konfig.max_versuche:
            self.board.kommentiere(
                karte.id,
                f"`make check` rot, Versuch {versuche}/{self.konfig.max_versuche} — blockiert. "
                f"Branch `{branch}` bleibt als Beweisstück.\n```\n{pruefung.ausgabe_ende}\n```",
            )
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            self._melde(
                self.konfig.telegram,
                f"Hermes: Karte {meta.karte} ({meta.projekt}) nach {versuche} Versuchen blockiert.",
            )
            log.warning("karte %s blockiert nach %d versuchen", karte.id, versuche)
        else:
            self.board.kommentiere(
                karte.id,
                f"`make check` rot, Versuch {versuche}/{self.konfig.max_versuche} — "
                f"Fix-Runde folgt.\n```\n{pruefung.ausgabe_ende}\n```",
            )
            self.board.verschiebe(karte.id, self.konfig.spalten.bereit)
            log.info("karte %s rot, versuch %d, zurueck auf bereit", karte.id, versuche)

    def _materialisiere(self, karte: BoardKarte, yaml_text: str) -> None:
        """Freigegebene projekt.yaml-Karte: Repo, Stubs und Coder-Karten erzeugen."""
        self.board.verschiebe(karte.id, self.konfig.spalten.in_arbeit)
        try:
            projekt = materialisierung.materialisiere(self.konfig, self.board, yaml_text)
        except ProjektValidierungsFehler as e:
            # Sollte am Gate nicht mehr passieren — trotzdem sauber melden.
            self.board.kommentiere(karte.id, e.als_kommentar())
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            return
        except materialisierung.MaterialisierungsFehler as e:
            self.board.kommentiere(karte.id, f"Materialisierung fehlgeschlagen: {e}")
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            self._melde(
                self.konfig.telegram,
                f"Hermes: Materialisierung der Karte {karte.id} fehlgeschlagen.",
            )
            return
        except Exception as e:
            # Nichts darf die Karte in *In Arbeit* stranden lassen — jede
            # unerwartete Ausnahme geht sichtbar nach *Blockiert*.
            log.exception("materialisierung von %s unerwartet gescheitert", karte.id)
            self.board.kommentiere(
                karte.id, f"Materialisierung unerwartet abgebrochen: {type(e).__name__}: {e}"
            )
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            self._melde(
                self.konfig.telegram,
                f"Hermes: Materialisierung der Karte {karte.id} unerwartet abgebrochen.",
            )
            return
        self.board.kommentiere(
            karte.id,
            f"Materialisiert: `{projekt.projekt.name}` mit {len(projekt.karten)} Karten "
            f"in '{self.konfig.spalten.bereit}'.",
        )
        self.board.verschiebe(karte.id, self.konfig.spalten.done)
        log.info("projekt %s materialisiert (%d karten)", projekt.projekt.name, len(projekt.karten))

    def _nach_abbruch(self, karte, projekt: str, repo_pfad, branch: str, grund: str) -> None:
        """Abbruch/Timeout: Branch verwerfen, zurück auf *Bereit*, Zähler +1."""
        git.verwerfe_branch(repo_pfad, branch)
        versuche = self.zustand.erhoehe_versuche(karte.id)
        if versuche >= self.konfig.max_versuche:
            self.board.kommentiere(karte.id, f"{grund}, Versuch {versuche} — blockiert.")
            self.board.verschiebe(karte.id, self.konfig.spalten.blockiert)
            self._melde(
                self.konfig.telegram,
                f"Hermes: Karte {karte.id} ({projekt}) nach {versuche} Abbrüchen blockiert.",
            )
        else:
            self.board.kommentiere(
                karte.id, f"{grund}, Versuch {versuche}/{self.konfig.max_versuche} — Branch verworfen."
            )
            self.board.verschiebe(karte.id, self.konfig.spalten.bereit)
        log.warning("karte %s abbruch (%s), versuch %d", karte.id, grund, versuche)
