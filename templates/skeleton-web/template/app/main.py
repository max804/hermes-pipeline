"""FastAPI-App: Router-Registrierung, Static-Mount, /healthz."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import einstellungen
from app.routes import pages

app = FastAPI(title=einstellungen.titel)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(pages.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
