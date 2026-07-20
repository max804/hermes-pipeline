# DECISIONS.md — Append-only-Log

Git ist das Gedächtnis der Pipeline (`ARCHITEKTUR.md` §4). Hier landen,
nur angehängt, nie umgeschrieben:

- Reviewer-Fails und ihre Ursache
- Fix-Begründungen
- Korrekturen am Freigabe-Gate
- Reibungspunkte aus Pilotläufen (Session 5)

Format pro Eintrag:

```
## JJJJ-MM-TT · [Kontext: Karte/Projekt/Session]
Was ist passiert · Entscheidung · Begründung
```

---

## 2026-07-15 · [Aufbau: Materialisierung]

ARCHITEKTUR.md §3.4 sieht „ARCHITEKTUR.md und rote Test-Stubs per einmaligem
Aider-Lauf" vor. Umgesetzt ist beides **deterministisch ohne LLM**: Die
Stub-Inhalte stehen laut §6 bereits wörtlich in der projekt.yaml, und
ARCHITEKTUR.md lässt sich vollständig aus ihr rendern. Begründung: §3.4
verlangt selbst „erzeugt der Worker deterministisch" — der Aider-Lauf wäre
eine unnötige Fehlerquelle. Weniger Teile, gleiche Wirkung.

## 2026-07-20 · [Pilot: K01 blockiert — Architekten-Stub war in sich widersprüchlich]

Erster echter Blocker des Piloten, Ursache beim Architekten, nicht beim
Coder: Der Test-Stub von K01 rief `pruefe_dienst` synchron auf, während
die Akzeptanzkriterien Nebenläufigkeit per `asyncio.gather` verlangten —
der Coder baute folgerichtig `async def`, und der Stub erhielt eine
Coroutine (`'coroutine' object has no attribute 'status'`). Der Coder
durfte den Stub laut AGENTS.md nicht anfassen: drei ehrliche Runden, dann
Blockiert + Ping. Das System verhielt sich exakt wie entworfen (inklusive
Sequenz-Wächter, der K02/K03 zurückhielt). Behebung als Gate-Korrektur:
Stub auf dem Kartenbranch auf `asyncio.run(pruefe_dienst(...))`
korrigiert, Karte zurück nach Bereit. Lehre in den Architekten-Skill
übernommen: Stubs müssen ihr Interface konsistent behandeln — wer
async-Verhalten in der Akzeptanz fordert, ruft im Stub JEDE potenziell
asynchrone Funktion über `asyncio.run` auf (oder legt sync explizit fest).

## 2026-07-17 · [Pilot-Reibung: Materialisierung strandete in "In Arbeit"]

Erste echte Materialisierung im Pilot blieb in *In Arbeit* hängen, keine
Coder-Karten. Ursache: Der `hermes-worker`-User hat keine globale
Git-Config; der `git commit` bei der Skeleton-Instanziierung scheiterte an
fehlender Author-Identität. Der Fehler (CalledProcessError) war keiner der
in `_materialisiere` gefangenen Typen und landete im Tick-Bare-Except — die
Karte blieb in *In Arbeit* stehen. Zwei Fixes: (1) `_instanziiere` setzt
`user.name`/`user.email` LOKAL im Projekt-Repo (aus `git_user_name`/
`git_user_email` der Config) — davon erben auch Aiders Commits, robust ohne
globale Git-Config; (2) `_materialisiere` fängt jetzt jede Ausnahme und
schiebt nach *Blockiert* statt zu stranden. Lehre: Setup-Annahmen (globale
Git-Config) gehören nicht in den Betrieb — der Worker macht sich unabhängig.

## 2026-07-16 · [Betrieb: Lemonade-Server statt Ollama]

Der lokale LLM-Server auf dem Strix Halo (192.168.178.27) ist Lemonade
(OpenAI-kompatible API, Port 13305) statt Ollama. Aider spricht ihn über
`OPENAI_API_BASE`/`OPENAI_API_KEY` (Dummy-Schlüssel) an; der Worker setzt
beides aus der Config (`openai_api_base`/`openai_api_key`), Zusatz-Flags
über `aider_extra_args` (verifiziert: `--no-show-model-warnings
--map-tokens 1024 --timeout 900`). Coder-Modell:
`openai/Qwen3-Coder-Next-GGUF`. Ollama-Unterstützung bleibt als Alternative
in der Config erhalten. Handtest (Schritt 4) am 16.07.2026 bestanden.

## 2026-07-15 · [Aufbau: Reviewer-Lauf — Fix-Rückläufer als Kartenrückgabe]

§2 gibt dem Reviewer das Recht, „ausschließlich Fix-Rückläuferkarten zu
erzeugen". Umgesetzt als Rückgabe DERSELBEN Karte nach *Bereit* (Befunde als
Kommentar + Kontext für den nächsten Aider-Lauf) statt als neue Board-Karte:
Eine Duplikat-Karte hätte die Eindeutigkeit Karte ↔ Branch ↔ Stub ↔
Versuchszähler gebrochen. Der geteilte 3-Versuche-Zähler deckt Check- und
Review-Fehlschläge gemeinsam ab. Zusätzlich übernimmt der Worker nach
Review-OK den Squash-Merge (§8) selbst — Done ohne Merge hätte main nie
weiterbewegt — und ein Sequenz-Wächter verhindert, dass eine neue Karte
startet, solange ein Vorgänger desselben Projekts in Review/In Arbeit/
Blockiert hängt (sie würde auf einem main ohne dessen Code aufbauen).
Reviewer-Aktivierung erst nach dem Bug-Diff-Test: `reviewer_modell` leer =
Review bleibt beim Menschen.

## 2026-07-15 · [Aufbau: Eigenes Board statt bestehendes Hermes-Kanban]

Entscheidung des Betreibers: Das Board wird nicht das bestehende
Hermes-Kanban, sondern ein eigener Pipeline-Baustein (`board/`,
FastAPI + SQLite + HTMX, Port 9119 bleibt). Gewinn: Die zuvor nur
angenommenen API-Endpunkte des Workers sind jetzt ein von uns
kontrollierter, beidseitig getesteter Vertrag (Integrationstest fährt den
echten Worker-Client per HTTP gegen das echte Board) — der größte
Verifikationspunkt vor dem Piloten entfällt. Dashboard und Steuerung
(Intake-Formulare mit Vorlagen, Freigabe per Drag & Drop, Kommentare der
Agenten) laufen im Browser. ARCHITEKTUR.md §3 wurde aktualisiert.

## 2026-07-15 · [Aufbau: Test-Stub-Staging]

Alle Stubs sofort scharf zu materialisieren hätte einen Widerspruch erzeugt:
`make check` der Karte K01 wäre an den roten Stubs von K02…Kn gescheitert —
keine Karte könnte je grün werden, und „main ist per Definition immer grün"
(§8) wäre ab Materialisierung verletzt. Entscheidung: Stubs liegen als
`tests/test_karten/test_karte_<nr>.py.wartend` im Repo; der Worker schaltet
den Stub einer Karte beim Start ihres Laufs scharf (`git mv` + Commit
`[K##] Test-Stub aktiviert` auf dem Kartenbranch). Damit erreicht jeder
grüne Stub main erst zusammen mit dem Code, der ihn grün macht.

---
