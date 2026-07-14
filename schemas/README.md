# schemas/ — Vertragsschicht

**Wird in Session 3 gebaut** (siehe `../ROADMAP.md`). Vertrag laut
`../ARCHITEKTUR.md` §3 und §6.

## Geplanter Inhalt

### 1. `projekt.yaml`-Schema (Pydantic)

Das einzige Abgabe-Artefakt des Architekten. Validiert:

- Pflichtfelder vorhanden
- Abhängigkeits-IDs existent und **zyklenfrei**
- Dateipfade im Skeleton-Namensraum
- Kartenschema: Titel, Ziel (ein Satz), betroffene Dateien (Pflichtfeld),
  maschinenprüfbare Akzeptanzkriterien, Abhängigkeits-ID
- Kartengröße: eine Karte = ein Aider-Lauf = grob eine Dateigruppe

Validierungsfehler gehen als **eine** Rückrunde an den Architekten.

### 2. Intake-Validierung

Prüft Karten in *Eingang* gegen die Pflichtfelder der Vorlagen in
`../intake-vorlagen/`; unvollständige Karten werden mit Kommentar
zurückgewiesen.

### 3. Materialisierung

Nach Freigabe deterministisch: Projekt-Repo per Copier, Karten via Board-API,
`ARCHITEKTUR.md` + rote Test-Stubs per einmaligem Aider-Lauf, Commit.
