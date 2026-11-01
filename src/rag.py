"""Etapes 7 a 11 : retrieval, seuil, assemblage du contexte, generation, references, journal."""
import time
import uuid

from src.access import load_roles
from src.config import min_score
from src.embeddings import get_embedder
from src.index import get_collection
from src.llm import REFUSAL_TEXT, get_llm
from src.logging_utils import hash_text, log_event
from src.retriever import retrieve
from src.security import sanitize


class RagPipeline:
    def __init__(self, params, collection, embedder, llm, roles=None):
        self.params, self.collection, self.embedder, self.llm = params, collection, embedder, llm
        self.roles = roles if roles is not None else load_roles()
        self.threshold = min_score(params)
        self.log_path = params["logging"]["requests_log"]

    def _prepare_context(self, hits):
        """Sanitisation au moment de la requete (defense en profondeur)."""
        passages, flagged = [], 0
        for h in hits:
            text, removed = sanitize(h["text"]) if self.params["security"]["sanitize_at_query"] \
                else (h["text"], 0)
            flagged += removed
            if text.strip():
                passages.append({**h, "text": text})
        return passages, flagged

    def answer(self, question, role, log=True):
        start = time.perf_counter()
        event = {"request_id": str(uuid.uuid4()), "question_hash": hash_text(question),
                 "role": role, "error": None}
        result = {"answer": REFUSAL_TEXT, "references": [], "refused": True, "reason": None,
                  "retrieved": [], "context_chunk_ids": [], "flagged": 0, "top_score": 0.0,
                  "prompt_tokens": 0, "completion_tokens": 0}
        try:
            hits = retrieve(self.collection, self.embedder, question, role,
                            self.params["retrieval"]["top_k"], self.roles)
            result["retrieved"] = [{"chunk_id": h["chunk_id"], "doc_id": h["meta"]["doc_id"],
                                    "access_level": h["meta"]["access_level"],
                                    "score": round(h["score"], 4)} for h in hits]
            result["top_score"] = hits[0]["score"] if hits else 0.0
            if not hits or result["top_score"] < self.threshold:
                result["reason"] = "retrieval_insuffisant"
            else:
                passages, flagged = self._prepare_context(hits)
                result["flagged"] = flagged
                result["context_chunk_ids"] = [p["chunk_id"] for p in passages]
                out = self.llm(question, passages)
                result.update(answer=out["text"], prompt_tokens=out["prompt_tokens"],
                              completion_tokens=out["completion_tokens"])
                result["refused"] = out["text"].strip() == REFUSAL_TEXT
                result["reason"] = "refus_modele" if result["refused"] else None
                if not result["refused"]:
                    refs = {(p["meta"]["doc_id"], p["meta"]["version"], p["meta"]["page"]) for p in passages}
                    result["references"] = [{"doc_id": d, "version": v, "page": pg}
                                            for d, v, pg in sorted(refs)]
        except PermissionError as exc:
            result.update(reason="acces_refuse")
            event["error"] = f"PermissionError: {exc}"
        except Exception as exc:  # noqa: BLE001  erreur LLM, reseau, index... : journalisee, jamais masquee
            result.update(reason="erreur")
            event["error"] = f"{type(exc).__name__}: {exc}"
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        event.update(refused=result["refused"], reason=result["reason"], latency_ms=result["latency_ms"],
                     n_passages=len(result["context_chunk_ids"]), top_score=round(result["top_score"], 4),
                     flagged=result["flagged"], prompt_tokens=result["prompt_tokens"],
                     completion_tokens=result["completion_tokens"],
                     config=self.params["chunking"]["active"])
        if log:
            log_event(self.log_path, event)
        return result


def build_pipeline(params, index_dir=None, llm=None, embedder=None):
    index_dir = index_dir or params["index"]["dir"]
    collection = get_collection(index_dir, params["index"]["collection"])
    return RagPipeline(params, collection, embedder or get_embedder(params), llm or get_llm(params))
