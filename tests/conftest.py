import copy

import pytest

from src.build import build
from src.config import ROOT, load_params
from src.embeddings import get_embedder
from src.index import get_collection
from src.llm import ExtractiveLLM
from src.rag import RagPipeline


@pytest.fixture(scope="session")
def params():
    p = load_params()
    p = copy.deepcopy(p)
    p["embeddings"]["provider"] = "hash"           # CI deterministe, aucun telechargement
    p["llm"]["provider"] = "extractive"
    p["logging"]["requests_log"] = None
    return p


@pytest.fixture(scope="session")
def index_dir(tmp_path_factory, params):
    d = tmp_path_factory.mktemp("index")
    build(params, "A", index_dir=d, root=ROOT, write_processed=False)
    return d


@pytest.fixture(scope="session")
def embed(params):
    return get_embedder(params)


@pytest.fixture(scope="session")
def collection(index_dir, params):
    return get_collection(index_dir, params["index"]["collection"])


class SpyLLM(ExtractiveLLM):
    """LLM extractif qui memorise les passages recus (pour verifier ce qui entre dans le contexte)."""
    def __init__(self):
        self.seen = []

    def __call__(self, question, passages):
        self.seen.append(list(passages))
        return super().__call__(question, passages)


@pytest.fixture()
def spy():
    return SpyLLM()


@pytest.fixture()
def pipeline(params, collection, embed, spy):
    return RagPipeline(params, collection, embed, spy)
