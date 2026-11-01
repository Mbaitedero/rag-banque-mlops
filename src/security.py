"""Detection simple d'instructions malveillantes dans les documents (prompt injection documentaire)."""
import re

INJECTION_PATTERNS = [
    r"ignore[rz]?\s+(toutes\s+)?(les\s+)?(r[eè]gles|instructions)",
    r"ignore\s+(all|any|previous)",
    r"important pour l.assistant",
    r"(r[eé]v[eè]le|affiche|donne)[^.]{0,40}(code secret|mot de passe)",
    r"code secret",
    r"system prompt",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def is_suspicious(sentence):
    return any(p.search(sentence) for p in _COMPILED)


def sanitize(text):
    """Retire les phrases suspectes. Retourne (texte_nettoye, nombre_de_phrases_retirees)."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    kept, removed = [], 0
    for part in parts:
        if part.strip() and is_suspicious(part):
            removed += 1
        else:
            kept.append(part)
    return " ".join(p for p in kept if p.strip()), removed
