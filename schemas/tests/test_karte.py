import pytest

from hermes_schemas.karte import (
    KartenFormatFehler,
    KartenMeta,
    baue_kartenbeschreibung,
    lade_kartenmeta,
)

GUELTIG = """---
projekt: homelab-status
karte: K07
dateien: [app/routen/status.py, tests/test_karte_07.py]
---
Ziel: Statusseite rendert Kacheln.

Akzeptanzkriterien:
- pytest tests/test_karte_07.py grün
"""


def test_gueltige_karte_wird_zerlegt():
    meta, text = lade_kartenmeta(GUELTIG)
    assert meta.projekt == "homelab-status"
    assert meta.karte == "K07"
    assert text.startswith("Ziel:")
    assert "---" not in text


def test_fehlendes_front_matter():
    with pytest.raises(KartenFormatFehler, match="Front-Matter"):
        lade_kartenmeta("Nur Text ohne Meta")


def test_leerer_auftragstext():
    kopf = GUELTIG.split("---")[1]
    with pytest.raises(KartenFormatFehler, match="Auftragstext"):
        lade_kartenmeta(f"---{kopf}---\n   \n")


def test_roundtrip_bauen_und_laden():
    meta = KartenMeta(projekt="homelab-status", karte="K01", dateien=["app/main.py"])
    beschreibung = baue_kartenbeschreibung(meta, "Ziel: Hauptmodul anlegen.")
    geladen, text = lade_kartenmeta(beschreibung)
    assert geladen == meta
    assert text == "Ziel: Hauptmodul anlegen."
