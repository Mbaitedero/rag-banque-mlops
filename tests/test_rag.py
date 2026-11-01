import json

from src.llm import REFUSAL_TEXT
from src.monitoring import load_events, summarize


def test_answerable_question_returns_answer_and_references(pipeline):
    res = pipeline.answer("Quel est le plafond de retrait de la carte Premium ?", "agent", log=False)
    assert not res["refused"]
    assert "1 500" in res["answer"]
    assert res["references"]


def test_out_of_corpus_question_is_refused(pipeline):
    res = pipeline.answer("Quelle est la capitale de l'Australie ?", "agent", log=False)
    assert res["refused"]
    assert res["answer"] == REFUSAL_TEXT
    assert res["references"] == []


def test_requests_are_logged_without_raw_question(pipeline, tmp_path):
    log = tmp_path / "requests.jsonl"
    pipeline.log_path = str(log)
    pipeline.answer("Quel est le plafond de retrait de la carte Classic ?", "agent")
    events = load_events(log)
    assert len(events) == 1
    line = json.dumps(events[0])
    assert "plafond" not in line
    assert events[0]["question_hash"] and events[0]["latency_ms"] >= 0


def test_monitoring_summary(pipeline, tmp_path):
    log = tmp_path / "requests.jsonl"
    pipeline.log_path = str(log)
    pipeline.answer("Quel est le plafond de retrait de la carte Classic ?", "agent")
    pipeline.answer("Quelle est la capitale de l'Australie ?", "agent")
    summary = summarize(load_events(log))
    assert summary["n_requests"] == 2
    assert summary["refusal_rate"] == 0.5
    assert summary["error_rate"] == 0.0
    assert summary["latency_p95_ms"] >= 0
