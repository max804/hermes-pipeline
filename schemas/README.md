# schemas/ — Vertragsschicht

**Status: gebaut** (Session 3, siehe `../ROADMAP.md`). Vertrag laut
`../ARCHITEKTUR.md` §3 und §6. Paket `hermes_schemas`, Tests unter
`tests/`, valides Referenzbeispiel unter `beispiele/projekt.beispiel.yaml`.

## Inhalt

### 1. `projekt.yaml`-Schema (Pydantic) — `hermes_schemas/projekt.py`

Das einzige Abgabe-Artefakt des Architekten. Validiert:

- Pflichtfelder vorhanden
- Abhängigkeits-IDs existent und **zyklenfrei**
- Dateipfade im Skeleton-Namensraum
- Kartenschema: Titel, Ziel (ein Satz), betroffene Dateien (Pflichtfeld),
  maschinenprüfbare Akzeptanzkriterien, Abhängigkeits-ID
- Kartengröße: eine Karte = ein Aider-Lauf = grob eine Dateigruppe

Validierungsfehler gehen als **eine** Rückrunde an den Architekten.

### 2. Intake-Validierung — `hermes_schemas/intake.py`

Prüft Karten in *Eingang* gegen die Pflichtfelder der Vorlagen in
`../intake-vorlagen/`; unvollständige Karten weist der Worker mit dem
generierten Kommentar zurück (Duplikatschutz liegt beim Worker).

### 3. Kartenformat — `hermes_schemas/karte.py`

YAML-Front-Matter (`projekt`, `karte`, `dateien`) + Auftragstext; das
maschinenlesbare Bindeglied zwischen Materialisierung und Worker.

### 4. Noch offen: Materialisierung

Nach Freigabe deterministisch: Projekt-Repo per Copier, Karten via Board-API,
`ARCHITEKTUR.md` + rote Test-Stubs per einmaligem Aider-Lauf, Commit.
Braucht das existierende `skeleton-web`-Repo — nächste Session.
