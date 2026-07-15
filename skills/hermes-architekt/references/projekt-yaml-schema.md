# projekt.yaml — Feld-für-Feld-Spezifikation

Wahrheitsquelle: `schemas/hermes_schemas/projekt.py` (Pydantic) im Repo
`hermes-pipeline`. Der Worker validiert damit; `hermes-validiere` nutzt
denselben Code. Validierungsfehler kommen gesammelt als EINE Rückrunde.

## Wurzel

```yaml
projekt:      # Kopf
architektur:  # instanziierte Blaupause
karten:       # 1–n Karten (Ziel: ≤ 10)
```

Keine weiteren Wurzel-Schlüssel (`extra="forbid"` überall — Tippfehler
in Feldnamen sind Validierungsfehler, keine stillen No-ops).

## projekt

| Feld | Typ | Regel |
|---|---|---|
| `name` | str | `^[a-z][a-z0-9-]{2,49}$` — wird Repo-/Stack-Name |
| `domaene` | `web` \| `device-tool` | genau diese zwei |
| `beschreibung` | str | ≥ 20 Zeichen, trägt auch deine dokumentierten Annahmen |

## architektur

| Feld | Typ | Regel |
|---|---|---|
| `module` | list[str] | ≥ 1; Muster: `"pfad/datei.py — Ein-Satz-Zweck"` |
| `datenmodell` | str | Prosa/Notation, auch „nur im Speicher" ist eine Aussage |
| `routen` | list[str] | nur `web`; Muster: `"GET /pfad — Zweck"` |
| `geraeteprofile` | list[str] | nur `device-tool`; Profil-Dateinamen |
| `ausgeschlossen` | list[str] | ≥ 1 — Explizit-nicht aus dem Intake, wörtlich |

## karten[]

| Feld | Typ | Regel |
|---|---|---|
| `id` | str | `K01`–`K999`, eindeutig |
| `titel` | str | 3–100 Zeichen |
| `ziel` | str | 10–300 Zeichen, EIN Satz |
| `dateien` | list[str] | ≥ 1; relativ, kein `..`; im Skeleton-Namensraum (unten) |
| `akzeptanz` | list[str] | ≥ 1; maschinenprüfbar formuliert |
| `abhaengig_von` | list[str] | existierende Karten-IDs, zyklenfrei, nicht selbst |
| `test_stub` | str | ≥ 10 Zeichen; roter Test, landet in `tests/test_karten/test_karte_<nr>.py` |

## Skeleton-Namensraum (erlaubte `dateien`-Wurzeln)

| Domäne | Wurzeln |
|---|---|
| `web` | `app/`, `tests/`, `deploy.sh`, `compose.yaml`, `ARCHITEKTUR.md`, `README.md` |
| `device-tool` | `app/`, `tests/`, `device-profiles/`, `.github/workflows/`, `ARCHITEKTUR.md`, `README.md` |

Änderungen am Namensraum sind Skeleton-Änderungen und werden in
`SKELETON_NAMENSRAUM` (`projekt.py`) nachgezogen.

## Häufige Validierungsfehler

- Abhängigkeit auf nicht existierende Karten-ID (Tippfehler `K10` vs `K01`)
- Zyklus über mehrere Karten (A→B→C→A) — Reihenfolge entwerfen, dann IDs
- `dateien` außerhalb des Namensraums (z. B. `src/…` statt `app/…`)
- `test_stub` vergessen — Akzeptanz nur als Prosa reicht nicht
