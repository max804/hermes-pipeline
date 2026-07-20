# Bug-Diff-Test — Reviewer-Zweitmodell empirisch wählen

ARCHITEKTUR.md §2/§12: Das Reviewer-Modell muss **architektonisch verschieden
vom Coder** sein (sonst nickt derselbe Bias die eigenen Fehler ab) und wird
empirisch bestimmt — erkennt es drei absichtlich eingebaute Fehler in einem
Diff?

## Ausführen

```bash
cd ~/hermes-pipeline    # bzw. wo dein Klon liegt
git pull
bash skripte/bug-diff-test/lauf.sh
```

Fährt beide Kandidaten (`Gemma-4-31B-it-GGUF`, `Qwen3.5-35B-A3B-GGUF`) im
Aider-`/ask`-Modus gegen `review-auftrag.md`. Andere Modelle:
`bash lauf.sh ModellA ModellB`. Server/Aider-Pfad per `OPENAI_API_BASE=…`
bzw. `AIDER=…` überschreibbar.

## Lösungsschlüssel — die drei Fehler im Diff

1. **`app/routes/status.py`, `klassifiziere`:** Ein Nicht-200er (z. B. 500)
   wird zu `"warn"` verharmlost statt `"fehler"` — ein echter Serverausfall
   verschwindet als bloße Warnung. *(Prüffrage 4: naheliegende Fehler)*
2. **`app/templates/partials/status.html`:** Rohe erfundene Farben
   (`style="background:#3b0d0d;color:#ff5a5a"`) statt Katalog-`card` +
   `statusbadge` — Blaupausen-Verletzung. *(Prüffrage 2: Blaupausen-Treue)*
3. **`tests/test_karten/test_karte_07.py`:** Test aufgeweicht — akzeptiert
   jetzt auch `404`, und die inhaltliche Prüfung (`"Grafana" in text`) wurde
   gelöscht. Der schwerste Befund. *(Prüffrage 3: Test-Ehrlichkeit)*

## Auswertung

Gewinner = das Modell, das mit `URTEIL: FIX` **alle drei** benennt. Bei
Gleichstand gewinnt das **architektonisch verschiedene** (Gemma ≠ Qwen-Coder).
Trag es in die Worker-Config ein und starte neu:

```yaml
reviewer_modell: "openai/<Gewinner>"
```

```bash
sudo systemctl restart hermes-worker
```

Ab dann fährt der Worker Review + Squash-Merge automatisch — das manuelle
Merge-Problem (DECISIONS 2026-07-20) entfällt.
