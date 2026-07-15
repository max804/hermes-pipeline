import pytest
from fastapi.testclient import TestClient

from hermes_board.app import erzeuge_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HERMES_INTAKE_VORLAGEN",
        str(__import__("pathlib").Path(__file__).parents[2] / "intake-vorlagen"),
    )
    return TestClient(erzeuge_app(tmp_path / "board.db"))


def test_board_zeigt_alle_spalten(client):
    seite = client.get("/")
    assert seite.status_code == 200
    for spalte in ("Eingang", "Freigabe", "Blockiert"):
        assert spalte in seite.text


def test_partial_wird_ausgeliefert(client):
    assert client.get("/partials/board").status_code == 200


def test_neue_karte_ueber_formular(client):
    antwort = client.post(
        "/neu",
        data={"titel": "Testkarte", "beschreibung": "# Hallo", "spalte": "Eingang"},
        follow_redirects=False,
    )
    assert antwort.status_code == 303
    detail = client.get(antwort.headers["location"])
    assert "Testkarte" in detail.text
    assert "<h1" in detail.text  # Markdown gerendert


def test_vorlagen_vorbelegung(client):
    seite = client.get("/neu", params={"vorlage": "neu"})
    assert "Intake: Neues Projekt" in seite.text
    seite = client.get("/neu", params={"vorlage": "aenderung"})
    assert "Intake: Änderung" in seite.text


def test_kommentar_und_verschieben_ueber_ui(client):
    ort = client.post(
        "/neu", data={"titel": "K", "beschreibung": "", "spalte": "Eingang"}, follow_redirects=False
    ).headers["location"]
    client.post(f"{ort}/kommentare", data={"text": "Anmerkung"}, follow_redirects=False)
    client.post(f"{ort}/verschieben", data={"spalte": "Done"}, follow_redirects=False)
    detail = client.get(ort).text
    assert "Anmerkung" in detail and "Done" in detail


def test_statische_artefakte(client):
    for datei in ("/static/theme.css", "/static/htmx.min.js", "/static/dragdrop.js"):
        assert client.get(datei).status_code == 200
