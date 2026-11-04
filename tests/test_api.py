import json

from fastapi.testclient import TestClient

from src.api import _add_citations, create_app


class FakeCollection:
    def get(self, ids, include):
        assert ids == ["chunk-1", "chunk-2"]
        assert include == ["documents", "metadatas"]
        return {
            "documents": [
                "Informations générales de la FAQ sans le plafond de retrait.",
                "Le plafond de retrait de la carte Premium est de 1 500 euros."
            ],
            "metadatas": [
                {
                    "doc_id": "tarifs_cartes",
                    "title": "Tarifs cartes",
                    "version": "v2",
                    "page": 1,
                    "access_level": "public",
                },
                {
                    "doc_id": "tarifs_cartes",
                    "title": "Tarifs cartes",
                    "version": "v2",
                    "page": 1,
                    "access_level": "public",
                },
            ],
        }


class FakePipeline:
    collection = FakeCollection()

    def __init__(self):
        self.calls = []

    def answer(self, question, role):
        self.calls.append((question, role))
        return {
            "request_id": "request-123",
            "answer": "Le plafond de retrait de la carte Premium est de 1 500 euros.",
            "refused": False,
            "reason": None,
            "references": [
                {"doc_id": "tarifs_cartes", "version": "v2", "page": 1}
            ],
            "context_chunk_ids": ["chunk-1", "chunk-2"],
            "latency_ms": 4.5,
        }


def create_client(tmp_path):
    pipeline = FakePipeline()
    app = create_app(pipeline, tmp_path / "feedback.jsonl")
    return TestClient(app), pipeline


def test_chat_returns_pipeline_answer_and_numbered_source(tmp_path):
    client, pipeline = create_client(tmp_path)

    response = client.post(
        "/api/chat",
        json={
            "question": "Quel est le plafond de la carte Premium ?",
            "role": "agent",
            "conversation_id": "conversation-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "request-123"
    assert body["answer"].endswith("[1]")
    assert body["references"] == [
        {
            "n": 1,
            "doc_id": "tarifs_cartes",
            "title": "Tarifs cartes",
            "version": "v2",
            "page": 1,
            "access_level": "public",
            "excerpt": "Le plafond de retrait de la carte Premium est de 1 500 euros.",
        }
    ]
    assert pipeline.calls == [
        ("Quel est le plafond de la carte Premium ?", "agent")
    ]


def test_chat_sse_emits_tokens_sources_and_done(tmp_path):
    client, _ = create_client(tmp_path)

    response = client.post(
        "/api/chat",
        headers={"Accept": "text/event-stream"},
        json={
            "question": "Quel est le plafond de la carte Premium ?",
            "role": "agent",
            "conversation_id": "conversation-1",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: token" in response.text
    assert "event: sources" in response.text
    assert "event: done" in response.text
    events = [
        line.removeprefix("data: ")
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert json.loads(events[-1])["request_id"] == "request-123"


def test_chat_rejects_unknown_role(tmp_path):
    client, pipeline = create_client(tmp_path)

    response = client.post(
        "/api/chat",
        json={
            "question": "Question de test",
            "role": "administrateur",
            "conversation_id": "conversation-1",
        },
    )

    assert response.status_code == 422
    assert pipeline.calls == []


def test_feedback_is_saved_as_jsonl(tmp_path):
    client, _ = create_client(tmp_path)

    response = client.post(
        "/api/feedback",
        json={
            "request_id": "request-123",
            "rating": "down",
            "comment": "Réponse à vérifier",
        },
    )

    assert response.status_code == 204
    saved_feedback = (tmp_path / "feedback.jsonl").read_text(encoding="utf-8")
    entry = json.loads(saved_feedback)
    assert entry["request_id"] == "request-123"
    assert entry["rating"] == "down"
    assert entry["comment"] == "Réponse à vérifier"


def test_llm_document_citations_are_converted_to_numbered_citations():
    answer = "Consultez la source [tarifs_cartes v2 p.1]."
    references = [
        {
            "n": 1,
            "doc_id": "tarifs_cartes",
            "version": "v2",
            "page": 1,
        }
    ]

    assert _add_citations(answer, references, []) == "Consultez la source [1]."


def test_numbered_citations_preserve_markdown_line_breaks():
    references = [
        {
            "n": 1,
            "doc_id": "tarifs_cartes",
            "version": "v2",
            "page": 1,
        }
    ]
    answer = "Le plafond de retrait est de 1 500 euros.\n\nLa source est à jour."
    sources = [
        (
            "tarifs_cartes",
            "v2",
            1,
            "Le plafond de retrait est de 1 500 euros.",
        )
    ]

    assert _add_citations(answer, references, sources) == (
        "Le plafond de retrait est de 1 500 euros. [1]\n\nLa source est à jour."
    )
