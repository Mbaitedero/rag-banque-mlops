"""Etape 1 : ingestion. Extrait le texte de chaque document et conserve la provenance."""
import csv
import hashlib
from pathlib import Path

from pypdf import PdfReader

from src.config import ROOT

REQUIRED_COLUMNS = ["doc_id", "title", "subdir", "filename", "source", "license", "version",
                    "date", "doc_type", "access_level", "status"]


def load_inventory(params, root=ROOT):
    path = Path(root) / params["corpus"]["inventory"]
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def corpus_hash(params, root=ROOT):
    """Empreinte du corpus : inventaire + contenu de tous les fichiers references."""
    h = hashlib.sha256()
    inv = load_inventory(params, root)
    h.update((Path(root) / params["corpus"]["inventory"]).read_bytes())
    for row in sorted(inv, key=lambda r: r["doc_id"]):
        p = Path(root) / params["corpus"]["raw_dir"] / row["subdir"] / row["filename"]
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _read_pdf(path):
    reader = PdfReader(str(path))
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def _read_text(path):
    return [(1, Path(path).read_text(encoding="utf-8"))]


def load_documents(params, root=ROOT):
    """Retourne une liste d'enregistrements {doc_id, page, text, ...metadonnees}."""
    records = []
    allowed = set(params["corpus"]["include_status"])
    for row in load_inventory(params, root):
        if row["status"] not in allowed:
            continue
        path = Path(root) / params["corpus"]["raw_dir"] / row["subdir"] / row["filename"]
        pages = _read_pdf(path) if path.suffix.lower() == ".pdf" else _read_text(path)
        for page, text in pages:
            rec = {k: row[k] for k in REQUIRED_COLUMNS}
            rec["page"] = page
            rec["text"] = text
            rec["corpus_version"] = params["corpus"]["version"]
            records.append(rec)
    return records
