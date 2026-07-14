"""Beispielroute "/" — Muster für alle Seiten-Routen.

Schichtenmodell (BLAUPAUSE.md): Die Route bereitet alle Daten fertig auf,
das Template komponiert nur Katalog-Komponenten. Die Demo-Daten hier werden
im echten Projekt durch die Karten des Architekten ersetzt.
"""

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import escape

from app.config import einstellungen

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    dienste = [
        {"name": "Beispieldienst", "beschreibung": "Antwortet fristgerecht.", "status": "ok"},
        {"name": "Wackelkandidat", "beschreibung": "Antwortzeit erhöht.", "status": "warn"},
        {"name": "Ausgefallen", "beschreibung": "Keine Antwort auf /healthz.", "status": "fehler"},
    ]
    pruefungen = [
        ["Beispieldienst", "ok", "12 ms"],
        ["Wackelkandidat", "warn", "480 ms"],
        ["Ausgefallen", "fehler", "—"],
    ]
    return templates.TemplateResponse(
        request,
        "index.html",
        {"titel": einstellungen.titel, "dienste": dienste, "pruefungen": pruefungen},
    )


@router.post("/partials/echo", response_class=HTMLResponse)
def echo(name: str = Form("")) -> HTMLResponse:
    """Muster für HTMX-Fragmente: kleine Antwort, kein volles Layout.
    Nutzereingaben IMMER escapen — auch in Fragmenten."""
    return HTMLResponse(f'<p class="text-sm text-emerald-400">Empfangen: {escape(name)}</p>')
