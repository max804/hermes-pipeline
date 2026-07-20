"""Board-App: JSON-API (Vertrag des Workers) + HTMX-Dashboard.

API — exakt die Pfade, die worker/hermes_worker/board.py spricht:
    GET  /api/karten?spalte=<name>
    POST /api/karten                     {titel, beschreibung, spalte} → {id}
    POST /api/karten/<id>/verschieben    {spalte}
    POST /api/karten/<id>/kommentare     {text}
    GET  /api/spalten
    POST /api/spalten                    {name}

Konfiguration über ENV:
    HERMES_BOARD_DB           (Standard: ~/hermes-board.db)
    HERMES_INTAKE_VORLAGEN    (Standard: ../intake-vorlagen relativ zum Repo)
"""

from __future__ import annotations

import os
from pathlib import Path

import markdown as markdown_lib
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from hermes_board.speicher import KarteNichtGefunden, SpalteNichtGefunden, Speicher

_HIER = Path(__file__).parent


def _vorlagen_verzeichnis() -> Path:
    umgebung = os.environ.get("HERMES_INTAKE_VORLAGEN")
    if umgebung:
        return Path(umgebung).expanduser()
    return _HIER.parent.parent.parent / "intake-vorlagen"


def _markdown(text: str) -> str:
    return markdown_lib.markdown(text, extensions=["fenced_code", "tables", "sane_lists"])


class NeueKarte(BaseModel):
    titel: str = Field(min_length=1, max_length=200)
    beschreibung: str = ""
    spalte: str


class Verschieben(BaseModel):
    spalte: str


class NeuerKommentar(BaseModel):
    text: str = Field(min_length=1)


class NeueSpalte(BaseModel):
    name: str = Field(min_length=1, max_length=50)


def erzeuge_app(datenbank: Path | str | None = None) -> FastAPI:
    pfad = datenbank or os.environ.get("HERMES_BOARD_DB", "~/hermes-board.db")
    speicher = Speicher(Path(str(pfad)).expanduser())

    app = FastAPI(title="Hermes Board")
    app.state.speicher = speicher
    app.mount("/static", StaticFiles(directory=_HIER / "static"), name="static")
    templates = Jinja2Templates(directory=_HIER / "templates")
    templates.env.filters["markdown"] = _markdown

    # --- JSON-API (Worker-Vertrag) -------------------------------------------

    @app.get("/api/spalten")
    def api_spalten() -> list[dict]:
        return [{"name": n} for n in speicher.spalten()]

    @app.post("/api/spalten", status_code=201)
    def api_spalte_anlegen(spalte: NeueSpalte) -> dict:
        speicher.spalte_anlegen(spalte.name)
        return {"name": spalte.name}

    @app.get("/api/karten")
    def api_karten(spalte: str | None = None) -> list[dict]:
        return [
            {"id": k.id, "titel": k.titel, "beschreibung": k.beschreibung, "spalte": k.spalte}
            for k in speicher.karten(spalte)
        ]

    @app.post("/api/karten", status_code=201)
    def api_karte_anlegen(karte: NeueKarte) -> dict:
        try:
            karten_id = speicher.karte_anlegen(karte.titel, karte.beschreibung, karte.spalte)
        except SpalteNichtGefunden as e:
            raise HTTPException(404, f"Spalte unbekannt: {e}") from e
        return {"id": karten_id}

    @app.post("/api/karten/{karten_id}/verschieben")
    def api_verschieben(karten_id: int, ziel: Verschieben) -> dict:
        try:
            speicher.verschiebe(karten_id, ziel.spalte)
        except KarteNichtGefunden as e:
            raise HTTPException(404, f"Karte unbekannt: {e}") from e
        except SpalteNichtGefunden as e:
            raise HTTPException(404, f"Spalte unbekannt: {e}") from e
        return {"id": karten_id, "spalte": ziel.spalte}

    @app.post("/api/karten/{karten_id}/kommentare", status_code=201)
    def api_kommentieren(karten_id: int, kommentar: NeuerKommentar) -> dict:
        try:
            kommentar_id = speicher.kommentiere(karten_id, kommentar.text)
        except KarteNichtGefunden as e:
            raise HTTPException(404, f"Karte unbekannt: {e}") from e
        return {"id": kommentar_id}

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "karten": len(speicher.karten())}

    # --- Dashboard-UI ---------------------------------------------------------

    def _board_kontext(request: Request) -> dict:
        spalten = speicher.spalten()
        return {
            "spalten": [(name, speicher.karten(name)) for name in spalten],
            "spalten_namen": spalten,
        }

    @app.get("/", response_class=HTMLResponse)
    def board(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "board.html", _board_kontext(request))

    @app.get("/partials/board", response_class=HTMLResponse)
    def board_partial(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "partials/board.html", _board_kontext(request))

    @app.get("/karten/{karten_id}", response_class=HTMLResponse)
    def karte_detail(request: Request, karten_id: int) -> HTMLResponse:
        try:
            karte = speicher.karte(karten_id)
        except KarteNichtGefunden as e:
            raise HTTPException(404, "Karte unbekannt") from e
        return templates.TemplateResponse(
            request,
            "karte.html",
            {
                "karte": karte,
                "kommentare": speicher.kommentare(karten_id),
                "spalten_namen": speicher.spalten(),
            },
        )

    @app.get("/neu", response_class=HTMLResponse)
    def karte_neu_formular(request: Request, vorlage: str = "") -> HTMLResponse:
        vorbelegung = ""
        datei = {
            "neu": "intake-neuprojekt.md",
            "aenderung": "intake-aenderung.md",
        }.get(vorlage)
        if datei:
            pfad = _vorlagen_verzeichnis() / datei
            if pfad.is_file():
                vorbelegung = pfad.read_text()
        return templates.TemplateResponse(
            request,
            "neu.html",
            {
                "vorbelegung": vorbelegung,
                "vorlage": vorlage,
                "spalten_namen": speicher.spalten(),
            },
        )

    @app.post("/neu")
    def karte_neu(
        titel: str = Form(...), beschreibung: str = Form(""), spalte: str = Form("Eingang")
    ) -> RedirectResponse:
        karten_id = speicher.karte_anlegen(titel, beschreibung, spalte)
        return RedirectResponse(f"/karten/{karten_id}", status_code=303)

    @app.post("/karten/{karten_id}/verschieben")
    def ui_verschieben(karten_id: int, spalte: str = Form(...)) -> RedirectResponse:
        speicher.verschiebe(karten_id, spalte)
        return RedirectResponse(f"/karten/{karten_id}", status_code=303)

    @app.post("/karten/{karten_id}/kommentare")
    def ui_kommentieren(karten_id: int, text: str = Form(...)) -> RedirectResponse:
        speicher.kommentiere(karten_id, text)
        return RedirectResponse(f"/karten/{karten_id}", status_code=303)

    @app.post("/karten/{karten_id}/bearbeiten")
    def ui_bearbeiten(
        karten_id: int, titel: str = Form(...), beschreibung: str = Form("")
    ) -> RedirectResponse:
        speicher.beschreibung_setzen(karten_id, titel, beschreibung)
        return RedirectResponse(f"/karten/{karten_id}", status_code=303)

    return app
