"""Etape 2 : nettoyage reproductible des documents."""
import hashlib
import re
from collections import defaultdict

from src.security import sanitize


def _strip_markdown(text):
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("`", "")
    return text


def _remove_repeated_lines(records):
    """Retire les en-tetes et pieds de page : lignes presentes sur toutes les pages d'un PDF."""
    by_doc = defaultdict(list)
    for r in records:
        by_doc[r["doc_id"]].append(r)
    for recs in by_doc.values():
        if len(recs) < 2:
            continue
        counts = defaultdict(int)
        for r in recs:
            keys = {re.sub(r"\d+", "#", ln.strip()) for ln in r["text"].splitlines() if ln.strip()}
            for k in keys:
                counts[k] += 1
        repeated = {k for k, c in counts.items() if c == len(recs)}
        for r in recs:
            lines = [ln for ln in r["text"].splitlines()
                     if re.sub(r"\d+", "#", ln.strip()) not in repeated]
            r["text"] = "\n".join(lines)


def clean_records(records, params, min_chars=20):
    """Retourne (enregistrements nettoyes, statistiques)."""
    stats = {"empty_removed": 0, "duplicates_removed": 0, "injection_sentences_removed": 0}
    records = [dict(r) for r in records]
    _remove_repeated_lines(records)
    seen, out = set(), []
    for r in records:
        text = _strip_markdown(r["text"])
        if params["security"]["sanitize_at_ingest"]:
            text, removed = sanitize(text)
            stats["injection_sentences_removed"] += removed
        text = re.sub(r"[ \t\xa0]+", " ", text)
        text = re.sub(r"\s*\n\s*", "\n", text).strip()
        if len(text) < min_chars:
            stats["empty_removed"] += 1
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in seen:
            stats["duplicates_removed"] += 1
            continue
        seen.add(digest)
        r["text"] = text
        out.append(r)
    return out, stats
