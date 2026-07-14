# Hermes Architektur-Pipeline v2

**Systementwurf für agentengetriebene Softwareentwicklung**
Stand: 14.07.2026 · Ergebnis der Grilling-Session · Status: freigegeben zur Umsetzung

---

## 1. Ziel und Abgrenzung

Aus einer strukturierten Projekteingabe entsteht über das Hermes-Kanban automatisch professionelle Software — in genau zwei Domänen: Web-Projekte (statische Seiten bis Web-Apps) und Windows-Desktop-Tools zur Konfiguration von Mikrocontrollern über Modbus TCP.

Das System ist ein **Neubau** (nicht Erweiterung der alten Pipeline), zieht aber gezielt Inspiration aus ihr. Die diagnostizierten Fehler der alten Pipeline sind als Anti-Ziele verbindlich:

| Fehler alt | Gegenmaßnahme neu |
|---|---|
| **A** — kein Architektur-Schritt, Agenten codeten drauflos | Dedizierter Architekt mit Freigabe-Gate vor jeder Codezeile |
| **C** — zu generisch, kein Domänenwissen, Mittelmaß | Nur zwei Domänen, je ein zementiertes Skeleton + Blaupause |
| **D** — Überkomplexität (11 Profile, 3 Datenbanken), nie stabil | Trio-Modell, Poll-Worker statt Event-Infrastruktur, Git statt Datenbanken |

Der Leitgedanke des gesamten Entwurfs: **Intelligenz wird vorn konzentriert (Architektur, Test-Stubs), hinten bleibt Fleißarbeit in engen Leitplanken.** Qualität entsteht nicht dadurch, dass Agenten gut würfeln, sondern dadurch, dass Skeletons nur gute Ergebnisse zulassen.

---

## 2. Die drei Agentenrollen (Trio-Modell)

Es gibt exakt drei Rollen. Erweiterung ist später möglich, Schrumpfen wäre es nicht — deshalb startet das System minimal.

**Architekt** — läuft als Hermes-Session mit einem Cloud-Frontier-Modell (einmal pro Projekt, größter Qualitätshebel, Cent-Beträge). Er liest die Projekteingabe, stellt maximal eine gesammelte Rückfragerunde per Telegram, instanziiert die Blaupause und liefert als einziges Abgabe-Artefakt eine `projekt.yaml` (siehe Abschnitt 6). **Nur der Architekt darf Karten erzeugen.**

**Coder** — läuft als direkter Aider-Lauf mit qwen3-coder (lokal, Ollama auf dem Strix Halo). Er arbeitet genau eine Karte pro Lauf ab, im Skeleton, gegen die Blaupause, auf einem eigenen Branch. Er erzeugt keine Karten.

**Reviewer** — läuft als Aider-`/ask`-Lauf mit einem lokalen Zweitmodell, das architektonisch verschieden vom Coder sein muss (Kandidaten: qwen3.6, gpt-oss, ornith — endgültige Wahl empirisch per Bug-Diff-Test: erkennt das Modell drei absichtlich eingebaute Fehler in einem Diff?). Sein LLM-Urteil ist nur eine Stimme; die harte Wahrheit liefert `make check`. Er darf ausschließlich Fix-Rückläuferkarten erzeugen.

Doku und Deployment sind keine eigenen Agenten, sondern Karten, die der Coder abarbeitet.

---

## 3. Kanban-Board und Ablauf

Das bestehende Hermes-Kanban (API auf Port 9119) bleibt das Board. Spalten:

**Eingang → Architektur → Freigabe (Mensch) → Bereit → In Arbeit → Review → Done**, plus **Blockiert** für Eskalationen.

Der Ablauf eines Projekts:

