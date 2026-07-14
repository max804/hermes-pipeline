from pathlib import Path

from hermes_schemas.intake import pruefe_intake

VORLAGEN = Path(__file__).parent.parent.parent / "intake-vorlagen"

NEU_WEB_GUELTIG = """# Intake: Neues Projekt

## Domäne (Pflicht)

- [x] `web` — statische Seite bis Web-App
- [ ] `device-tool` — Windows-Desktop-Tool

## Projektname (Pflicht)

homelab-status

## Ziel (Pflicht, 3–5 Sätze)

Ein Kachel-Dashboard für das Homelab. Es prüft die wichtigsten Dienste per
HTTP-Healthcheck. Der Zustand ist auf einen Blick erkennbar.

## Muss-Funktionen (Pflicht)

- Healthcheck für Portainer, n8n, Ollama, Grafana
- Kachel-Ansicht mit Statusbadge

## Explizit nicht (Pflicht)

- kein Auth in v1

## Nur bei Domäne `web`: Seiten-/Routenliste (Pflicht)

| Route | Zweck |
|---|---|
| `/` | Dashboard |
"""


def test_gueltiger_web_intake():
    ergebnis = pruefe_intake(NEU_WEB_GUELTIG)
    assert ergebnis.gueltig, ergebnis.beanstandungen
    assert ergebnis.art == "neu"
    assert ergebnis.domaene == "web"


def test_leere_vorlage_selbst_wird_zurueckgewiesen():
    """Die unausgefüllte Vorlage muss durchfallen — sonst prüft der Worker nichts."""
    vorlage = (VORLAGEN / "intake-neuprojekt.md").read_text()
    ergebnis = pruefe_intake(vorlage)
    assert not ergebnis.gueltig
    assert len(ergebnis.beanstandungen) >= 3


def test_leere_change_vorlage_wird_zurueckgewiesen():
    vorlage = (VORLAGEN / "intake-aenderung.md").read_text()
    ergebnis = pruefe_intake(vorlage)
    assert ergebnis.art == "aenderung"
    assert not ergebnis.gueltig


def test_fehlende_routenliste_bei_web():
    ohne_routen = NEU_WEB_GUELTIG.split("## Nur bei Domäne")[0]
    ergebnis = pruefe_intake(ohne_routen)
    assert any("Routenliste" in b for b in ergebnis.beanstandungen)


def test_zwei_domaenen_angekreuzt():
    doppelt = NEU_WEB_GUELTIG.replace("- [ ] `device-tool`", "- [x] `device-tool`")
    ergebnis = pruefe_intake(doppelt)
    assert any("genau eine" in b for b in ergebnis.beanstandungen)


def test_zu_knappes_ziel():
    knapp = NEU_WEB_GUELTIG.replace(
        "Ein Kachel-Dashboard für das Homelab. Es prüft die wichtigsten Dienste per\n"
        "HTTP-Healthcheck. Der Zustand ist auf einen Blick erkennbar.",
        "Dashboard.",
    )
    ergebnis = pruefe_intake(knapp)
    assert any("3–5 Sätze" in b for b in ergebnis.beanstandungen)


def test_device_tool_braucht_registermap():
    device = NEU_WEB_GUELTIG.replace("- [x] `web`", "- [ ] `web`").replace(
        "- [ ] `device-tool`", "- [x] `device-tool`"
    )
    ergebnis = pruefe_intake(device)
    assert any("Registermap" in b for b in ergebnis.beanstandungen)


def test_unbekannter_kartentyp():
    ergebnis = pruefe_intake("# Irgendeine Karte\n\nText")
    assert ergebnis.art == "unbekannt"
    assert not ergebnis.gueltig


def test_gueltige_aenderungskarte():
    text = """# Intake: Änderung an Projekt X

## Projekt (Pflicht)

homelab-status

## Ziel der Änderung (Pflicht, 3–5 Sätze)

Die Grafana-Kachel zeigt Timeout. Ursache ist der zu knappe Standard-Timeout.
Der Timeout soll pro Dienst konfigurierbar werden.

## Muss-Funktionen / Muss-Verhalten (Pflicht)

- Timeout pro Dienst in der Konfiguration

## Explizit nicht (Pflicht)

- kein Retry-Mechanismus

## Berührt die Änderung die Architektur? (Pflicht)

- [x] Nein
- [ ] Ja
"""
    ergebnis = pruefe_intake(text)
    assert ergebnis.gueltig, ergebnis.beanstandungen
