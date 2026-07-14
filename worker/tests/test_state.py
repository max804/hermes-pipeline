from hermes_worker.state import WorkerZustand


def test_versuche_zaehlen(zustand: WorkerZustand):
    zustand.registriere("42", "homelab-status", "karte/01-x")
    assert zustand.versuche("42") == 0
    assert zustand.erhoehe_versuche("42") == 1
    assert zustand.erhoehe_versuche("42") == 2


def test_unbekannte_karte_hat_null_versuche(zustand: WorkerZustand):
    assert zustand.versuche("gibtsnicht") == 0


def test_laufende_karten_ueberleben_reconnect(tmp_path):
    pfad = tmp_path / "w.db"
    z1 = WorkerZustand(pfad)
    z1.registriere("7", "homelab-status", "karte/07-x")
    z1.setze_laufend("7", True)
    z1.schliesse()

    z2 = WorkerZustand(pfad)  # simulierter Neustart
    assert z2.laufende_karten() == [("7", "homelab-status", "karte/07-x")]
    z2.setze_laufend("7", False)
    assert z2.laufende_karten() == []
    z2.schliesse()


def test_intake_kommentar_duplikatschutz(zustand: WorkerZustand):
    assert not zustand.intake_bereits_kommentiert("1", "abc")
    zustand.merke_intake_kommentar("1", "abc")
    assert zustand.intake_bereits_kommentiert("1", "abc")
    assert not zustand.intake_bereits_kommentiert("1", "geaendert")


def test_letzte_pruefung(zustand: WorkerZustand):
    zustand.registriere("42", "p", "b")
    assert zustand.letzte_pruefung("42") == ""
    zustand.setze_letzte_pruefung("42", "FAILED test_x")
    assert zustand.letzte_pruefung("42") == "FAILED test_x"
