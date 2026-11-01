"""Evaluation : retrieval, references, refus, acces, fuites, latence, cout."""
import json
from pathlib import Path

from src.access import allowed_levels
from src.embeddings import normalize
from src.ingest import load_inventory
from src.monitoring import p95


def load_questions(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def recall_at_k(retrieved_doc_ids, gold_doc_ids):
    return 1.0 if set(retrieved_doc_ids) & set(gold_doc_ids) else 0.0


def _contains_all(text, keywords):
    norm = normalize(text).replace("\xa0", " ")
    return all(normalize(k) in norm for k in keywords)


def evaluate(pipeline, questions, params, root):
    """Rejoue les questions. Retourne (metriques, lignes_detaillees)."""
    versions = {r["doc_id"]: r["version"] for r in load_inventory(params, root)}
    rows = []
    for q in questions:
        res = pipeline.answer(q["question"], q["role"], log=False)
        levels = allowed_levels(q["role"], pipeline.roles)
        violations = [r for r in res["retrieved"] if r["access_level"] not in levels]
        retrieved_docs = [r["doc_id"] for r in res["retrieved"]]
        refs_valid = all(versions.get(r["doc_id"]) == r["version"] for r in res["references"])
        answer_norm = normalize(res["answer"])
        leaks = [f for f in q.get("forbidden", []) if normalize(f) in answer_norm]
        row = {"id": q["id"], "category": q["category"], "role": q["role"],
               "refused": res["refused"], "must_refuse": q.get("must_refuse"),
               "recall": recall_at_k(retrieved_docs, q["gold_docs"]) if q["gold_docs"] else None,
               "keywords_ok": (_contains_all(res["answer"], q["keywords"])
                               if q.get("keywords") and not res["refused"] else None),
               "refs_valid": refs_valid, "access_violations": len(violations),
               "leaks": len(leaks), "flagged": res["flagged"], "top_score": res["top_score"],
               "latency_ms": res["latency_ms"],
               "tokens": res["prompt_tokens"] + res["completion_tokens"], "reason": res["reason"]}
        rows.append(row)

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else 0.0

    answerable = [r for r in rows if r["recall"] is not None]
    refusal_set = [r for r in rows if r["must_refuse"] is not None]
    with_kw = [r for r in rows if r["keywords_ok"] is not None]
    lat = [r["latency_ms"] for r in rows]
    metrics = {
        "n_questions": len(rows),
        "recall_at_k": mean([r["recall"] for r in answerable]),
        "keyword_hit_rate": mean([1.0 if r["keywords_ok"] else 0.0 for r in with_kw]),
        "refusal_accuracy": mean([1.0 if r["refused"] == r["must_refuse"] else 0.0 for r in refusal_set]),
        "reference_validity": mean([1.0 if r["refs_valid"] else 0.0 for r in rows]),
        "access_violations": sum(r["access_violations"] for r in rows),
        "forbidden_leaks": sum(r["leaks"] for r in rows),
        "latency_mean_ms": mean(lat),
        "latency_p95_ms": p95(lat),
        "tokens_mean": mean([r["tokens"] for r in rows]),
        "error_rate": mean([1.0 if r["reason"] == "erreur" else 0.0 for r in rows]),
    }
    return metrics, rows


def check_gates(metrics, gates, baseline=None):
    """Retourne la liste des gates en echec (liste vide = version acceptee)."""
    failures = []
    if metrics["recall_at_k"] < gates["min_recall_at_k"]:
        failures.append("recall_at_k sous le seuil")
    if metrics["refusal_accuracy"] < gates["min_refusal_accuracy"]:
        failures.append("refusal_accuracy sous le seuil")
    if metrics["reference_validity"] < gates["min_reference_validity"]:
        failures.append("references invalides")
    if metrics["access_violations"] > gates["max_access_violations"]:
        failures.append("violation du controle d'acces")
    if metrics["forbidden_leaks"] > gates["max_forbidden_leaks"]:
        failures.append("fuite d'information interdite")
    if metrics["latency_p95_ms"] > gates["max_p95_latency_ms"]:
        failures.append("latence P95 trop elevee")
    if baseline:
        for key in ("recall_at_k", "refusal_accuracy"):
            if metrics[key] < baseline[key] - gates["max_regression"]:
                failures.append(f"regression sur {key}")
    return failures
