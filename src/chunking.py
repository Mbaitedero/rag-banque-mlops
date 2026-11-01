"""Etape 3 : decoupage en chunks avec metadonnees et identifiants stables."""
import hashlib

META_KEYS = ["doc_id", "title", "source", "version", "date", "doc_type", "access_level",
             "status", "corpus_version"]


def chunk_words(text, size, overlap):
    if overlap >= size:
        raise ValueError("overlap doit etre strictement inferieur a size")
    words = text.split()
    step = size - overlap
    chunks = []
    for start in range(0, max(len(words) - overlap, 1), step):
        piece = words[start:start + size]
        if piece:
            chunks.append(" ".join(piece))
    return chunks


def make_chunk_id(doc_id, version, page, idx, text):
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{doc_id}:{version}:p{page}:{idx}:{h}"


def make_chunks(records, size, overlap):
    """Chaque chunk herite des metadonnees de son document."""
    chunks = []
    for rec in records:
        for idx, text in enumerate(chunk_words(rec["text"], size, overlap)):
            meta = {k: rec[k] for k in META_KEYS}
            meta["page"] = int(rec["page"])
            meta["chunk_index"] = idx
            chunks.append({"chunk_id": make_chunk_id(rec["doc_id"], rec["version"], rec["page"], idx, text),
                           "text": text, "metadata": meta})
    return chunks
