# Ein Image, zwei Rollen (hermes-board / hermes-worker). Der Worker startet
# `make check` über den gemounteten Host-Docker-Socket (Docker-out-of-Docker),
# deshalb enthält das Image die Docker-CLI, git, make und aider.
#
# Build aus dem Repo-Wurzelverzeichnis:
#   docker build -f deploy/Dockerfile -t hermes-pipeline:latest .
#
# Architektur: x86_64. Für arm64 die DOCKER_CLI_URL unten anpassen.
FROM python:3.12-slim

ARG DOCKER_CLI_URL=https://download.docker.com/linux/static/stable/x86_64/docker-27.3.1.tgz

RUN apt-get update \
 && apt-get install -y --no-install-recommends git make curl ca-certificates \
 && curl -fsSL "$DOCKER_CLI_URL" | tar xz -C /usr/local/bin --strip-components=1 docker/docker \
 && apt-get purge -y curl && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Git-Identität für vom Worker angelegte und gemergte Projekt-Repos
RUN git config --global user.name "Hermes Pipeline" \
 && git config --global user.email "hermes@localhost" \
 && git config --global --add safe.directory '*'

WORKDIR /app
COPY schemas ./schemas
COPY worker ./worker
COPY board ./board
COPY intake-vorlagen ./intake-vorlagen
COPY deploy/entrypoint-worker.sh /entrypoint-worker.sh

RUN pip install --no-cache-dir ./schemas \
 && pip install --no-cache-dir ./worker ./board aider-chat \
 && chmod +x /entrypoint-worker.sh

# Intake-Vorlagen liegen im Image; das Board findet sie hierüber.
ENV HERMES_INTAKE_VORLAGEN=/app/intake-vorlagen \
    HERMES_BOARD_HOST=0.0.0.0 \
    HERMES_BOARD_PORT=9119

EXPOSE 9119
# Standardrolle: Board. Der Worker überschreibt den Entrypoint (siehe compose).
CMD ["hermes-board"]
