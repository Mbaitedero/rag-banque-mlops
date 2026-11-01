import pytest

from src.chunking import chunk_words, make_chunk_id, make_chunks


def test_chunk_size_is_respected():
    text = " ".join(f"mot{i}" for i in range(250))
    chunks = chunk_words(text, size=60, overlap=10)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 60 for c in chunks)


def test_overlap_between_consecutive_chunks():
    text = " ".join(f"mot{i}" for i in range(200))
    chunks = chunk_words(text, size=50, overlap=10)
    assert chunks[0].split()[-10:] == chunks[1].split()[:10]


def test_short_text_gives_one_chunk():
    assert chunk_words("un deux trois", size=60, overlap=10) == ["un deux trois"]


def test_invalid_overlap_rejected():
    with pytest.raises(ValueError):
        chunk_words("a b c", size=5, overlap=5)


def test_chunk_ids_are_deterministic():
    assert make_chunk_id("doc", "v1", 1, 0, "texte") == make_chunk_id("doc", "v1", 1, 0, "texte")
    assert make_chunk_id("doc", "v1", 1, 0, "texte") != make_chunk_id("doc", "v1", 1, 0, "autre")


def test_chunks_inherit_metadata():
    rec = {"doc_id": "d1", "title": "T", "source": "s", "version": "v1", "date": "2026-01-01",
           "doc_type": "faq", "access_level": "conformite", "status": "active",
           "corpus_version": "corpus-v1", "page": 1, "text": " ".join(["mot"] * 130)}
    chunks = make_chunks([rec], size=60, overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert c["metadata"]["access_level"] == "conformite"
        assert c["metadata"]["doc_id"] == "d1"
        assert c["metadata"]["page"] == 1
