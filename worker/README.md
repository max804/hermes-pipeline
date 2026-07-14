# worker/ — Der Poll-Worker

**Wird in Session 2 gebaut** (siehe `../ROADMAP.md`). Vertrag laut
`../ARCHITEKTUR.md` §4:

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

## Geplanter Inhalt

```
worker/
├── hermes_worker/        Python-Paket (Poll-Loop, Aider-Runner, Board-Client)
├── hermes-worker.service systemd-Unit
└── README.md
```
