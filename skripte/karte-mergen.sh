#!/usr/bin/env bash
# Squash-merged den Branch einer fertigen Karte nach main und löscht ihn.
#
# Der EINE Handgriff, der beim manuellen Review (Reviewer-Modell aus) den
# Git-Merge an das Verschieben nach *Done* koppelt. Ohne ihn driften Board
# und Git auseinander: die Karte steht auf Done, ihr Code aber nur auf dem
# Branch, und die nächste Karte baut auf einem main ohne sie auf
# (Pilot-Reibung 2026-07-20, siehe DECISIONS.md).
#
# Aufruf im Projekt-Repo:
#   karte-mergen.sh <branch> "[K##] Titel"
# Beispiel:
#   karte-mergen.sh karte/01-k01-healthcheck-modul "[K01] Healthcheck-Modul"
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Aufruf: karte-mergen.sh <branch> \"[K##] Titel\"" >&2
    exit 2
fi
branch="$1"
nachricht="$2"

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Arbeitsbaum nicht sauber — erst committen/verwerfen." >&2
    exit 1
fi

git checkout main
git merge --squash "$branch"
git commit -m "$nachricht"
git branch -D "$branch"
echo "Gemergt nach main: $nachricht (Branch $branch gelöscht)"
