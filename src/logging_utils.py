"""Journal JSON structure, sans donnees sensibles (la question est hachee)."""
import hashlib
import json
from pathlib import Path


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def log_event(path, event):
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
