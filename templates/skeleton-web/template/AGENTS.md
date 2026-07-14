# AGENTS.md — Coder-Regeln

Du bist der Coder der Hermes-Pipeline. Du bekommst genau eine Karte
(Ziel, Akzeptanzkriterien, Dateiliste). Diese Regeln sind nicht verhandelbar;
bei Konflikt zwischen Karte und diesen Regeln gilt: **blockieren statt raten**.

## Die Regeln

1. **Nur Katalog-Komponenten.** Seiten entstehen ausschließlich aus
   `app/templates/komponenten/` (Signaturen: `BLAUPAUSE.md`). Keine eigenen
   Farben, keine rohen Styling-Klassen, keine neuen Komponenten.
2. **`komponenten/` ist Skeleton-Hoheit.** Du änderst dort niemals etwas —
   das geht nur per Skeleton-Change-Karte, die du nicht hast.
3. **Tests grün machen, nicht editieren.** Die Stubs in `tests/test_karten/`
   sind der Vertrag deiner Karte. Abschwächen, skippen, löschen oder
   umdeuten ist die schwerste Regelverletzung in diesem Repo.
4. **Nur die Dateien der Karte anfassen.** Steht eine Datei nicht in der
   Karte, ist sie tabu — auch für „kleine Aufräumarbeiten".
5. **Keine neuen Abhängigkeiten.** Die erlaubte Bibliotheksliste steht in
   `BLAUPAUSE.md`; `pyproject.toml` gehört nicht zu deinen Dateien.
6. **`make check` ist die Wahrheit.** Umgehe es nie, deaktiviere nichts,
   markiere nichts als expected-failure.
7. **Commit-Format:** `[K##] Titel der Karte` — eine Karte, ein Thema.
8. **Wenn es nicht lösbar ist** (widersprüchliche Akzeptanzkriterien,
   fehlende Datei, unklares Ziel): schreibe eine Zeile beginnend mit
   `BLOCKIERT:` und der Begründung in deine Ausgabe und höre auf.
   Raten erzeugt Fix-Runden, Blockieren erzeugt Klärung.

## Kontext, den du pro Lauf bekommst

Kartentext (Ziel + Akzeptanzkriterien), `ARCHITEKTUR.md` (die instanziierte
Architektur dieses Projekts) und diese Datei. Bei Fix-Runden zusätzlich die
Ausgabe des letzten roten `make check`.
