# skeleton-web — Copier-Template der Web-Domäne

> **⚠️ ABGESPALTEN (16.07.2026): Die Wahrheit ist jetzt das Repo
> `github.com/max804/skeleton-web`** (Tag-Historie `web-v*`). Diese Kopie
> hier dient nur noch den Tests des Meta-Repos. Änderungen am Skeleton
> passieren im Skeleton-Repo (per Skeleton-Change-Karte) und werden bei
> Bedarf hierher zurückgespiegelt, damit die Tests aktuell bleiben.

Zementiert die Architekturentscheidungen aus `ARCHITEKTUR.md` §5.1 in Code:
FastAPI + Jinja2 + HTMX + Tailwind, Komponentenkatalog, `make check` im
netzlosen Container.

## Nutzung

```bash
copier copy --trust gh:max804/skeleton-web ~/projekte/<name>
```

Fragen: `projektname`, `beschreibung`, `port`, `static_only`, `caddy_domain`.

## Vendorte Artefakte

- `app/static/htmx.min.js` — htmx **2.0.4** von der npm-Registry
  (`htmx.org-2.0.4.tgz`), SHA-256
  `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`.
  Kein CDN: die Apps laufen im LAN auch ohne Internet.
- `app/static/theme.css` — kompiliertes Tailwind CSS v4 aus
  `tailwind.input.css` (Standalone-CLI bzw. `@tailwindcss/cli`, **kein Node
  im instanziierten Projekt**). Neu bauen nach Katalog-Änderungen:
  `make css`.

## Abnahmetest (ARCHITEKTUR.md §5.3)

„Kann ich selbst in diesem Skeleton in 30 Minuten von Hand eine Seite
bauen?" — nur aus Katalog-Komponenten, ohne ein einziges frei erfundenes
rohes Styling.
