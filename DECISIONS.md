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
