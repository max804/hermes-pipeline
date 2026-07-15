# skills/ — Skills des Hermes-Ökosystems

## hermes-architekt

Die Architekten-Rolle (einzige kartenerzeugende Rolle, ARCHITEKTUR.md §2).
Selbsttragend: Schema-Referenz und valides Beispiel liegen unter
`hermes-architekt/references/` bei.

**Installation** in das Skill-Verzeichnis der Hermes-Session kopieren, z. B.:

```bash
cp -r skills/hermes-architekt ~/.claude/skills/
```

Damit `hermes-validiere` (Selbstprüfung vor Abgabe) verfügbar ist:

```bash
pip install -e <hermes-pipeline>/schemas
```

**Pflegeregel:** Wahrheitsquelle des Schemas ist
`schemas/hermes_schemas/projekt.py`. Die Beispiel-Kopie in den
Skill-References wird per Test (`schemas/tests/test_cli.py`) gegen das
Original gehalten — bei Schemaänderungen beide nachziehen, sonst wird
`make check` rot.

## Bewusst NICHT hier

Coder und Reviewer bekommen keine Skills — ihr Spezialwissen liegt in den
Skeleton-Repos (`BLAUPAUSE.md` + `AGENTS.md`) und reist per Copier mit
jedem Projekt (ROADMAP.md §3.2). Ein `pipeline-admin`-Skill ist als Komfort
nach stabilem Betrieb notiert.
