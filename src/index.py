"""Etape 5 : index vectoriel unique (ChromaDB) avec metadonnees."""
import chromadb


def get_client(index_dir):
    return chromadb.PersistentClient(path=str(index_dir))


def build_index(chunks, embedder, index_dir, collection_name, batch_size=64):
    client = get_client(index_dir)
    names = [getattr(c, "name", c) for c in client.list_collections()]
    if collection_name in names:
        client.delete_collection(collection_name)
    col = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        col.add(ids=[c["chunk_id"] for c in batch],
                documents=[c["text"] for c in batch],
                embeddings=embedder([c["text"] for c in batch]),
                metadatas=[c["metadata"] for c in batch])
    return col


def get_collection(index_dir, collection_name):
    return get_client(index_dir).get_collection(collection_name)
