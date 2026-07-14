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
├── worker/             Poll-Worker (Python, SQLite, systemd-Unit)          → Session 2
├── schemas/            projekt.yaml-Pydantic-Schema, Intake-Validierung    → Session 3
├── prompts/            Architekten-Prompt, Reviewer-Prompt                 → Session 3–4
└── intake-vorlagen/    Die zwei Markdown-Templates (Neuprojekt / Änderung)
```

Die **Skeletons sind bewusst eigene Repos** (`skeleton-web`, `skeleton-device-tool`),
weil Copier sie als Template-Quelle braucht. Sie gehören nicht hierher.

## Einstieg

1. [`ARCHITEKTUR.md`](ARCHITEKTUR.md) lesen — Zielbild, Trio-Modell, Anti-Ziele.
2. [`ROADMAP.md`](ROADMAP.md) lesen — wer baut was, in welcher Reihenfolge.
3. Aktuelle Session aus der Roadmap aufnehmen.
