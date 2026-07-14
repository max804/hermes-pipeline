"""Poll-Worker der Hermes-Pipeline (ARCHITEKTUR.md §4).

Ein einzelner Daemon: pollt alle 30 Sekunden die Board-API, validiert
Eingang-Karten, arbeitet *Bereit*-Karten sequenziell per Aider ab und
prüft das Ergebnis mit ``make check`` im netzlosen Container. Kein
Event-Push, keine Queue — langweilig und debugbar.
"""
