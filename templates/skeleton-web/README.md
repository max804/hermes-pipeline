# skeleton-web — Copier-Template der Web-Domäne

Zementiert die Architekturentscheidungen aus `ARCHITEKTUR.md` §5.1 in Code:
FastAPI + Jinja2 + HTMX + Tailwind, Komponentenkatalog, `make check` im
netzlosen Container.

## ⚠️ Abspalten vor dem Pilotprojekt

Dieses Template liegt zum Entwerfen unter `hermes-pipeline/templates/`.
**Vor dem ersten instanziierten Projekt** muss es in ein eigenes Repo
`skeleton-web` mit eigener Tag-Historie (`web-v0.1.0`, …) umziehen —
`copier update` arbeitet über Git-Tags des Template-Repos, und eine mit
Worker-Releases geteilte Tag-Historie wird beim Update alter Projekte
unentwirrbar. Solange kein Projekt auf die Template-URL zeigt, ist der
Umzug ein einfaches `git filter-repo`/Copy — danach nicht mehr.

## Nutzung

```bash
copier copy ./templates/skeleton-web ~/projekte/<name>     # solange Monorepo
copier copy gh:max804/skeleton-web   ~/projekte/<name>     # nach Abspaltung
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
