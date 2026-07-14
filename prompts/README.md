# prompts/ — Architekten- und Reviewer-Prompt

**Werden in Session 3–4 gebaut** (siehe `../ROADMAP.md`).

## Architekten-Prompt

Grundlage des Skills `hermes-architekt` (Session 4, geschrieben mit
`skill-creator` + `writing-great-skills`). Muss enthalten:

- das `projekt.yaml`-Schema mit Beispiel
- die Kartenregeln: Pflichtfelder; eine Karte = ein Aider-Lauf;
  **nur der Architekt erzeugt Karten**
- die Ein-Runden-Rückfrageregel (maximal eine gesammelte Rückfragerunde
  per Telegram)
- Verweise auf die Blaupausen beider Domänen (`BLAUPAUSE.md` in
  `skeleton-web` bzw. `skeleton-device-tool`)

## Reviewer-Prompt

Für den Aider-`/ask`-Lauf mit dem lokalen Zweitmodell. Regeln:

- LLM-Urteil ist nur **eine** Stimme; die harte Wahrheit liefert `make check`
- darf ausschließlich Fix-Rückläuferkarten erzeugen
- Modellwahl empirisch per Bug-Diff-Test (erkennt das Modell drei absichtlich
  eingebaute Fehler in einem Diff?) — Kandidaten: qwen3.6, gpt-oss, ornith

## Abgrenzung: Coder bekommt keinen Prompt aus diesem Verzeichnis

Das Coder-Wissen liegt im Skeleton-Repo (`BLAUPAUSE.md` + `AGENTS.md`) und
reist per Copier mit jedem Projekt mit — keine zweite Wissensquelle hier
pflegen (siehe `../ROADMAP.md` §3.2).
