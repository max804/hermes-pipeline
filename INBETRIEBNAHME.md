# Inbetriebnahme — Schritt für Schritt zum Piloten

Reihenfolge verbindlich; jeder Schritt endet mit einem Prüfpunkt.
Voraussetzungen auf dem Strix Halo: Python ≥ 3.11 **inklusive
venv-Unterstützung** (Debian/Ubuntu: `sudo apt install python3.12-venv` —
sonst scheitert `make setup` mit „ensurepip is not available"; danach
`rm -rf .venv` und neu ausführen), git, Docker, Ollama (mit qwen3-coder
gezogen), Aider.

---

## Schritt 1 — Branch mergen und Repo holen

Alles liegt auf dem Branch `claude/agent-setup-roadmap-21cm1o`. Auf GitHub
nach `main` mergen (oder Claude eine PR öffnen lassen), dann:

```bash
mkdir -p ~/hermes && cd ~/hermes
git clone git@github.com:max804/hermes-pipeline.git
cd hermes-pipeline
make setup
make check
```

**Prüfpunkt:** 69 Tests grün (25 schemas / 32 worker / 12 board).

## Schritt 2 — Board starten und ansehen

> **Portentscheidung (15.07.2026):** Auf dem Zielrechner belegt das alte
> Hermes (Prozess `hermes`) weiterhin Port 9119. Das neue Board läuft
> deshalb auf **9120** — überall, wo unten 9119 stünde, gilt 9120.

```bash
HERMES_BOARD_PORT=9120 .venv/bin/hermes-board
```

Browser: `http://localhost:9120` (bzw. `http://<strix-ip>:9120` im LAN).

**Prüfpunkt:** Acht Spalten sichtbar, „+ Neues Projekt" öffnet das Formular
mit vorbelegter Intake-Vorlage, eine Testkarte lässt sich per Drag & Drop
verschieben. (Danach Testkarte auf *Done* parken oder DB löschen:
`rm ~/hermes-board.db*`.)

## Schritt 3 — 30-Minuten-Abnahmetest am Skeleton

Das ist dein nicht delegierbares Urteil (ARCHITEKTUR.md §5.3):

```bash
.venv/bin/copier copy --trust templates/skeleton-web ~/projekte/probe
cd ~/projekte/probe
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Baue in 30 Minuten von Hand eine Seite — **nur** aus Katalog-Komponenten
(`{% import "komponenten/katalog.html" as k %}`, Signaturen in
`BLAUPAUSE.md`). Bewerte: Reichen die Komponenten? Gefallen dir die
Farbtoken? Fehlt etwas → Notiz; das wird eine Skeleton-Änderung, kein Hack.

Direkt hinterher die Sandbox testen (das macht später der Worker):

```bash
docker build -f Dockerfile.check -t probe-check .
docker run --rm --network none --memory 8g --cpus 4 -v "$PWD":/work -w /work probe-check make check
```

**Prüfpunkt:** Seite gebaut, `make check` im Container grün.

## Schritt 4 — Aider-Probelauf (Coder-Kommando verifizieren)

Im Probe-Projekt genau das Kommando fahren, das der Worker baut:

```bash
cd ~/projekte/probe && git init -b main && git add -A && git commit -m init
echo "Füge in app/routes/pages.py einen Kommentar '# probe' hinzu." > /tmp/auftrag.md
aider --yes-always --model ollama_chat/qwen3-coder \
      --message-file /tmp/auftrag.md \
      --read ARCHITEKTUR.md --read AGENTS.md \
      app/routes/pages.py
