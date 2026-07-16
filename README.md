# hermes-pipeline

Meta-Repo der Hermes Architektur-Pipeline — agentengetriebene Softwareentwicklung
in zwei Domänen (Web-Projekte, Windows-Device-Tools über Modbus TCP).

**[`ARCHITEKTUR.md`](ARCHITEKTUR.md) ist die Wahrheit.** Jede Änderung am System,
die die Architektur berührt, aktualisiert dieses Dokument mit.

## Struktur

```
hermes-pipeline/
├── ARCHITEKTUR.md      Systementwurf v2 (freigegeben zur Umsetzung) — die Wahrheit
├── ROADMAP.md          Orchestrierte Roadmap: Sessions, Aufteilung, Skill-Struktur
├── DECISIONS.md        Append-only-Log: Reviewer-Fails, Fix-Begründungen, Gate-Korrekturen
├── board/              Kanban-Board: Dashboard + Steuerung (FastAPI, HTMX, SQLite, Port 9119)
├── worker/             Poll-Worker (Python, SQLite, systemd-Unit)
├── schemas/            projekt.yaml-Pydantic-Schema, Kartenformat, Intake-Validierung
├── prompts/            Architekten-Prompt, Reviewer-Prompt (Entwürfe)
├── intake-vorlagen/    Die zwei Markdown-Templates (Neuprojekt / Änderung)
├── skills/
│   └── hermes-architekt/  Skill der Architekten-Rolle (selbsttragend, installierbar)
├── skripte/            Einmal-Werkzeuge (Kanban-Spalten anlegen)
└── templates/
    └── skeleton-web/   Copier-Template der Web-Domäne — ⚠️ NUR ZUM ENTWERFEN hier
```

**Skeleton-Abspaltung (16.07.2026):** Das Web-Skeleton lebt jetzt im eigenen
Repo **`github.com/max804/skeleton-web`** (Tags `web-v*`); die Kopie unter
`templates/skeleton-web/` dient nur noch den Tests dieses Meta-Repos.

## Einstieg

1. [`ARCHITEKTUR.md`](ARCHITEKTUR.md) lesen — Zielbild, Trio-Modell, Anti-Ziele.
2. [`ROADMAP.md`](ROADMAP.md) lesen — wer baut was, in welcher Reihenfolge.
3. [`INBETRIEBNAHME.md`](INBETRIEBNAHME.md) — Schritt-für-Schritt vom
   Checkout bis zum Piloten.
