# BLAUPAUSE — Web-Domäne

Der Architektur-Vertrag dieser Domäne. Der **Architekt** instanziiert ihn
pro Projekt in der `projekt.yaml`; die **Coder** befolgen ihn. Änderungen an
diesem Dokument sind Skeleton-Änderungen und laufen nur über
Skeleton-Change-Karten mit strengem Gate.

## Schichtenmodell

**Route → Template → Komponente.** Keine Logik in Templates: Routen bereiten
alle Daten fertig auf (Sortierung, Formatierung, Statusableitung), Templates
komponieren ausschließlich Katalog-Komponenten, Komponenten sind dumm.
HTMX-Interaktionen liefern Fragmente über eigene `/partials/…`-Routen.

## Namenskonventionen

| Artefakt | Muster | Beispiel |
|---|---|---|
| Routen-Datei | `app/routes/<bereich>.py`, exportiert `router` — wird automatisch registriert, `main.py` nie anfassen | `app/routes/status.py` |
| Seiten-Template | `app/templates/<seite>.html` | `app/templates/index.html` |
| Fragment-Template | `app/templates/partials/<name>.html` | `partials/statusgrid.html` |
| Partial-Route | `GET /partials/<name>` | `/partials/statusgrid` |
| Karten-Test | `tests/test_karten/test_karte_<nr>.py` | `test_karte_07.py` |

## Erlaubte Bibliotheken (abgeschlossene Liste)

Laufzeit: **FastAPI, Jinja2, httpx, uvicorn** (+ `python-multipart` als
FastAPI-Formular-Unterbau) — sonst nichts.
Test: **pytest, html5lib**. Lint: **ruff**.

Jede weitere Bibliothek ist eine Architekturentscheidung: eigene Karte,
Begründung in `ARCHITEKTUR.md`, Eintrag in `DECISIONS.md`. Explizit gilt
das auch für Datenbank-Layer — siehe Verbote.

## Komponentenkatalog (Signaturen)

Import in jeder Seite:
`{% import "komponenten/katalog.html" as k %}`

| Komponente | Signatur | Zweck |
|---|---|---|
| Card | `k.card(titel, inhalt="", status=None)` oder `{% call k.card(titel) %}…{% endcall %}` | Inhaltskachel, optional mit Statusbadge |
| Tabelle | `k.tabelle(spalten, zeilen)` | Datenzeilen; `zeilen` = Liste von Listen |
| Statusbadge | `k.statusbadge(zustand)` | `ok` / `warn` / `fehler` |
| Formularfeld | `k.feld(name, label, typ="text", wert="", pflicht=False)` | Label + Input |
| Auswahl | `k.select(name, label, optionen, gewaehlt="")` | Dropdown |
| Absenden | `k.submit(text="Speichern")` | Primär-Button |
| Grid | `{% call k.grid(spalten=3) %}…{% endcall %}` | Responsives Kachel-Raster (1–4 Spalten) |
| Sektion | `{% call k.sektion(titel) %}…{% endcall %}` | Abschnitt mit Überschrift |

Der Architekt wählt pro Seite aus diesem Katalog; fehlt eine Komponente,
ist das eine Skeleton-Change-Karte — niemals eine Projekt-Improvisation.

## Design

Dark Mode ist der Standard und einzige Modus in v1. Farben kommen
ausschließlich aus den Katalog-Komponenten; Seiten setzen keine eigenen
Farb-, Abstands- oder Typografie-Klassen jenseits der Katalog-Nutzung.
`app/static/theme.css` ist kompiliertes Tailwind — nach Katalog-Änderungen
(nur via Skeleton-Karte) `make css`.

## Deployment-Muster

Letzte Karte jedes Projekts (vom Architekten standardmäßig eingeplant):
`deploy.sh` deployt den Stack per Portainer-API, Token **per Dateipfad**
(nie Klartext im Repo), Caddy-Snippet wird generiert, Reload erst nach
menschlicher Bestätigung. Healthcheck über die echte URL ist Teil der
Done-Definition.

## Explizit verboten

- **kein SQLAlchemy / keine Datenbank in v1** — Persistenz ist eine
  Architekturentscheidung mit eigener Karte
- **kein Auth ohne eigene Karte**
- **kein JavaScript** außer htmx-Attributen (vendorte `htmx.min.js`);
  keine zusätzlichen JS-Dateien, keine CDNs
- **keine eigenen Farben oder Komponenten** — nur Katalog
- **kein Node/npm im Projekt** — CSS wird mit der Tailwind-Standalone-CLI
  gebaut