```

**Prüfpunkt:** Aider läuft ohne Rückfragen durch und committet. Falls deine
Aider-Version Flags anders nennt: einzige Anpassungsstelle ist
`worker/hermes_worker/aider_runner.py` (und `reviewer.py` für
`--chat-mode ask`).

## Schritt 5 — Skeleton abspalten (vor dem Piloten!)

`copier update` braucht eigene Tags. Leeres GitHub-Repo `skeleton-web`
anlegen, dann entweder Claude machen lassen („füge skeleton-web hinzu")
oder von Hand:

```bash
cd ~/hermes
git clone git@github.com:max804/skeleton-web.git
cp -r hermes-pipeline/templates/skeleton-web/* skeleton-web/
cd skeleton-web && git add -A && git commit -m "skeleton-web v0.1.0 (aus hermes-pipeline abgespalten)"
git tag web-v0.1.0 && git push -u origin main --tags
```

Ab jetzt ist das Skeleton-Repo die Wahrheit; die Kopie unter
`templates/` im Meta-Repo dient nur noch den Tests.

**Prüfpunkt:** `copier copy gh:max804/skeleton-web /tmp/x` funktioniert.

## Schritt 6 — Worker-User, Dienste, Konfiguration

```bash
sudo useradd --create-home --shell /usr/sbin/nologin hermes-worker
sudo usermod -aG docker hermes-worker
sudo -u hermes-worker bash -c '
  cd ~ && git clone https://github.com/max804/hermes-pipeline.git
  python3 -m venv .venv
  .venv/bin/pip install -e hermes-pipeline/schemas -e hermes-pipeline/worker -e hermes-pipeline/board aider-chat
  mkdir -p ~/projekte
  cp hermes-pipeline/worker/config.beispiel.yaml ~/config.yaml
'
sudoedit /home/hermes-worker/config.yaml
```

In der `config.yaml` anpassen:
- `board_url: "http://127.0.0.1:9120"` (Portentscheidung aus Schritt 2!)
- `aider_bin: "/home/hermes-worker/.venv/bin/aider"`
- `template_quellen: {web: "gh:max804/skeleton-web"}`
- `telegram:` Token-Datei + Chat-ID (oder leer lassen → nur Logfile)
- `reviewer_modell:` **leer lassen** (bis Schritt 9)

In der kopierten `hermes-board.service` außerdem die Zeile
`Environment=HERMES_BOARD_PORT=9119` auf `9120` ändern, **bevor**
`daemon-reload` läuft.

Dienste:

```bash
sudo cp /home/hermes-worker/hermes-pipeline/board/hermes-board.service /etc/systemd/system/
sudo cp /home/hermes-worker/hermes-pipeline/worker/hermes-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-board hermes-worker
journalctl -fu hermes-worker
```

**Prüfpunkt:** Board unter Port 9119 erreichbar, Worker-Log zeigt alle
30 s einen Poll ohne Fehler.

## Schritt 7 — Pilot (Session 5): Homelab-Statusseite

1. **Intake:** Board → „+ Neues Projekt", Vorlage ausfüllen (Domäne web,
   Ziel 3–5 Sätze, Muss-Funktionen, Explizit-nicht, Routenliste), Karte in
   *Eingang*. Der Worker validiert — unvollständig = Kommentar, vollständig
   = *Architektur*.
2. **Architektur:** Hermes-Session mit dem Skill `hermes-architekt`
   (`cp -r skills/hermes-architekt ~/.claude/skills/`). Ergebnis-
   `projekt.yaml` mit `hermes-validiere projekt.yaml` prüfen, dann als
   ```yaml-Block in die Kartenbeschreibung (Detailseite → Bearbeiten) und
   Karte nach *Freigabe* ziehen.
3. **Freigabe-Gate:** Zehn Minuten lesen, korrigieren. Freigeben = Karte
   nach *Bereit* ziehen. Der Worker materialisiert: Repo, ARCHITEKTUR.md,
   Stubs, Coder-Karten.
4. **Zuschauen:** Coder-Karten laufen sequenziell. Grün landet in *Review*.
   **Solange der Reviewer aus ist, bist du der Reviewer** — und wegen des
   Sequenz-Wächters startet die nächste Karte erst, wenn du die Review-Karte
   erledigst:

   ```bash
   cd ~/projekte/homelab-status
   git log main..karte/01-healthcheck-modul --oneline && git diff main...karte/01-healthcheck-modul
   git checkout main && git merge --squash karte/01-healthcheck-modul
   git commit -m "[K01] Healthcheck-Modul" && git branch -D karte/01-healthcheck-modul
   ```

   Danach Karte im Board nach *Done* ziehen.
5. **Jeden Reibungspunkt sofort in `DECISIONS.md` notieren** — das ist der
   eigentliche Ertrag des Piloten.

**Prüfpunkt:** Deploy-Karte durchgelaufen, Statusseite antwortet über die
echte URL.

## Schritt 8 — Nachschärfen

DECISIONS.md durchgehen und die Reibungspunkte als Aufgaben an Claude
zurückspielen (interaktive Session, wie bisher).

## Schritt 9 — Bug-Diff-Test, dann Reviewer scharf schalten

In einen Karten-Diff drei absichtliche Fehler einbauen (z. B. erfundene
Farbklasse, abgeschwächter Test, vertauschte Parameter) und je Kandidat:

```bash
aider --chat-mode ask --model ollama_chat/<kandidat> --message-file /tmp/review-auftrag.md
```

Das Modell, das alle drei findet (Kandidaten: qwen3.6, gpt-oss, ornith),
in `config.yaml` als `reviewer_modell` eintragen,
`sudo systemctl restart hermes-worker`. Ab dann: Review, Squash-Merge und
Done vollautomatisch.

## Danach (mit Claude)

- Device-Tool-Skeleton (Bauplan §11, Punkte 6–7) — erst nach dem Piloten
- Optional: manueller Cloud-Retry für blockierte Karten, `pipeline-admin`-Skill
