"""Controle d'acces documentaire : table role -> niveaux d'acces (refus par defaut)."""
from pathlib import Path

import yaml

from src.config import ROOT


def load_roles(path=None):
    p = Path(path) if path else ROOT / "data" / "users.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)["roles"]


def allowed_levels(role, roles=None):
    roles = roles if roles is not None else load_roles()
    if role not in roles:
        raise PermissionError(f"role inconnu : {role}")
    return list(roles[role]["access_levels"])
