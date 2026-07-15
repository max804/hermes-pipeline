"""Das Kanban-Board der Hermes-Pipeline.

Dashboard und Steuerung laufen hier (FastAPI + Jinja2 + HTMX, SQLite);
im Hintergrund arbeitet der Poll-Worker mit den Agenten. Die API dieses
Boards IST der Vertrag, den `worker/hermes_worker/board.py` spricht —
ein Integrationstest im Worker hält beide Seiten deckungsgleich.
"""
