# Roadmap: Agenten-Setup und Dokumentationsstruktur

Stand: 14.07.2026 · abgeleitet aus `ARCHITEKTUR.md` (v2, freigegeben) · Status: verbindlich

Grundsatz vorweg (folgt aus der Logik des Architekturdokuments, Frage 21):
**Die Einrichtung ist keine Aufgabe für die Pipeline-Agenten**, sondern für
Mensch + Claude in interaktiven Arbeitssessions. Ein „Einrichtungs-Agent, der
alles selbständig aufbaut" wäre genau das Henne-Ei-Problem und der
Meta-Arbeits-Overhead (Fehler D), der im Entwurf ausgeschlossen wurde.
In den Sessions schreibt Claude ~90 % des Codes; der Mensch steuert und testet.

---

## 1. Repo-Struktur (dieses Meta-Repo)

```
hermes-pipeline/
├── ARCHITEKTUR.md          ← die v2-Datei — sie ist ab jetzt die Wahrheit
├── worker/                 ← der Poll-Worker (Python, SQLite, systemd-Unit)
├── schemas/                ← projekt.yaml-Pydantic-Schema, Intake-Validierung
├── prompts/                ← Architekten-Prompt, Reviewer-Prompt
└── intake-vorlagen/        ← die zwei Markdown-Templates (Neu / Change)
```

Die Skeletons sind bewusst **eigene Repos** (`skeleton-web`,
`skeleton-device-tool`), weil Copier sie als Template-Quelle braucht.

---

## 2. Was wer baut — die ehrliche Aufteilung

**Nur der Mensch (nicht delegierbar):**
- Geräteprofil-YAML-Schema (Modbus-Fachwissen)
- Abnahme des Komponentenkatalogs (Geschmacksurteil)
- jedes Freigabe-Gate

**Mensch + Claude interaktiv (die Handarbeits-Sessions):**
- Web-Skeleton mit Komponentenkatalog und Blaupause
- Poll-Worker
- `projekt.yaml`-Schema
- Architekten-Prompt
- systemd-Setup und `hermes-worker`-User

Hier schreibt Claude den Code, der Mensch führt aus und prüft — der schnellste
und sicherste Weg, kein autonomer Agent nötig.

**Trivial per Hand oder API-Call (5 Minuten):**
- Kanban-Spalten anlegen (Eingang → Architektur → Freigabe → Bereit →
  In Arbeit → Review → Done → Blockiert) auf Port 9119.

**Später die Pipeline selbst:**
- Skeleton-Verbesserungen als Change-Karten — aber erst, wenn die Pipeline
  einmal end-to-end gelaufen ist.

---

## 3. „Skills" bedeuten in der Pipeline zwei verschiedene Dinge

Sauber trennen, sonst entstehen doppelte Wissensbestände:

### 3.1 Der Architekt bekommt einen echten Skill: `hermes-architekt`

Neuer Skill im bestehenden Skill-Ökosystem. Inhalt:
- das `projekt.yaml`-Schema mit Beispiel
- die Kartenregeln (Pflichtfelder; eine Karte = ein Aider-Lauf; nur der
  Architekt erzeugt Karten)
- die Ein-Runden-Rückfrageregel
- Verweise auf die Blaupausen beider Domänen

Wird mit den vorhandenen Werkzeugen `skill-creator` + `writing-great-skills`
geschrieben (Session 4).

### 3.2 Coder und Reviewer bekommen **keine** Skills

Ihr Spezialwissen liegt im **Skeleton-Repo** — Aider lädt keine
Skill-Bibliothek; sein Kontext kommt aus dem Repo selbst. Konkret:
- Die Blaupause liegt als `BLAUPAUSE.md` im Skeleton.
- Dazu eine `AGENTS.md` (etablierter Kontext-Anker) mit den Coder-Regeln:
  nur Katalog-Komponenten, keine eigenen Farben, Tests grün machen,
  nie `make check` umgehen.
- Der Poll-Worker füttert Aider pro Lauf mit:
  **Kartentext + `ARCHITEKTUR.md` + `AGENTS.md`**.

