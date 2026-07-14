# Entwicklung am Meta-Repo selbst. Die Projekt-Pipelines nutzen das
# `make check` ihres Skeletons — dieses hier prüft Worker und Schemas.

.PHONY: setup check

setup:
	python3 -m venv .venv
	.venv/bin/pip install -q -e "schemas[dev]" -e "worker[dev]"

check:
	.venv/bin/python -m pytest schemas/tests -q
	cd worker && ../.venv/bin/python -m pytest tests -q
