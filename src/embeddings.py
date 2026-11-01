"""Etape 4 : embeddings.

- "hash" : representation lexicale deterministe (aucun telechargement) pour la CI et les tests.
- "sentence-transformers" : modele semantique reel (a installer : requirements-optional.txt).
"""
import hashlib
import itertools
import math
import re
import unicodedata
from collections import Counter

STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "et", "ou", "en", "au", "aux", "a",
    "ce", "cette", "ces", "est", "sont", "que", "qui", "quoi", "quel", "quelle", "quels", "quelles",
    "dans", "pour", "par", "sur", "avec", "sans", "je", "il", "elle", "on", "nous", "vous", "mon",
    "ma", "mes", "son", "sa", "ses", "se", "si", "ne", "pas", "plus", "comment", "combien",
    "quand", "faire", "etre", "avoir", "y", "s", "n", "c", "qu", "j", "m", "t",
}


def normalize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def tokenize(text):
    tokens = re.findall(r"[a-z0-9]+", normalize(text))
    out = []
    for t in tokens:
        if t in STOPWORDS:
            continue
        if len(t) > 4 and t.endswith("s"):
            t = t[:-1]
        out.append(t)
    return out


class HashEmbedder:
    name = "hash"

    def __init__(self, dim=512):
        self.dim = dim

    def _idx(self, token):
        return int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % self.dim

    def _vec(self, text):
        tokens = tokenize(text)
        vec = [0.0] * self.dim
        for tok, c in Counter(tokens).items():
            vec[self._idx(tok)] += 1.0 + math.log(c)
        for a, b in itertools.pairwise(tokens):
            vec[self._idx(a + "_" + b)] += 0.5
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def __call__(self, texts):
        return [self._vec(t) for t in texts]


class SentenceTransformerEmbedder:
    def __init__(self, model_name):
        # import tardif : dependance optionnelle (requirements-optional.txt)
        from sentence_transformers import SentenceTransformer

        self.name = f"st:{model_name}"
        self.model = SentenceTransformer(model_name)

    def __call__(self, texts):
        return self.model.encode(list(texts), normalize_embeddings=True).tolist()


def get_embedder(params):
    emb = params["embeddings"]
    if emb["provider"] == "hash":
        return HashEmbedder(emb["hash_dim"])
    if emb["provider"] == "sentence-transformers":
        return SentenceTransformerEmbedder(emb["st_model"])
    raise ValueError(f"provider d'embeddings inconnu : {emb['provider']}")
