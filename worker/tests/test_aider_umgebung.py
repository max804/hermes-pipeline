from hermes_worker.aider_runner import aider_umgebung


def test_openai_server_wird_gesetzt(konfig):
    konfig.openai_api_base = "http://192.168.178.27:13305/api/v1"
    konfig.openai_api_key = "lemonade"
    umgebung = aider_umgebung(konfig)
    assert umgebung["OPENAI_API_BASE"] == "http://192.168.178.27:13305/api/v1"
    assert umgebung["OPENAI_API_KEY"] == "lemonade"


def test_openai_ohne_schluessel_bekommt_dummy(konfig):
    konfig.openai_api_base = "http://192.168.178.27:13305/api/v1"
    konfig.openai_api_key = ""
    assert aider_umgebung(konfig)["OPENAI_API_KEY"] == "unbenutzt"


def test_ollama_api_base_wird_gesetzt(konfig):
    konfig.ollama_api_base = "http://192.168.178.27:11434"
    umgebung = aider_umgebung(konfig)
    assert umgebung["OLLAMA_API_BASE"] == "http://192.168.178.27:11434"


def test_leer_laesst_umgebung_unveraendert(konfig, monkeypatch):
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    konfig.ollama_api_base = ""
    konfig.openai_api_base = ""
    umgebung = aider_umgebung(konfig)
    assert "OLLAMA_API_BASE" not in umgebung
    assert "OPENAI_API_BASE" not in umgebung
