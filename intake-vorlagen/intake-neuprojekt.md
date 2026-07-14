# Intake: Neues Projekt

<!--
Diese Karte kommt in die Spalte **Eingang**. Der Worker validiert die
Pflichtfelder und weist unvollständige Karten mit Kommentar zurück.
Alle mit (Pflicht) markierten Abschnitte müssen ausgefüllt sein.
-->

## Domäne (Pflicht)

<!-- Genau eine ankreuzen. Andere Domänen nimmt die Pipeline nicht an. -->

- [ ] `web` — statische Seite bis Web-App (FastAPI + Jinja2 + HTMX + Tailwind)
- [ ] `device-tool` — Windows-Desktop-Tool für Mikrocontroller über Modbus TCP

## Projektname (Pflicht)

<!-- kurz, kleinbuchstaben-mit-bindestrich; wird Repo- und Verzeichnisname -->

## Ziel (Pflicht, 3–5 Sätze)

<!-- Was soll entstehen, für wen, was macht es besser als der Ist-Zustand? -->

## Muss-Funktionen (Pflicht)

<!-- Aufzählung. Was ohne Diskussion drin sein muss. -->

-
-

## Explizit nicht (Pflicht)

<!-- Was bewusst NICHT gebaut wird (z. B. „kein Auth in v1").
     Der Architekt übernimmt das in die projekt.yaml als Ausgeschlossenes. -->

-

## Nur bei Domäne `web`: Seiten-/Routenliste (Pflicht)

<!-- Jede Seite/Route eine Zeile: Pfad — Zweck -->

| Route | Zweck |
|---|---|
| `/` | |

## Nur bei Domäne `device-tool`: Rohe Registermap (Pflicht)

<!-- Roh einfügen (Hersteller-Doku, Tabelle, Auszug) — der Architekt
     formalisiert sie ins Geräteprofil-YAML. Byte-/Word-Order bei float32
     angeben, falls bekannt! -->

```
```

## Freitext (optional)

<!-- Referenzen, Beispiele, Vorlieben, bekannte Stolpersteine -->
