"""Git-Operationen im Projekt-Repo (ARCHITEKTUR.md §8: Branch pro Karte)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


class GitFehler(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    lauf = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120
    )
    if lauf.returncode != 0:
        raise GitFehler(f"git {' '.join(args)}: {lauf.stderr.strip()}")
    return lauf.stdout.strip()


def branch_name(karten_id: str, titel: str) -> str:
    """K07 + 'Geräteliste-View' → karte/07-geraeteliste-view"""
    nummer = karten_id.lstrip("K")
    slug = titel.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        slug = slug.replace(a, b)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")[:40].rstrip("-")
    return f"karte/{nummer}-{slug}"


def beginne_karte(repo: Path, branch: str) -> None:
    """Fix-Runde setzt auf dem bestehenden Branch auf, sonst frisch von main."""
    _git(repo, "checkout", "main")
    vorhandene = _git(repo, "branch", "--list", branch)
    if vorhandene:
        _git(repo, "checkout", branch)
    else:
        _git(repo, "checkout", "-b", branch)


def aktiviere_test_stub(repo: Path, karten_id: str) -> bool:
    """Materialisierte Stubs liegen als tests/test_karten/….py.wartend, damit
    `make check` nicht an den roten Tests ALLER späteren Karten scheitert.
    Beim Start der Karte wird ihr Stub scharfgeschaltet und committet."""
    nummer = karten_id.lstrip("K")
    wartend = repo / "tests" / "test_karten" / f"test_karte_{nummer}.py.wartend"
    ziel = wartend.with_suffix("")  # .py
    if not wartend.exists():
        return ziel.exists()  # schon aktiviert (Fix-Runde) oder nie materialisiert
    _git(repo, "mv", str(wartend.relative_to(repo)), str(ziel.relative_to(repo)))
    _git(repo, "commit", "-m", f"[{karten_id}] Test-Stub aktiviert")
    return True


def commit_alle(repo: Path, botschaft: str) -> None:
    _git(repo, "add", "-A")
    if _git(repo, "status", "--porcelain"):  # leer = nichts zu committen
        _git(repo, "commit", "-m", botschaft)


def verwerfe_branch(repo: Path, branch: str) -> None:
    """Abbruch/Timeout: Branch verwerfen, Arbeitskopie sauber auf main."""
    subprocess.run(
        ["git", "-C", str(repo), "reset", "--hard"], capture_output=True, timeout=120
    )
    subprocess.run(
        ["git", "-C", str(repo), "checkout", "main"], capture_output=True, timeout=120
    )
    subprocess.run(
        ["git", "-C", str(repo), "branch", "-D", branch], capture_output=True, timeout=120
    )
