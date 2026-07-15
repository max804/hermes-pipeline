# worker/ — Der Poll-Worker

**Status: Minimalversion gebaut** (Session 2, siehe `../ROADMAP.md`).
Vertrag laut `../ARCHITEKTUR.md` §4:

Ein einzelner Python-Daemon auf dem Strix Halo, als systemd-Service, unter
einem eigenen sudo-losen Linux-User `hermes-worker` (Home enthält nur
`~/projekte` und die Worker-Datenbank).

## Verbindliche Eckpunkte

- Pollt alle 30 Sekunden die Board-API (Port 9119): Karten in *Bereit* ohne
  laufenden Bearbeiter → Aider-Lauf starten
- Kein Event-Push, keine Webhooks, keine Queue — langweilig und debugbar
- Zustand: eine SQLite (`worker.db`) mit Karte ↔ Prozess ↔ Versuchszähler;
  überlebt den eigenen Neustart
- Observability: strukturiertes Logfile + Telegram-Meldungen
- 20-Minuten-Timeout pro Aider-Lauf: Prozess killen, Branch verwerfen,
  Karte zurück auf *Bereit*, Zähler +1
- Maximal 3 Versuche pro Karte, dann *Blockiert* + Telegram-Ping
- Aider-Kontext pro Lauf: Kartentext + `ARCHITEKTUR.md` + `AGENTS.md`
  (aus dem Projekt-Repo)
- `make check` läuft im Container:
  `docker run --rm --network none --memory 8g --cpus 4 -v <repo>:/work`
- Der Worker selbst läuft **nicht** in Docker — Aider braucht direkten
  Repo-Zugriff

## Inhalt

```
worker/
├── hermes_worker/
│   ├── worker.py          Poll-Schleife und Karten-Zustandsmaschine
│   ├── board.py           Board-API-Client — Endpunkt-ANNAHMEN, siehe unten
│   ├── state.py           SQLite-Zustand (worker.db)
│   ├── aider_runner.py    Ein Aider-Lauf = eine Karte, 20-min-Timeout
│   ├── checks.py          make check im netzlosen Container
│   ├── repo.py            Branch pro Karte, Verwerfen bei Abbruch
│   ├── telegram.py        Meldungen (No-op wenn unkonfiguriert)
│   ├── config.py          YAML-Konfiguration ($HERMES_WORKER_CONFIG)
│   └── __main__.py        Daemon-Einstieg
├── tests/                 pytest mit Fake-Board/-Aider und echtem Wegwerf-Git-Repo
├── hermes-worker.service  systemd-Unit inkl. Installationsanleitung im Kopf
└── config.beispiel.yaml
```

## Vor dem ersten echten Lauf zu verifizieren

1. **Board-API-Endpunkte**: Die Pfade in `hermes_worker/board.py` sind
   Annahmen — gegen das echte Hermes-Kanban (Port 9119) prüfen und nur
   dort anpassen.
2. **Aider-Aufrufparameter** in `aider_runner.py` gegen die installierte
   Aider-Version prüfen (`--message-file`, `--read`, `--yes-always`).
3. `hermes-worker`-User anlegen (Anleitung im Kopf der systemd-Unit),
   Config nach `/home/hermes-worker/config.yaml`.

## Materialisierung (`hermes_worker/materialisierung.py`)

Eine freigegebene Karte, deren Beschreibung eine valide projekt.yaml trägt
(roh oder als ```yaml-Block), wird vom Menschen nach *Bereit* gezogen. Der
Worker erkennt sie und erzeugt deterministisch: Repo per Copier
(`template_quellen` in der Config), projekt.yaml + gerenderte ARCHITEKTUR.md
im Repo, Test-Stubs als `…py.wartend` (scharfgeschaltet erst beim Start der
jeweiligen Karte — Begründung: DECISIONS.md), Commit, Coder-Karten in
topologischer Reihenfolge nach *Bereit*. Change-Projekte (Repo existiert):
keine Instanziierung, ARCHITEKTUR.md bleibt unangetastet.

## Reviewer-Lauf (`hermes_worker/reviewer.py`)

Aktiv, sobald `reviewer_modell` in der Config gesetzt ist (leer = Review
bleibt beim Menschen — so bleibt es, bis der Bug-Diff-Test das Zweitmodell
entschieden hat). Pro Tick eine Karte aus *Review*:

- Aider-`/ask` mit dem Zweitmodell: Kartentext + Diff (`main...branch`,
  gekürzt auf 30 kB) + ARCHITEKTUR.md/AGENTS.md read-only
- `URTEIL: OK` → Squash-Merge nach main als `[K##] Titel`, Branch weg,
  Karte nach *Done*
- `URTEIL: FIX` → Fix-Rückläufer: Befunde als Kommentar + `letzte_pruefung`,
  Karte zurück nach *Bereit*, Zähler +1 (ab 3 → *Blockiert* + Ping)
- unparsebar/Timeout → *Blockiert* + Ping (Mensch schiebt zurück nach
  *Review* für einen neuen Versuch)

**Sequenz-Wächter:** Projekte mit Karte in *Review*, *In Arbeit* oder
*Blockiert* starten keine neue *Bereit*-Karte — sie würde auf einem main
aufbauen, dem der ungemergte Vorgänger fehlt.

## Noch offen

- Manueller Cloud-Retry für blockierte Karten (ARCHITEKTUR.md §10,
  „Eskalation") — v1: von Hand
