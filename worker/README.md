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

## Noch offen (nächste Session)

- **Materialisierung** (ARCHITEKTUR.md §3.4): Freigabe-Karte → Copier,
  Karten via Board-API, ARCHITEKTUR.md + rote Test-Stubs. Braucht das
  existierende `skeleton-web`-Repo.
- Squash-Merge nach Review (v1: manuell nach Review-Spalte)
