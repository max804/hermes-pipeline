from pathlib import Path

import pytest

from hermes_schemas import cli

WURZEL = Path(__file__).parent.parent.parent
BEISPIEL = WURZEL / "schemas" / "beispiele" / "projekt.beispiel.yaml"


def _lauf(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr("sys.argv", ["hermes-validiere", *argv])
    return cli.main()


def test_valide_datei_gibt_null(monkeypatch, capsys):
    assert _lauf(monkeypatch, str(BEISPIEL)) == 0
    assert "OK: homelab-status" in capsys.readouterr().out


def test_invalide_datei_gibt_eins(monkeypatch, tmp_path, capsys):
    kaputt = tmp_path / "projekt.yaml"
    kaputt.write_text(BEISPIEL.read_text().replace("abhaengig_von: [K01]", "abhaengig_von: [K99]"))
    assert _lauf(monkeypatch, str(kaputt)) == 1
    assert "K99" in capsys.readouterr().out


def test_fehlende_datei_gibt_zwei(monkeypatch):
    assert _lauf(monkeypatch, "/gibt/es/nicht.yaml") == 2


def test_falscher_aufruf_gibt_zwei(monkeypatch):
    assert _lauf(monkeypatch) == 2


@pytest.mark.parametrize(
    "kopie",
    [WURZEL / "skills" / "hermes-architekt" / "references" / "projekt.beispiel.yaml"],
    ids=["skill-referenz"],
)
def test_beispiel_kopien_bleiben_valide_und_identisch(kopie):
    """Der Skill reist ohne dieses Repo — seine Beispiel-Kopie darf nie
    vom validierten Original in schemas/beispiele/ abweichen."""
    assert kopie.read_text() == BEISPIEL.read_text(), (
        f"{kopie} weicht vom Original ab — Kopie nachziehen"
    )
