import json

import pytest

from src.config import ROOT
from src.evaluation import check_gates, evaluate, load_questions

BASELINE = ROOT / "eval" / "baseline.json"


@pytest.fixture(scope="module")
def metrics(pipeline_factory):
    pipeline = pipeline_factory()
    return evaluate(pipeline, load_questions(ROOT / "eval" / "questions.jsonl"), pipeline.params, ROOT)[0]


@pytest.fixture(scope="module")
def pipeline_factory(params, collection, embed):
    from src.llm import ExtractiveLLM
    from src.rag import RagPipeline
    return lambda: RagPipeline(params, collection, embed, ExtractiveLLM())


def test_baseline_file_exists():
    assert BASELINE.exists(), "lancez : python -m scripts.run_eval --config A --write-baseline"


def test_no_regression_against_baseline(metrics, params):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    delta = params["quality_gate"]["max_regression"]
    assert metrics["recall_at_k"] >= baseline["recall_at_k"] - delta
    assert metrics["refusal_accuracy"] >= baseline["refusal_accuracy"] - delta


def test_all_quality_gates_pass(metrics, params):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert check_gates(metrics, params["quality_gate"], baseline) == []


def test_no_access_violation_or_leak(metrics):
    assert metrics["access_violations"] == 0
    assert metrics["forbidden_leaks"] == 0
    assert metrics["reference_validity"] == 1.0
