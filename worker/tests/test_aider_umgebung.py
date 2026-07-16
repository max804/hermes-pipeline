from hermes_worker.aider_runner import aider_umgebung


def test_ollama_api_base_wird_gesetzt(konfig):
    konfig.ollama_api_base = "http://192.168.178.27:11434"
    umgebung = aider_umgebung(konfig)
    assert umgebung["OLLAMA_API_BASE"] == "http://192.168.178.27:11434"


def test_leer_laesst_umgebung_unveraendert(konfig, monkeypatch):
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    konfig.ollama_api_base = ""
    assert "OLLAMA_API_BASE" not in aider_umgebung(konfig)