1. **Intake:** Eine Karte in *Eingang* mit ausgefüllter Markdown-Vorlage (Pflichtfelder: Domäne, Ziel in 3–5 Sätzen, Muss-Funktionen, Explizit-nicht; bei device-tool zusätzlich die rohe Registermap, bei web die Seiten-/Routenliste). Der Worker validiert die Pflichtfelder und weist unvollständige Karten mit Kommentar zurück.
2. **Architektur:** Hermes-Session entwirft, darf einmal gesammelt rückfragen, liefert `projekt.yaml`. Der Worker validiert das YAML gegen ein Pydantic-Schema (Pflichtfelder, Abhängigkeits-IDs existent und zyklenfrei, Dateipfade im Skeleton-Namensraum). Validierungsfehler gehen als eine Rückrunde an den Architekten.
3. **Freigabe-Gate (der einzige Pflicht-Eingriff des Menschen):** Die valide `projekt.yaml` hängt an der Freigabe-Karte. Zehn Minuten lesen, korrigieren, freigeben. Der höchste Hebel bei den billigsten Korrekturkosten.
4. **Materialisierung:** Nach Freigabe erzeugt der Worker deterministisch: Projekt-Repo per Copier, Karten via Board-API, `ARCHITEKTUR.md` und rote Test-Stubs per einmaligem Aider-Lauf, Commit.
5. **Coder-Schleife:** Karten in *Bereit* werden sequenziell (ein Agent pro Projekt, keine Parallelität in v1) abgearbeitet. Grün → Done. Rot → Fix-Runde, maximal **3 Versuche**, dann *Blockiert* + Telegram-Ping. Bei blockierten Karten optional manueller Retry mit Cloud-Modell.
6. **Abschluss:** Web-Projekte enden mit einer Deploy-Karte (Abschnitt 9), Device-Tools mit einem Release-Tag, der den Windows-Build auslöst (Abschnitt 8).

