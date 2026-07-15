"""Der Reviewer-Lauf (ARCHITEKTUR.md §2): Aider-`/ask` mit dem lokalen
Zweitmodell, das architektonisch verschieden vom Coder sein muss.

Sein Urteil ist eine Stimme — die harte Wahrheit hat `make check` schon vor
der Review-Spalte geliefert. Er prüft, was Tests nicht sehen (Vertragstreue,
Blaupausen-Treue, Test-Ehrlichkeit) und darf ausschließlich Fix-Rückläufer
erzeugen. Prompt-Quelle: prompts/reviewer-prompt.md im Meta-Repo — bei
Änderungen dort die Konstante hier nachziehen.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from hermes_worker.config import WorkerKonfig

_DIFF_GRENZE = 30_000

PROMPT = """Du bist der Reviewer der Hermes-Pipeline. `make check` ist bereits grün —
du prüfst, was Tests nicht sehen. Beantworte NUR auf Basis von Karte und Diff.

Prüffragen, in dieser Reihenfolge:
1. Vertragstreue: Setzt der Diff genau das Kartenziel um — nicht weniger,
   nicht mehr? Änderungen außerhalb der Dateiliste der Karte sind ein Befund.
2. Blaupausen-Treue: nur Katalog-Komponenten, keine erfundenen Farben, keine
   neuen Bibliotheken, keine umgangenen Konventionen aus AGENTS.md.
3. Test-Ehrlichkeit: Wurden Tests abgeschwächt, geskippt, gelöscht oder
   umgedeutet? Das ist der schwerste Befund.
4. Naheliegende Fehler: Randfälle, vertauschte Parameter, tote Pfade —
   konkret mit Datei und Fundstelle.

Antworte mit GENAU einer der beiden Formen (letzte Zeile deiner Antwort
beginnt mit URTEIL:):

URTEIL: OK — ein Satz Begründung.

oder

URTEIL: FIX
1. <Datei, Fundstelle>: <was falsch ist> — <was stattdessen>
2. …

## Karte

{kartentext}

## Diff (main...{branch})

```diff
{diff}
```
"""


@dataclass(frozen=True)
class ReviewErgebnis:
    urteil: Literal["ok", "fix", "unklar"]
    befunde: str
    ausgabe_ende: str


def _diff(repo: Path, branch: str) -> str:
    lauf = subprocess.run(
        ["git", "-C", str(repo), "diff", f"main...{branch}"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    diff = lauf.stdout
    if len(diff) > _DIFF_GRENZE:
        diff = diff[:_DIFF_GRENZE] + "\n… (Diff gekürzt)"
    return diff


def parse_urteil(ausgabe: str) -> ReviewErgebnis:
    treffer = list(re.finditer(r"^\s*URTEIL:\s*(OK|FIX)\b(.*)$", ausgabe, re.MULTILINE | re.IGNORECASE))
    if not treffer:
        return ReviewErgebnis("unklar", "", ausgabe[-2000:])
    letzter = treffer[-1]
    if letzter.group(1).upper() == "OK":
        return ReviewErgebnis("ok", "", ausgabe[-2000:])
    befunde = ausgabe[letzter.start():].strip()
    return ReviewErgebnis("fix", befunde[:4000], ausgabe[-2000:])


def fuehre_review_aus(
    konfig: WorkerKonfig, repo: Path, branch: str, kartentext: str
) -> ReviewErgebnis:
    prompt = PROMPT.format(kartentext=kartentext, branch=branch, diff=_diff(repo, branch))
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", prefix="hermes-review-", delete=False
    ) as f:
        f.write(prompt)
        promptdatei = f.name

    kommando = [
        konfig.aider_bin,
        "--chat-mode", "ask",
        "--yes-always",
        "--model", konfig.reviewer_modell,
        "--message-file", promptdatei,
        "--read", "ARCHITEKTUR.md",
        "--read", "AGENTS.md",
    ]
    try:
        lauf = subprocess.run(
            kommando,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=konfig.aider_timeout_s,
        )
    except subprocess.TimeoutExpired:
        return ReviewErgebnis("unklar", "", "Review-Timeout")
    finally:
        Path(promptdatei).unlink(missing_ok=True)

    if lauf.returncode != 0:
        return ReviewErgebnis("unklar", "", (lauf.stdout + "\n" + lauf.stderr)[-2000:])
    return parse_urteil(lauf.stdout)
