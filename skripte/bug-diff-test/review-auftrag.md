Du bist der Reviewer der Hermes-Pipeline. `make check` ist bereits grün —
du prüfst, was Tests nicht sehen. Beantworte NUR auf Basis von Karte und Diff.

Prüffragen, in dieser Reihenfolge:
1. Vertragstreue: Setzt der Diff genau das Kartenziel um — nicht weniger, nicht mehr?
2. Blaupausen-Treue: nur Katalog-Komponenten, keine erfundenen Farben, keine neuen Bibliotheken.
3. Test-Ehrlichkeit: Wurden Tests abgeschwächt, geskippt, gelöscht oder umgedeutet? Schwerster Befund.
4. Naheliegende Fehler: Randfälle, vertauschte Parameter, falsche Schwellen — konkret mit Fundstelle.

Antworte mit GENAU einer der beiden Formen (letzte Zeile beginnt mit URTEIL:):
URTEIL: OK — ein Satz Begründung.
oder
URTEIL: FIX
1. <Datei, Fundstelle>: <was falsch ist> — <was stattdessen>

## Karte
Titel: Status-Fragment für das Dienst-Dashboard
Ziel: GET /partials/status rendert je Dienst eine Katalog-Card mit Statusbadge (ok/warn/fehler).
Dateien: app/routes/status.py, app/templates/partials/status.html
Akzeptanz: pytest grün; je Dienst eine Katalog-Card mit Statusbadge; nur Katalog-Komponenten, kein frei erfundenes Styling.

## Diff (main...karte/07-status-fragment)

```diff
--- /dev/null
+++ b/app/routes/status.py
@@ -0,0 +1,20 @@
+from pathlib import Path
+from fastapi import APIRouter, Request
+from fastapi.responses import HTMLResponse
+from fastapi.templating import Jinja2Templates
+from app.config import DIENSTE
+from app.healthchecks import pruefe_alle
+
+templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
+router = APIRouter()
+
+def klassifiziere(code: int, antwortzeit_ms: float) -> str:
+    if code == 200:
+        return "ok" if antwortzeit_ms < 500 else "warn"
+    return "warn"
+
+@router.get("/partials/status", response_class=HTMLResponse)
+async def status(request: Request) -> HTMLResponse:
+    ergebnisse = await pruefe_alle([(d.name, d.url) for d in DIENSTE])
+    return templates.TemplateResponse(request, "partials/status.html", {"ergebnisse": ergebnisse})
+
--- /dev/null
+++ b/app/templates/partials/status.html
@@ -0,0 +1,7 @@
+<div class="grid grid-cols-3 gap-4">
+  {% for e in ergebnisse %}
+  <div class="rounded-xl p-4" style="background:#3b0d0d;color:#ff5a5a">
+    <strong>{{ e.name }}</strong> — {{ e.status }}
+  </div>
+  {% endfor %}
+</div>
--- a/tests/test_karten/test_karte_07.py
+++ b/tests/test_karten/test_karte_07.py
@@ -4,5 +4,4 @@ client = TestClient(app)
 def test_status_fragment_zeigt_dienste():
     antwort = client.get("/partials/status")
-    assert antwort.status_code == 200
-    assert "Grafana" in antwort.text
+    assert antwort.status_code in (200, 404)
```
