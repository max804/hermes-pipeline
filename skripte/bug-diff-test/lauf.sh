#!/usr/bin/env bash
# Bug-Diff-Test (ARCHITEKTUR.md §2/§12): fährt beide Reviewer-Kandidaten im
# Aider-/ask-Modus gegen denselben Diff mit drei absichtlichen Fehlern und
# zeigt ihre Urteile untereinander. Gewinner = wer alle drei findet
# (Lösungsschlüssel in README.md dieses Verzeichnisses).
#
# Aufruf (als der User, der Aider installiert hat):
#   bash skripte/bug-diff-test/lauf.sh
# Modelle/Server per Umgebung überschreibbar:
#   AIDER=/pfad/zu/aider OPENAI_API_BASE=... bash lauf.sh Modell1 Modell2
set -uo pipefail

HIER="$(cd "$(dirname "$0")" && pwd)"
: "${OPENAI_API_BASE:=http://192.168.178.27:13305/api/v1}"
: "${OPENAI_API_KEY:=lemonade}"
: "${AIDER:=$HOME/aider-venv/bin/aider}"
export OPENAI_API_BASE OPENAI_API_KEY

if [[ $# -gt 0 ]]; then
    KANDIDATEN=("$@")
else
    KANDIDATEN=("Gemma-4-31B-it-GGUF" "Qwen3.5-35B-A3B-GGUF")
fi

if [[ ! -x "$AIDER" ]]; then
    echo "Aider nicht gefunden unter $AIDER — Pfad per AIDER=... setzen." >&2
    exit 2
fi

for M in "${KANDIDATEN[@]}"; do
    echo
    echo "########################################################"
    echo "## KANDIDAT: $M"
    echo "########################################################"
    "$AIDER" --chat-mode ask --model "openai/$M" \
        --no-show-model-warnings --map-tokens 1024 --timeout 900 \
        --message-file "$HIER/review-auftrag.md" --yes-always 2>&1 | tail -55
done

echo
echo "Fertig. Lösungsschlüssel: $HIER/README.md"
