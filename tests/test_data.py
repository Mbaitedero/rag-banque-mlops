from pathlib import Path

from src.clean import clean_records
from src.config import ROOT
from src.ingest import REQUIRED_COLUMNS, corpus_hash, load_documents, load_inventory

VALID_LEVELS = {"public", "conformite"}


def test_inventory_has_required_columns(params):
    rows = load_inventory(params, ROOT)
    assert rows
    for col in REQUIRED_COLUMNS:
        assert col in rows[0]


def test_doc_ids_are_unique(params):
    ids = [r["doc_id"] for r in load_inventory(params, ROOT)]
    assert len(ids) == len(set(ids))


def test_files_exist_and_access_levels_valid(params):
    for r in load_inventory(params, ROOT):
        path = Path(ROOT) / params["corpus"]["raw_dir"] / r["subdir"] / r["filename"]
        assert path.exists(), path
        assert r["access_level"] in VALID_LEVELS
        assert r["version"] and r["date"]


def test_internal_documents_are_restricted(params):
    for r in load_inventory(params, ROOT):
        if r["subdir"] == "internal":
            assert r["access_level"] != "public"


def test_obsolete_documents_are_not_indexed(params):
    obsolete = {r["doc_id"] for r in load_inventory(params, ROOT) if r["status"] == "obsolete"}
    assert obsolete, "le corpus doit contenir au moins un document obsolete pour ce test"
    indexed = {r["doc_id"] for r in load_documents(params, ROOT)}
    assert not (obsolete & indexed)


def test_cleaned_records_are_valid(params):
    records, _stats = clean_records(load_documents(params, ROOT), params)
    assert records
    assert all(r["text"].strip() for r in records)
    texts = [r["text"] for r in records]
    assert len(texts) == len(set(texts)), "doublons exacts apres nettoyage"


def test_pdf_headers_and_footers_removed(params):
    records, _ = clean_records(load_documents(params, ROOT), params)
    tarifs = [r for r in records if r["doc_id"] == "tarifs_cartes"]
    assert len(tarifs) == 2
    assert all("Tarifs 2026 - document fictif" not in r["text"] for r in tarifs)
    assert all("Page 1/2" not in r["text"] and "Page 2/2" not in r["text"] for r in tarifs)


def test_corpus_hash_is_stable(params):
    assert corpus_hash(params, ROOT) == corpus_hash(params, ROOT)
