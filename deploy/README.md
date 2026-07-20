# Hermes-Pipeline als Docker-Image

Die ganze Pipeline (Board + Worker) als **ein Image**, betrieben als zwei
Container. Auf einem neuen System: Repo holen, `.env` ausfüllen, `up` — läuft.

## Voraussetzungen auf dem Zielsystem

- Docker + Docker Compose
- Netzzugang zu deinem LLM-Server (Lemonade/Ollama) und zu GitHub
  (Copier zieht das Skeleton von `gh:max804/skeleton-web`)
- x86_64 (für arm64 im `Dockerfile` die `DOCKER_CLI_URL` anpassen)

## Installation

```bash
git clone https://github.com/max804/hermes-pipeline.git
cd hermes-pipeline/deploy
cp .env.example .env
nano .env                 # LLM-Adresse, Modelle, ggf. Telegram eintragen
sudo mkdir -p /opt/hermes # geteilter, persistenter Zustand
docker compose up -d --build
```

Board öffnen: `http://<host>:9119` (bzw. `HERMES_BOARD_PUBLISH` aus der .env).

## Prüfen

```bash
docker compose ps
curl -s http://localhost:9119/healthz          # {"status":"ok",...}
docker compose logs -f worker                  # alle 30 s ein Poll, kein Fehler
```

Kurztest der Kette: im Board „+ Leere Karte" in *Eingang* anlegen — der
Worker kommentiert sie binnen ~30 s (unvollständiger Intake). Danach steht
dem ersten echten Projekt nichts im Weg (Ablauf: `../INBETRIEBNAHME.md` §7).

## Was wo liegt

Alles Persistente unter **`/opt/hermes`** (auf Host und im Container
derselbe Pfad — siehe unten):

- `projekte/` — die instanziierten Projekt-Repos
- `board.db`, `worker.db` — SQLite-Zustand
- `config.yaml` — vom Entrypoint aus der `.env` gerendert
- `telegram-token` — nur falls Telegram gesetzt

Backup = dieses Verzeichnis sichern. Update = `git pull && docker compose up -d --build`.

## Warum der Host-Docker-Socket?

Der Worker führt LLM-geschriebenen Code niemals direkt aus, sondern nur in
einem wegwerfbaren, **netzlosen** Container (`make check`, ARCHITEKTUR §7).
Dafür braucht er Docker — hier über den gemounteten Host-Socket
(`/var/run/docker.sock`). Die Check-Container laufen also als Geschwister
auf dem Host.

**Deshalb muss `/opt/hermes` auf Host und Container identisch sein:** Der
Worker startet `docker run -v /opt/hermes/projekte/<x>:/work …`, und dieser
Bind-Mount wird vom **Host**-Daemon aufgelöst. Nur bei gleichem Pfad zeigt
er auf dasselbe Verzeichnis. Wer den Pfad ändern will, ändert ihn an allen
drei Stellen in `docker-compose.yml` (beide `volumes` + `HERMES_STATE`) gleich.

**Sicherheitshinweis:** Der Docker-Socket gibt dem Worker-Container
Host-Docker-Rechte (≈ root auf dem Host). Betreibe das nur in deinem
vertrauten Homelab, nicht offen im Netz. Kein Reverse-Proxy ohne Auth davor.

## Reviewer an/aus

`HERMES_REVIEWER_MODELL` in der `.env`:
- gesetzt → Worker reviewt automatisch und squash-merged bei OK nach `main`
- leer → Karten bleiben in *Review*, du mergst von Hand
  (`../skripte/karte-mergen.sh`)

Nach Änderung: `docker compose up -d` (rendert die Config neu).
