"""HTTP-Smoke-Test + HTML-Validierung (ARCHITEKTUR.md §7).

Läuft gegen ALLE registrierten GET-Routen ohne Pfadparameter — neue Seiten
sind damit automatisch abgedeckt, nichts kann „vergessen" werden.
"""

import html5lib
from fastapi.routing import APIRoute

from app.main import app


def _get_routen() -> list[str]:
    return [
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and "GET" in route.methods and "{" not in route.path
    ]


def test_healthz(client):
    antwort = client.get("/healthz")
    assert antwort.status_code == 200
    assert antwort.json() == {"status": "ok"}


def test_alle_get_routen_antworten(client):
    assert _get_routen(), "keine Routen registriert?"
    for pfad in _get_routen():
        assert client.get(pfad).status_code == 200, f"Route {pfad} antwortet nicht mit 200"


def test_html_ist_valide(client):
    parser = html5lib.HTMLParser(strict=True)
    for pfad in _get_routen():
        antwort = client.get(pfad)
        if not antwort.headers["content-type"].startswith("text/html"):
            continue
        parser.parse(antwort.text)  # wirft ParseError bei invalidem HTML5
        assert "{{" not in antwort.text, f"{pfad}: ungerendertes Jinja im Output"
        assert "{%" not in antwort.text, f"{pfad}: ungerendertes Jinja im Output"


def test_statische_artefakte_vorhanden(client):
    for datei in ("/static/theme.css", "/static/htmx.min.js"):
        assert client.get(datei).status_code == 200, f"{datei} fehlt — vendored, kein CDN"
