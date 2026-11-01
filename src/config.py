"""Chargement des parametres et des chemins du projet."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_params(path=None):
    p = Path(path) if path else ROOT / "params.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def chunk_config(params, name=None):
    name = name or params["chunking"]["active"]
    cfg = params["chunking"]["configs"][name]
    return name, cfg["size"], cfg["overlap"]


def min_score(params):
    provider = params["embeddings"]["provider"]
    return params["retrieval"]["min_score"][provider]
