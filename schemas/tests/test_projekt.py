from pathlib import Path

import pytest

from hermes_schemas.projekt import ProjektValidierungsFehler, lade_projekt_yaml

BEISPIEL = (Path(__file__).parent.parent / "beispiele" / "projekt.beispiel.yaml").read_text()


def test_beispiel_ist_valide():
    projekt = lade_projekt_yaml(BEISPIEL)
    assert projekt.projekt.name == "homelab-status"
    assert [k.id for k in projekt.karten] == ["K01", "K02", "K03"]


def _mit_ersetzung(alt: str, neu: str) -> str:
    assert alt in BEISPIEL
    return BEISPIEL.replace(alt, neu)


def test_unbekannte_abhaengigkeit_wird_beanstandet():
    kaputt = _mit_ersetzung("abhaengig_von: [K01]", "abhaengig_von: [K99]")
    with pytest.raises(ProjektValidierungsFehler) as e:
        lade_projekt_yaml(kaputt)
    assert any("K99" in f for f in e.value.fehler)


def test_zyklus_wird_erkannt():
    kaputt = _mit_ersetzung("abhaengig_von: []", "abhaengig_von: [K03]")
    with pytest.raises(ProjektValidierungsFehler) as e:
        lade_projekt_yaml(kaputt)
    assert any("Zyklus" in f for f in e.value.fehler)


def test_pfad_ausserhalb_des_namensraums_wird_beanstandet():
    kaputt = _mit_ersetzung("- app/healthchecks.py", "- ../../etc/passwd")
    with pytest.raises(ProjektValidierungsFehler) as e:
        lade_projekt_yaml(kaputt)
    assert any("passwd" in f for f in e.value.fehler)


def test_fehler_werden_gesammelt_nicht_einzeln():
    kaputt = _mit_ersetzung("abhaengig_von: [K01]", "abhaengig_von: [K99]")
    kaputt = kaputt.replace("- app/healthchecks.py", "- /absolut/verboten.py")
    with pytest.raises(ProjektValidierungsFehler) as e:
        lade_projekt_yaml(kaputt)
    assert len(e.value.fehler) >= 2


def test_kaputtes_yaml_gibt_lesbaren_fehler():
    with pytest.raises(ProjektValidierungsFehler) as e:
        lade_projekt_yaml(":\n  - [")
    assert "YAML" in e.value.fehler[0]


def test_pflichtfelder_fehlen():
    with pytest.raises(ProjektValidierungsFehler) as e:
        lade_projekt_yaml("projekt:\n  name: x\n")
    assert e.value.fehler  # gesammelte, lesbare Meldungen
