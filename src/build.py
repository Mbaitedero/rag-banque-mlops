"""Construction reproductible de l'index (hors ligne) pour une configuration donnee."""
import json
import time
from pathlib import Path

from src import chunking, clean, ingest
from src.config import ROOT, chunk_config
from src.embeddings import get_embedder
from src.index import build_index


def prepare_chunks(params, config_name=None, root=ROOT):
    name, size, overlap = chunk_config(params, config_name)
    records = ingest.load_documents(params, root)
    records, stats = clean.clean_records(records, params)
    chunks = chunking.make_chunks(records, size, overlap)
    return name, records, chunks, stats


def _write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def build(params, config_name=None, index_dir=None, root=ROOT, write_processed=True):
    start = time.perf_counter()
    name, records, chunks, stats = prepare_chunks(params, config_name, root)
    embedder = get_embedder(params)
    index_dir = index_dir or (Path(root) / params["index"]["dir"])
    build_index(chunks, embedder, index_dir, params["index"]["collection"])
    if write_processed:
        out = Path(root) / params["corpus"]["processed_dir"]
        _write_jsonl(out / "documents.jsonl", records)
        _write_jsonl(out / f"chunks_{name}.jsonl", chunks)
    return {"config": name, "n_documents": len({r["doc_id"] for r in records}),
            "n_chunks": len(chunks), "build_time_s": round(time.perf_counter() - start, 3),
            "corpus_hash": ingest.corpus_hash(params, root), "embedder": embedder.name,
            "index_dir": str(index_dir), **{f"clean_{k}": v for k, v in stats.items()}}