**Änderungen an Bestandsprojekten** laufen über eine zweite Intake-Vorlage („Änderung an Projekt X"): identischer Ablauf, nur ohne Copier-Instanziierung. Verbindliche Regel: Jede Change-Karte, die die Architektur berührt, enthält als Akzeptanzkriterium die Aktualisierung von `ARCHITEKTUR.md` — das Dokument muss immer die Wahrheit bleiben.

---

## 4. Der Poll-Worker

Ein einzelner Python-Daemon auf dem Strix Halo, als systemd-Service, unter einem eigenen sudo-losen Linux-User `hermes-worker`, dessen Home nur `~/projekte` und die Worker-Datenbank enthält (SSH-Keys und persönliches Home damit außer Reichweite).

Er pollt alle 30 Sekunden die Board-API: Karten in *Bereit* ohne laufenden Bearbeiter → Aider-Lauf starten. Kein Event-Push, keine Webhooks, keine Queue — langweilig und debugbar, bewusst das Gegenteil von Fehler D.

Zustand: eine winzige SQLite (`worker.db`) mit Karte ↔ laufender Prozess ↔ Versuchszähler. Damit überlebt der Worker den eigenen Neustart sauber. Observability: strukturiertes Logfile plus Telegram-Meldungen. Kein Neo4j, kein Qdrant, kein InfluxDB in v1 — Git ist das Gedächtnis (`ARCHITEKTUR.md`, `DECISIONS.md` als Append-only-Log für Reviewer-Fails, Fix-Begründungen und Gate-Korrekturen). Qdrant-Wiederanschluss ist als Option notiert, falls nach 10+ Projekten projektübergreifende Suche gebraucht wird. Hermes (der Architekt) darf sein bestehendes Memory weiter nutzen.

**Harte Laufzeitregeln:** 20-Minuten-Timeout pro Aider-Lauf (Worker killt den Prozess, behandelt es wie Abbruch: Branch verwerfen, Karte zurück auf *Bereit*, Zähler +1). Kein Docker für den Worker selbst — Aider braucht direkten Repo-Zugriff.

---

## 5. Templates: Skeletons und Blaupausen

Pro Domäne existieren zwei zusammengehörige Artefakte:

**Skeleton** (lauffähiges Code-Gerüst als **Copier**-Template auf GitHub): zementiert Architekturentscheidungen in Code, den ein LLM nicht ignorieren kann. Copier statt einfachem Clone wegen sauberer Platzhalter und vor allem `copier update` — Skeleton-Verbesserungen lassen sich später in laufende Projekte nachziehen.

**Blaupause** (Architekturdokument): der Vertrag, den der Architekt instanziiert und die Coder befolgen — Modulschnitt, Namenskonventionen, erlaubte Bibliotheken, Kommunikationsmuster, explizite Verbote.

### 5.1 Web-Skeleton (`skeleton-web`)

Stack: **FastAPI + Jinja2 + HTMX + Tailwind CSS**, ein einziges Skeleton für beide Fälle — statische Seiten sind die Minimalausprägung (keine Routen außer Auslieferung). Enthält: `base.html` mit Layout, Tailwind-Theme (Farben, Abstände, Dark Mode als Standard), fertige Jinja2-Macros/Komponenten (Card, Tabelle, Statusbadge, Formularfeld), `Dockerfile` + `compose.yaml` + `deploy.sh` (Portainer-API), `Dockerfile.check` und `make check` (pytest + HTTP-Smoke-Test + HTML-Validierung).

**Designsystem-Regel:** Die Blaupause verbietet Codern, eigene Farben oder Komponenten zu erfinden — sie dürfen nur aus dem Komponentenkatalog komponieren. Der Architekt wählt pro Seite aus dem Katalog. Abnahmetest des Katalogs: Das Pilotprojekt muss sich vollständig daraus bauen lassen, ohne ein einziges frei erfundenes rohes Styling.

### 5.2 Device-Tool-Skeleton (`skeleton-device-tool`)

Stack: **Python + NiceGUI (native mode) + asyncio + pymodbus**, gebündelt als .exe via nicegui-pack. Begründung der Stack-Wahl: niedrigste LLM-Fehlerquote, schnellste eigene Diagnose, eingespielte Toolchain — nicht „die beste Windows-Technologie", sondern die beste für agentengenerierte Software.

Herzstück ist das **deklarative Geräteprofil**: ein YAML-Schema (`device-profiles/*.yaml`) mit Registeradresse, Name, Datentyp (inkl. Byte-/Word-Order bei float32!), Einheit, Min/Max, Zugriffsart, Modbus-Funktionscode. Die UI (Gerätebaum, Einstellmasken) wird generisch aus dem Profil gerendert — neues Gerät heißt neue YAML-Datei, null Codeänderung. Das Schema selbst wird von Hand definiert (Modbus-Fachwissen ist nicht delegierbar); die Registermap kommt roh mit der Projekteingabe, der Architekt formalisiert sie.

Weitere Bestandteile: Protokoll-Abstraktionsschicht (`DeviceProtocol`-Interface, pymodbus als erste Implementierung — spätere Protokolle sind Plugins, kein Umbau), Geräte-Discovery in v1 als IP-Liste plus „Netz scannen"-Button (Connect-Versuch auf Port 502 über den Bereich), **Modbus-Simulator** (pymodbus-Server) als Pflichtbestandteil — ohne ihn könnte kein Test der Kernfunktion je laufen —, NiceGUI-Wrapper-Komponenten im etablierten Dark-Mode-Stil, GitHub-Actions-YAML für den Windows-Build, `Dockerfile.check` und `make check` (pytest + ruff + mypy + Simulator-Integrationstests).

Als spätere Firmware-Konvention notiert: Geräte liefern ihr Profil selbst (erster Schritt: ein „Profil-Version"-Holding-Register).

### 5.3 Entstehung und Pflege

Die Erstversion beider Skeletons, Blaupausen und des Komponentenkatalogs entsteht in **Handarbeit** (interaktive Sessions mit Claude, außerhalb der Pipeline) — was zementiert wird, muss beim Gießen stimmen. Qualitätsmaßstab: „Kann ich selbst in diesem Skeleton in 30 Minuten von Hand eine Seite bauen?" Danach laufen Skeleton-Verbesserungen als normale Change-Karten durch die Pipeline, mit besonders strengem Gate (Skeleton-Fehler multiplizieren sich in alle Projekte), und `copier update` trägt sie in Bestandsprojekte.

---

## 6. Der Architekten-Vertrag: `projekt.yaml`

Das einzige Abgabe-Artefakt des Architekten, validiert per Pydantic-Schema, Grundlage des Freigabe-Gates, wandert anschließend ins Repo (die Projekthistorie beginnt mit ihrem eigenen Bauplan). Inhalt:

- **Architektur-Metadaten:** instanzierte Blaupause — Modulschnitt, Datenmodell, Routen bzw. Geräteprofile, und explizit Ausgeschlossenes („kein Auth in v1")
- **Kartenliste** nach Pflichtschema: Titel, Ziel (ein Satz), **betroffene Dateien (Pflichtfeld)**, maschinenprüfbar formulierte Akzeptanzkriterien, Abhängigkeits-ID. Kartengröße: eine Karte = ein Aider-Lauf = grob eine Dateigruppe
- **Test-Stub-Inhalte:** pro Karte rote Tests (`test_karte_07.py`), die der Coder grün machen muss — Akzeptanzkriterien als Code statt Prosa, der Reviewer prüft Exit-Codes statt Interpretation

---

## 7. Qualitätssicherung und Definition of Done

Eine Karte ist Done, wenn **alle** Prüfungen grün sind — das LLM-Urteil des Reviewers ist nur eine Stimme von mehreren. Die Prüfungen definiert das Skeleton als `make check` (nicht der Reviewer-Prompt, damit nichts „vergessen" werden kann):

- Web: pytest, HTTP-Smoke-Test (App starten, Routen abklopfen), HTML-Validierung
- Device-Tool: pytest, ruff, mypy, Integrationstests gegen den Modbus-Simulator

**Sandbox:** `make check` führt LLM-geschriebenen Code aus und läuft deshalb im Container: `docker run --rm --network none --memory 8g --cpus 4 -v <repo>:/work` über `Dockerfile.check`. Kein Netz, kein Home-Verzeichnis, harte Ressourcengrenzen. Aider selbst (nur Datei-Edits) bleibt nativ — die Trennlinie verläuft zwischen Schreiben (harmlos) und Ausführen (nicht harmlos). Der Simulator-Test kommt mit Container-internem Netz aus.

Als Ausbaustufe geparkt: visuelle Prüfung per Playwright-Screenshot + VLM-Bewertung.

---

## 8. Git-Strategie und Windows-Build

**Branch pro Karte** (`karte/07-geraeteliste`): Coder und Reviewer arbeiten dort. Grün → **Squash-Merge** nach `main`, eine Karte = ein Commit mit Karten-ID in der Message (`[K07] Geräteliste-View`) — lesbares Projektprotokoll, chirurgische Reverts. Rot nach 3 Runden → Branch bleibt als Beweisstück, Karte nach *Blockiert*. Abbruch/Timeout → Branch verwerfen, Karte zurück auf *Bereit*, Zähler +1. **`main` ist per Definition immer grün** — Voraussetzung für `copier update` und jede Change-Karte.

Repos liegen auf GitHub, Arbeitskopien unter `~/projekte/<name>` auf dem Strix Halo.

**Windows-.exe:** PyInstaller/nicegui-pack kann nicht cross-kompilieren, die Pipeline läuft aber auf Fedora. Lösung: **GitHub Actions mit `windows-latest`-Runner** — Push auf einen Release-Tag baut die .exe als Release-Artefakt; die Actions-YAML ist Teil des Skeletons. Der Build läuft nur bei Release-Tags, nicht pro Karte; die tägliche Wahrheit bleibt `make check` unter Linux. Der Reviewer kann den Build-Status per API abfragen — der grüne Build ist Teil der Done-Definition der letzten Karte. Falls künftig vertrauliche Projekte dazukommen: Windows-Build-VM im Proxmox als Nachrüstoption — aber nicht als Default.

---

## 9. Deployment (Web)

Deployment ist die vom Architekten standardmäßig eingeplante **letzte Karte**, nicht Handarbeit: `deploy.sh` deployt den Stack per Portainer-API (192.168.178.56; Mechanik liegt im Portainer-Admin-Skill dokumentiert), der Reviewer prüft danach den Healthcheck über die echte URL. Sicherheitsleitplanken: **scoped Portainer-Token nur für Stack-Operationen**, eingebunden per Dateipfad (nie Klartext im Repo). Caddy-Eintrag in v1 halbautomatisch: das Skript generiert den Snippet, das Reload erfolgt nur nach menschlicher Bestätigung — DNS/Proxy ist der eine Punkt, an dem ein Agentenfehler andere Dienste zerlegen könnte. Kein Continuous Deployment pro Karte.

---

## 10. Modell-Zuordnung

| Rolle | Modell | Begründung |
|---|---|---|
| Architekt | Cloud-Frontier (via Hermes) | Läuft einmal pro Projekt, größter Qualitätshebel, Output wird ohnehin im Gate reviewt |
| Coder | qwen3-coder (lokal, Ollama) | Läuft oft; zementiertes Skeleton + präzise Karten sind genau die Bedingungen, unter denen lokale Modelle gut sind |
| Reviewer | lokales Zweitmodell (qwen3.6 / gpt-oss / ornith, Wahl per Bug-Diff-Test) | Muss architektonisch verschieden vom Coder sein, sonst nickt derselbe Bias die eigenen Fehler ab |
| Eskalation | optional Cloud-Retry | Manuell wählbar bei blockierten Karten, vor eigenem Eingreifen |

---

## 11. Bauplan (Reihenfolge verbindlich)

Vertikaler Durchstich statt Infrastruktur-Vollausbau — erst wenn ein Projekt end-to-end durchgelaufen ist, kommt die zweite Domäne:

1. **Web-Skeleton** als Copier-Template bauen (Handarbeit, inkl. Komponentenkatalog und `Dockerfile.check`)
2. **Worker-Minimalversion:** Poll → Aider-Lauf → Spalte umhängen, ohne Eskalations-Komfort
3. **Architekten-Prompt + `projekt.yaml`-Schema + Kartenformat**
4. **Pilotprojekt end-to-end:** Homelab-Statusseite (HTTP-Healthchecks für Portainer, n8n, Ollama, Grafana als Kachel-Dashboard) — klein, nützlich, ≤10 Karten, verschmerzbar als Crashtest, und nah genug an vertrautem Terrain, um Agentenfehler sofort zu erkennen
5. **Nachschärfen** anhand der Pilot-Erfahrungen
6. **Device-Tool-Skeleton:** Geräteprofil-Schema (Handarbeit!), Simulator, NiceGUI-Komponenten, Actions-Build
7. Zweites Pilotprojekt in der Device-Domäne

---

## 12. Offene Punkte / bewusst Vertagtes

- Reviewer-Zweitmodell: finale Wahl empirisch (Bug-Diff-Test); „ornith" bei Umsetzung prüfen
- Playwright + VLM-Sichtprüfung: Ausbaustufe nach stabilem Betrieb
- Automatische Bug-Intake aus laufenden Diensten (Healthcheck rot → Karte): Ausbaustufe, Zutaten liegen dann bereit
- Geräte-Selbstbeschreibung per Firmware-Konvention (Profil-Version-Register): notiert
- Qdrant-Wiederanschluss für projektübergreifende Suche: erst ab ~10 Projekten prüfen
- Parallelität (mehrere Coder gleichzeitig): explizit nicht in v1
