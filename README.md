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
├── worker/             Poll-Worker (Python, SQLite, systemd-Unit)
├── schemas/            projekt.yaml-Pydantic-Schema, Kartenformat, Intake-Validierung
├── prompts/            Architekten-Prompt, Reviewer-Prompt (Entwürfe)
├── intake-vorlagen/    Die zwei Markdown-Templates (Neuprojekt / Änderung)
└── templates/
    └── skeleton-web/   Copier-Template der Web-Domäne — ⚠️ NUR ZUM ENTWERFEN hier
```

**⚠️ Skeleton-Abspaltung:** `templates/skeleton-web/` liegt zum Entwerfen im
Monorepo. Vor dem ersten instanziierten Projekt muss es in ein eigenes Repo
mit eigener Tag-Historie (`web-v0.1.0`, …) umziehen, weil `copier update`
über Git-Tags des Template-Repos arbeitet (Details:
`templates/skeleton-web/README.md`).

## Einstieg

1. [`ARCHITEKTUR.md`](ARCHITEKTUR.md) lesen — Zielbild, Trio-Modell, Anti-Ziele.
2. [`ROADMAP.md`](ROADMAP.md) lesen — wer baut was, in welcher Reihenfolge.
3. Aktuelle Session aus der Roadmap aufnehmen.
