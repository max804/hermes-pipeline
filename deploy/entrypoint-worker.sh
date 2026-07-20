#!/usr/bin/env bash
# Rendert die Worker-Config aus Umgebungsvariablen (aus der .env) und startet
# den Poll-Worker. So genügt zum Loslegen das Ausfüllen der .env — keine
# YAML-Handarbeit. Fortgeschrittene können stattdessen eine eigene
# config.yaml nach /opt/hermes/config.yaml mounten (dann wird diese genutzt).
set -euo pipefail

STAND="${HERMES_STATE:-/opt/hermes}"
CONFIG="$STAND/config.yaml"
PROJEKTE="${HERMES_PROJEKTE:-$STAND/projekte}"
mkdir -p "$PROJEKTE"

if [[ -f "$CONFIG" && "${HERMES_CONFIG_BEHALTEN:-}" == "1" ]]; then
    echo "entrypoint: bestehende $CONFIG wird genutzt (HERMES_CONFIG_BEHALTEN=1)."
else
    {
        echo "board_url: \"${HERMES_BOARD_URL:-http://board:9119}\""
        echo "projekte_verzeichnis: \"$PROJEKTE\""
        echo "datenbank: \"$STAND/worker.db\""
        echo "aider_bin: \"aider\""
        echo "openai_api_base: \"${HERMES_OPENAI_API_BASE:-}\""
        echo "openai_api_key: \"${HERMES_OPENAI_API_KEY:-}\""
        echo "ollama_api_base: \"${HERMES_OLLAMA_API_BASE:-}\""
        echo "coder_modell: \"${HERMES_CODER_MODELL:-openai/Qwen3-Coder-Next-GGUF}\""
        echo "reviewer_modell: \"${HERMES_REVIEWER_MODELL:-}\""
        echo "poll_intervall_s: ${HERMES_POLL_S:-30}"
        echo "aider_extra_args: [\"--no-show-model-warnings\", \"--map-tokens\", \"1024\", \"--timeout\", \"900\"]"
        echo "template_quellen:"
        echo "  web: \"${HERMES_TEMPLATE_WEB:-gh:max804/skeleton-web}\""
        if [[ -n "${HERMES_TELEGRAM_TOKEN:-}" ]]; then
            printf '%s' "$HERMES_TELEGRAM_TOKEN" > "$STAND/telegram-token"
            echo "telegram:"
            echo "  token_datei: \"$STAND/telegram-token\""
            echo "  chat_id: \"${HERMES_TELEGRAM_CHAT:-}\""
        else
            echo "telegram: {}"
        fi
    } > "$CONFIG"
    echo "entrypoint: $CONFIG geschrieben."
fi

export HERMES_WORKER_CONFIG="$CONFIG"
exec hermes-worker
