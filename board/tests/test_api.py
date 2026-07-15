"""API-Vertragstests — die Pfade und Payloads hier sind exakt die, die
worker/hermes_worker/board.py spricht. Änderungen nur beidseitig."""

import pytest
from fastapi.testclient import TestClient

from hermes_board.app import erzeuge_app
from hermes_board.speicher import STANDARD_SPALTEN


@pytest.fixture
def client(tmp_path):
    return TestClient(erzeuge_app(tmp_path / "board.db"))


def test_standard_spalten_beim_ersten_start(client):
    namen = [s["name"] for s in client.get("/api/spalten").json()]
    assert namen == STANDARD_SPALTEN


def test_spalte_anlegen_ist_idempotent(client):
    assert client.post("/api/spalten", json={"name": "Eingang"}).status_code == 201
    namen = [s["name"] for s in client.get("/api/spalten").json()]
    assert namen.count("Eingang") == 1


def test_karten_lebenszyklus(client):
    antwort = client.post(
        "/api/karten",
        json={"titel": "[K01] Testkarte", "beschreibung": "Ziel: x", "spalte": "Bereit"},
    )
    assert antwort.status_code == 201
    karten_id = antwort.json()["id"]

    karten = client.get("/api/karten", params={"spalte": "Bereit"}).json()
    assert [k["titel"] for k in karten] == ["[K01] Testkarte"]
    assert karten[0]["beschreibung"] == "Ziel: x"

    client.post(f"/api/karten/{karten_id}/verschieben", json={"spalte": "In Arbeit"})
    assert client.get("/api/karten", params={"spalte": "Bereit"}).json() == []
    assert len(client.get("/api/karten", params={"spalte": "In Arbeit"}).json()) == 1

    assert client.post(
        f"/api/karten/{karten_id}/kommentare", json={"text": "make check grün"}
    ).status_code == 201


def test_anlage_reihenfolge_bleibt_erhalten(client):
    for i in range(1, 4):
        client.post("/api/karten", json={"titel": f"[K0{i}] x", "beschreibung": "", "spalte": "Bereit"})
    titel = [k["titel"] for k in client.get("/api/karten", params={"spalte": "Bereit"}).json()]
    assert titel == ["[K01] x", "[K02] x", "[K03] x"]


def test_unbekannte_ziele_geben_404(client):
    assert client.post("/api/karten/999/verschieben", json={"spalte": "Bereit"}).status_code == 404
    assert client.post("/api/karten/999/kommentare", json={"text": "x"}).status_code == 404
    assert client.post(
        "/api/karten", json={"titel": "x", "beschreibung": "", "spalte": "GibtEsNicht"}
    ).status_code == 404


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"
