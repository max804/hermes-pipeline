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
