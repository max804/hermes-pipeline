"""FastAPI-App: automatische Router-Registrierung, Static-Mount, /healthz.

Jede Datei in app/routes/ exportiert ein ``router = APIRouter()`` und wird
hier automatisch eingebunden — neue Seiten fassen main.py nie an. Damit
bleibt die Dateiliste einer Karte auf ihre eigene Routen-Datei beschränkt.
"""

import importlib
import pkgutil
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import routes
from app.config import einstellungen

app = FastAPI(title=einstellungen.titel)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

for _modul_info in pkgutil.iter_modules(routes.__path__):
    _modul = importlib.import_module(f"app.routes.{_modul_info.name}")
    _router = getattr(_modul, "router", None)
    if _router is not None:
        app.include_router(_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
