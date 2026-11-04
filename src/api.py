"""API HTTP pour exposer le pipeline RAG existant au frontend."""
from __future__ import annotations

import json
import os
import re
import threading
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from src.config import ROOT

UserRole = Literal["agent", "conformite"]
RefusalReason = Literal[
    "retrieval_insuffisant", "refus_modele", "acces_refuse", "erreur"
]

_feedback_lock = threading.Lock()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=8000)
    role: UserRole
    conversation_id: str = Field(min_length=1, max_length=128)


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=128)
    rating: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=2000)


class ChatReference(BaseModel):
    n: int
    doc_id: str
    title: str
    version: str
    page: int
    access_level: Literal["public", "conformite"]
    excerpt: str


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    refused: bool
    reason: RefusalReason | None
    references: list[ChatReference]
    latency_ms: float


def _reference_key(reference: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(reference["doc_id"]),
        str(reference["version"]),
        int(reference["page"]),
    )


def _make_references(
    pipeline: Any, result: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[tuple[str, str, int, str]]]:
    raw_references = result.get("references", [])
    chunk_ids = result.get("context_chunk_ids", [])
    if not raw_references:
        return [], []
    if not chunk_ids:
        raise RuntimeError("Le pipeline a retourné des références sans chunks sources.")

    chunks = pipeline.collection.get(
        ids=chunk_ids,
        include=["documents", "metadatas"],
    )
    documents = chunks.get("documents") or []
    metadatas = chunks.get("metadatas") or []
    source_chunks: dict[tuple[str, str, int], list[tuple[str, dict[str, Any]]]] = {}
    for document, metadata in zip(documents, metadatas):
        if not isinstance(document, str) or not isinstance(metadata, dict):
            continue
        key = (
            str(metadata.get("doc_id", "")),
            str(metadata.get("version", "")),
            int(metadata.get("page", 0)),
        )
        source_chunks.setdefault(key, []).append((document, metadata))

    references: list[dict[str, Any]] = []
    citation_sources: list[tuple[str, str, int, str]] = []
    answer_sentences = [
        _normalize_text(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+", str(result.get("answer", "")))
        if sentence.strip()
    ]
    for number, raw_reference in enumerate(raw_references, start=1):
        key = _reference_key(raw_reference)
        matches = source_chunks.get(key, [])
        if not matches:
            raise RuntimeError(
                f"Les métadonnées du chunk référencé {key[0]} sont indisponibles."
            )
        excerpt, metadata = max(
            matches,
            key=lambda match: sum(
                sentence in _normalize_text(match[0])
                for sentence in answer_sentences
            ),
        )
        access_level = metadata.get("access_level")
        if access_level not in {"public", "conformite"}:
            raise RuntimeError(
                f"Niveau d’accès invalide pour la source {key[0]}."
            )
        references.append(
            {
                "n": number,
                "doc_id": key[0],
                "title": str(metadata.get("title", key[0])),
                "version": key[1],
                "page": key[2],
                "access_level": access_level,
                "excerpt": excerpt[:800],
            }
        )
        citation_sources.append(
            (*key, "\n".join(document for document, _ in matches))
        )
    return references, citation_sources


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _add_citations(
    answer: str,
    references: list[dict[str, Any]],
    citation_sources: list[tuple[str, str, int, str]],
) -> str:
    if not answer or not references:
        return answer

    rewritten = answer
    for reference in references:
        citation = re.compile(
            r"\[\s*"
            + re.escape(reference["doc_id"])
            + r"\s+"
            + re.escape(reference["version"])
            + r"\s+p\.?"
            + str(reference["page"])
            + r"\s*\]"
        )
        rewritten = citation.sub(f"[{reference['n']}]", rewritten)

    parts = re.split(r"(?<=[.!?])(?=\s|$)", rewritten)
    cited_parts: list[str] = []
    for part in parts:
        body = part.rstrip()
        if not body.strip() or re.search(r"\[\d+\]", body):
            cited_parts.append(part)
            continue
        normalized_part = _normalize_text(body)
        matching_numbers = [
            reference["n"]
            for reference, source in zip(references, citation_sources)
            if normalized_part
            and normalized_part in _normalize_text(source[3])
        ]
        if matching_numbers:
            trailing_whitespace = part[len(body) :]
            part = (
                f"{body} "
                + " ".join(f"[{number}]" for number in matching_numbers)
                + trailing_whitespace
            )
        cited_parts.append(part)
    return "".join(cited_parts)


def _make_chat_response(pipeline: Any, payload: ChatRequest) -> dict[str, Any]:
    result = pipeline.answer(payload.question, payload.role)
    references, citation_sources = _make_references(pipeline, result)
    answer = _add_citations(
        str(result.get("answer", "")), references, citation_sources
    )
    return ChatResponse(
        request_id=str(result.get("request_id") or uuid4()),
        answer=answer,
        refused=bool(result["refused"]),
        reason=result.get("reason"),
        references=references,
        latency_ms=float(result["latency_ms"]),
    ).model_dump()


def _sse_event(name: str, payload: Any) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_response(response: dict[str, Any]):
    for token in re.findall(r"\S+\s*", response["answer"]):
        yield _sse_event("token", {"token": token})
    yield _sse_event("sources", response["references"])
    yield _sse_event("done", response)


def create_app(
    pipeline: Any | None = None,
    feedback_path: str | Path | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.pipeline is None:
            from src.config import load_params
            from src.rag import build_pipeline

            app.state.pipeline = build_pipeline(load_params())
        yield

    application = FastAPI(
        title="MBAITEDERO BANK — Assistant documentaire",
        description="API du RAG documentaire fictif MBAITEDERO BANK.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.pipeline = pipeline
    application.state.feedback_path = Path(
        feedback_path
        or os.environ.get(
            "FEEDBACK_LOG_PATH", str(ROOT / "logs" / "feedback.jsonl")
        )
    )

    allowed_origins = [
        origin.strip()
        for origin in os.environ.get(
            "FRONTEND_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept"],
    )

    @application.get("/api/health")
    def health(request: Request):
        if request.app.state.pipeline is None:
            raise HTTPException(
                status_code=503,
                detail="Le pipeline RAG n’est pas initialisé.",
            )
        return {"status": "ok", "service": "MBAITEDERO BANK"}

    @application.post("/api/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest, request: Request):
        rag_pipeline = request.app.state.pipeline
        if rag_pipeline is None:
            raise HTTPException(
                status_code=503,
                detail="Le pipeline RAG n’est pas initialisé.",
            )
        response = _make_chat_response(rag_pipeline, payload)
        if "text/event-stream" in request.headers.get("accept", ""):
            return StreamingResponse(
                _stream_response(response),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        return response

    @application.post("/api/feedback", status_code=204)
    def feedback(payload: FeedbackRequest, request: Request):
        path: Path = request.app.state.feedback_path
        entry = {
            "request_id": payload.request_id,
            "rating": payload.rating,
            "comment": payload.comment,
            "received_at": datetime.now(UTC).isoformat(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with _feedback_lock, path.open("a", encoding="utf-8") as feedback_file:
            feedback_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return application


app = create_app()
