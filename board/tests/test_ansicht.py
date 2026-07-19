from datetime import datetime, timezone

from hermes_board import ansicht


def test_chip_aus_kartenpraefix():
    assert ansicht.chip_und_titel(7, "[K01] Healthcheck-Modul") == ("K01", "Healthcheck-Modul")


def test_chip_faellt_auf_id_zurueck():
    assert ansicht.chip_und_titel(7, "Freie Notiz") == ("#7", "Freie Notiz")


def test_akzent_bekannt_und_unbekannt():
    assert ansicht.akzent("Blockiert")[1] == "bg-red-500"
    assert ansicht.akzent("Selbst erfundene Spalte") == ("text-slate-300", "bg-slate-500")


def test_bauplan_tag_erkannt():
    assert ansicht.art_tag("projekt:\n  name: x\nkarten:\n  - id: K01") == "Bauplan"
    assert ansicht.art_tag("nur ein Kommentar") is None


def test_relativzeit():
    jetzt = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)
    assert ansicht.relativzeit("2026-07-19T11:58:00+00:00", jetzt=jetzt) == "vor 2 Min"
    assert ansicht.relativzeit("2026-07-19T09:00:00+00:00", jetzt=jetzt) == "vor 3 Std"
    assert ansicht.relativzeit("2026-07-19T11:59:40+00:00", jetzt=jetzt) == "gerade eben"
    assert ansicht.relativzeit("2026-07-17T12:00:00+00:00", jetzt=jetzt) == "vor 2 Tagen"


def test_baue_ansicht_verbindet_alles():
    class FakeKarte:
        id = 7
        titel = "[K01] Healthcheck-Modul"
        beschreibung = "Ziel: x"
        spalte = "Review"
        aktualisiert = "2026-07-19T11:00:00+00:00"

    jetzt = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)
    a = ansicht.baue_ansicht(FakeKarte(), 3, jetzt=jetzt)
    assert a.chip == "K01"
    assert a.titel == "Healthcheck-Modul"
    assert a.kommentare == 3
    assert a.punkt == "bg-violet-500"
    assert a.zeit == "vor 1 Std"