Das ist das Template-plus-Spezialwissen-System: Es reist mit jedem per Copier
instanziierten Projekt automatisch mit, ohne zweite zu pflegende Wissensquelle.

### 3.3 Optional (Komfort, nicht Fundament): `pipeline-admin`

Selbstpflegender Skill nach dem Muster des Portainer-Skills — für den
Betreiber, um Worker-Status, Logs und blockierte Karten zu verwalten.
Erst nach stabilem Betrieb.

---

## 4. Session-Reihenfolge (= Bauplan Punkt 1–4, in Arbeitspakete übersetzt)

### Session 1 — Web-Skeleton ✅ gebaut (als `templates/skeleton-web/` in diesem Repo)
*⚠️ Vor dem Pilotprojekt in ein eigenes Repo `skeleton-web` mit eigener
Tag-Historie (`web-v0.1.0`, …) abspalten — `copier update` arbeitet über
Git-Tags des Template-Repos, eine mit Worker-Releases geteilte Tag-Historie
wird beim Update alter Projekte unentwirrbar. Solange kein instanziiertes
Projekt auf die Template-URL zeigt, ist der Umzug trivial.*
- Copier-Struktur ✅ (`copier.yml`: projektname, beschreibung, port,
  static_only, caddy_domain; nur `*.jinja` wird gerendert)
- FastAPI + Jinja2 + HTMX + Tailwind-Gerüst, `base.html` ✅
  (htmx 2.0.4 vendored, `theme.css` kompiliertes Tailwind v4 —
  kein Node, kein CDN im Projekt)
- Komponentenkatalog ✅: card, tabelle, statusbadge, feld/select/submit,
  grid, sektion — Sammel-Import über `komponenten/katalog.html`
- `BLAUPAUSE.md` (Vertrag) + `AGENTS.md` (Coder-Leitplanken) ✅
- `Dockerfile.check`, `make check` (ruff + pytest: Smoke über alle Routen,
  strikte HTML5-Validierung, Karten-Tests) ✅
- `deploy.sh` (Portainer-API, Token per Dateipfad, Caddy-Snippet nur
  generiert) ✅

**Abnahmetest:** In 30 Minuten von Hand eine Seite darin bauen können —
**steht noch aus** (macht der Mensch, nicht die Maschine).

### Session 2 — Poll-Worker minimal (`worker/` in diesem Repo) ✅ gebaut
- Board-API pollen (30 s), Branch anlegen, Aider-Lauf mit Timeout (20 min)
- `make check` im Container, Spalte umhängen
- SQLite-Zustand (`worker.db`), Telegram-Ping
- `hermes-worker`-User (sudo-los) und systemd-Unit

### Session 3 — Vertragsschicht (`schemas/`, `intake-vorlagen/`) ✅ weitgehend gebaut
- Pydantic-Schema für `projekt.yaml` ✅
- Intake-Validierung (Pflichtfelder, Zurückweisen mit Kommentar) ✅
- die zwei Markdown-Vorlagen ✅
- Kartenformat (Front-Matter) ✅
- Materialisierungs-Schritt: YAML → Karten via Board-API + `ARCHITEKTUR.md`
  + rote Test-Stubs — **offen, braucht `skeleton-web`**

### Session 4 — Skill `hermes-architekt` + Board
- Skill mit `skill-creator` schreiben (Inhalt siehe 3.1) —
  inhaltlicher Entwurf liegt in `prompts/architekten-prompt.md`
- Reviewer-Prompt-Entwurf liegt in `prompts/reviewer-prompt.md`
- Kanban-Spalten anlegen (Port 9119)

### Session 5 — Pilot: Homelab-Statusseite
- Intake-Karte ausfüllen (HTTP-Healthchecks für Portainer, n8n, Ollama,
  Grafana als Kachel-Dashboard, ≤10 Karten)
- Pipeline laufen lassen, beobachten
- **jeden Reibungspunkt in `DECISIONS.md` notieren**

Danach: Nachschärfen, dann Device-Tool-Skeleton (Bauplan 5–7 in
`ARCHITEKTUR.md` §11).

**Werkzeug für Sessions 1–3:** Claude Code auf dem Strix Halo — arbeitet
direkt in den Repos, führt `make check` selbst aus und committet sauber.
