# AI KanBan Orchestrator — Ausbauplan (Schalt- und Waltzentrale)

Stand: 20.07.2026 · Planungsdokument, noch nicht umgesetzt.
Ziel: Das heutige Board (`board/`, FastAPI+SQLite+HTMX, Port 9119/8199) zur
vollständigen Steuerzentrale ausbauen — Optik/Umfang orientiert an der
Vorlage `github.com/max804/KanBan-Dashboard` (nur Orientierung, kein 1:1).

> **Für eine neue Session:** Erst `ARCHITEKTUR.md`, `DECISIONS.md`,
> `deploy/README.md` und dieses Dokument lesen. Das Board liegt in `board/`,
> der Worker in `worker/`, der Vertrag zwischen beiden in
> `worker/hermes_worker/board.py` ↔ `board/hermes_board/app.py`.

## Grundsatzentscheidung: Handarbeit, nicht Pipeline-auf-sich-selbst

Der Orchestrator ist die Steuerfläche. Er wird in **interaktiven
Claude-Sessions** gebaut (wie Skeleton/Worker, §5.3/§21), NICHT über die
Pipeline — sonst verwaltet das Werkzeug seinen eigenen Umbau und ein Fehler
legt die Steuerung lahm (Anti-Fehler D). Die Domänen-Projekte (Web/Device)
laufen weiter durch die Pipeline. Spätere Orchestrator-Verbesserungen können
Change-Karten werden, sobald er stabil ist (der laufende Board-Prozess ist
vom Quellcode entkoppelt: Neustart erst bei grünem `make check`).

## Das Fundament zuerst: Zwei-Wege-Kanal Board ↔ Worker

Heute ist die Kopplung einseitig: der Worker pollt die Board-API, das Board
weiß nichts über den Worker (außer dem indirekten „letzter Poll"-Trick in
`app.py`). Fast alle Wünsche unten brauchen **zwei** neue Richtungen:

- **Worker → Board (Live-Status):** Was tut der Worker gerade? Welche Karte,
  welches Modell, welche Phase (Coder/Check/Review)? → speist Wunsch 5.
- **Board → Worker (Kommandos):** Aktionen, die das Board auslöst und der
  Worker ausführt (Repo anlegen, pushen, Preview-Server starten, mergen). →
  speist Wunsch 4.

Vorschlag: eine kleine gemeinsame Tabelle in der Board-SQLite
(`worker_status`, `kommandos`) plus zwei API-Endpunkte
(`POST /api/status` schreibt der Worker, `GET/POST /api/kommandos`).
Bewusst dieselbe langweilige Poll-Mechanik wie bisher (Anti-Fehler D). Das
ist der erste Baustein — ohne ihn hängen 4/5/6 in der Luft.

## Die sechs Wünsche — Einordnung

