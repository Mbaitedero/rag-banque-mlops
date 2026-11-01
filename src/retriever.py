"""Retrieval avec filtre d'acces applique DANS la requete vectorielle (jamais apres)."""
from src.access import allowed_levels


def retrieve(collection, embed, question, role, top_k, roles=None):
    levels = allowed_levels(role, roles)                 # refus par defaut
    res = collection.query(
        query_embeddings=embed([question]),
        n_results=top_k,
        where={"access_level": {"$in": levels}},         # filtre avant/pendant la recherche
    )
    hits = []
    for cid, text, meta, dist in zip(res["ids"][0], res["documents"][0],
                                     res["metadatas"][0], res["distances"][0]):
        hits.append({"chunk_id": cid, "text": text, "meta": meta, "score": 1.0 - dist})
    return sorted(hits, key=lambda h: h["score"], reverse=True)