### 1. Änderungen per Agent automatisch in Karten einpflegen
Baut auf dem Bestehenden auf: Change-Intake (`intake-vorlagen/intake-aenderung.md`)
+ Architekt (`skills/hermes-architekt`) erzeugen bereits `projekt.yaml`→Karten.
Neu: ein niedrigschwelliger UI-Trigger („beschreibe die Änderung") statt
Karte-von-Hand. **Aufwand: mittel.** Abhängig von: Architekt-Anbindung (Wunsch 2).

### 2. Anbindung an Hermes-Agent + OpenRouter (mehr Modelle, Lernfähigkeit)
Architekt läuft ohnehin als Cloud-Frontier via Hermes (§2/§10). OpenRouter =
weitere OpenAI-kompatible `base_url` — technisch trivial (wir unterstützen
`openai_api_base` schon). „Lernfähigkeit" = Hermes-Memory nutzen (§4 erlaubt).
**Aufwand: klein–mittel**, v. a. Konfiguration/Integration, keine neue
Architektur.

### 3. Agenten + Skills per Drag & Drop zuordnen
Echte neue Fähigkeit. Braucht ein **Agenten-Register** (Name, Modell,
base_url, Rolle, Skill) als Datenmodell + UI, und der Worker wählt den Agenten
pro Karte/Spalte statt fixem `coder_modell`/`reviewer_modell`. **Aufwand: groß.**
Abhängig von: Agenten-Datenmodell (neu) und dem Zwei-Wege-Kanal.

### 4. Alles über die Plattform steuern — CLI abschaffen
Der große Hebel. Jede Handaktion wird ein Board-Kommando, das der Worker
ausführt: Projekt/Ordner anlegen, nach GitHub pushen, `make deploy`,
**Preview-Server im LAN starten wenn fertig** (auto-uvicorn + URL aufs Board),
mergen (löst zugleich das Board↔Git-Split-Brain, DECISIONS 2026-07-20).
**Aufwand: groß**, aber höchster Nutzen. Baut auf dem Zwei-Wege-Kanal.

### 5. Sehen, welches Modell gerade an welcher Karte arbeitet
Der Worker weiß es (worker.db: Karte↔Branch↔laufend). Nötig: Worker schreibt
aktuelle Tätigkeit (Karte, Modell, Phase) über `POST /api/status`, Board
zeigt sie (entspricht der „Agents-Toolbar"/„welcher Agent an welcher Karte"
der Vorlage). **Aufwand: klein–mittel**, sobald der Kanal steht. Sehr sichtbar.

### 6. GPU-Auslastung des LLM-Servers (192.168.178.27)
Externe Metrik. Kleiner Kollektor pollt den Server (Lemonade/Ollama-Stats
oder ein `nvidia-smi`-Endpunkt auf .27), Board zeigt sie als Kachel.
**Aufwand: klein–mittel**, isoliert. Abhängig davon, was .27 exponiert —
das ist zuerst zu klären (Skill `lemonade` prüfen: Auslastungs-Endpunkt?).

## Empfohlene Reihenfolge

1. **Zwei-Wege-Kanal** (Status + Kommandos) — das Rückgrat.
2. **Wunsch 5** (Live-„welches Modell an welcher Karte") — kleiner erster
   sichtbarer Gewinn, testet den Status-Kanal.
3. **Wunsch 4, schrittweise** — je ein Kommando pro Runde (erst „mergen"
   → schließt das Split-Brain; dann „Preview-Server starten"; dann
   „push/deploy"). Testet den Kommando-Kanal.
4. **Wunsch 6** (GPU-Kachel) — isoliert, jederzeit dazwischen machbar.
5. **Wunsch 2** (OpenRouter/Hermes-Anbindung) — Konfig-Erweiterung.
6. **Wunsch 3** (Agenten-Register + Drag&Drop) und **Wunsch 1**
   (Änderungs-Agent) — die größten Brocken, zuletzt, weil sie auf 2+4 aufbauen.

Grundsatz wie im Hauptbauplan: vertikale Durchstiche, ein Feature ganz fertig
(inkl. Tests, `make check` grün) bevor das nächste beginnt.

## Was heute schon steht (Ausgangspunkt)

- `board/` mit Topbar, Sidebar+System-Überblick, Kanban-Fenster im Stil der
  Vorlage; Drag&Drop; 5s-HTMX-Refresh; ehrlicher Worker-Status (letzter Poll);
  Client-Suche; Theme-Toggle. Tests in `board/tests/`.
- `ansicht.py` (ID-Chip, Farbe/Spalte, Relativzeit, Bauplan-Tag).
- Vorlage geklont analysiert: viele Fenster (Flow, Agents, Stats-Strip,
  Bottom-Strip mit 6 Analysefenstern) — bewusst noch NICHT gebaut, weil ohne
  echte Datenquelle. Dieser Plan liefert die Datenquellen nach.

## Offen zu klären (vor Umsetzung)
- Exponiert der Lemonade/Ollama-Server auf .27 GPU-/Auslastungsdaten? (Wunsch 6)
- Soll der Worker Kommandos synchron (im Poll-Tick) oder in einem eigenen
  Thread ausführen? (lange Aktionen wie Deploy) — Empfehlung: eigener Runner,
  Kommando-Tabelle mit Status pending/läuft/fertig/fehler.
- Preview-Server: fester Portbereich + Reverse-Proxy-Eintrag, oder je Projekt
  ein Port? (LAN-Sichtbarkeit, Wunsch 4)
