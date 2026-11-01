"""python -m scripts.run_eval --config A [--write-baseline] : evalue une configuration."""
import argparse
import json

from src.build import build
from src.config import ROOT, load_params
from src.evaluation import check_gates, evaluate, load_questions
from src.rag import build_pipeline
from src.tracking import log_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--questions", default="eval/questions.jsonl")
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()

    params = load_params()
    info = build(params, args.config)                      # index reconstruit pour la configuration testee
    name = info["config"]
    pipeline = build_pipeline(params)
    pipeline.log_path = None                               # l'evaluation ne pollue pas le journal de production
    metrics, rows = evaluate(pipeline, load_questions(ROOT / args.questions), params, ROOT)

    out = ROOT / "eval" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"metrics_{name}.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (out / f"details_{name}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if args.write_baseline:
        (ROOT / "eval" / "baseline.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    baseline_path = ROOT / "eval" / "baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else None
    failures = check_gates(metrics, params["quality_gate"], baseline)
    print("Gates :", "OK" if not failures else f"ECHEC -> {failures}")

    if not args.no_mlflow:
        cfg = params["chunking"]["configs"][name]
        log_run(params["mlflow"]["experiment"], f"eval-{name}",
                {"stage": "eval", "config": name, "chunk_size": cfg["size"], "chunk_overlap": cfg["overlap"],
                 "embedder": info["embedder"], "top_k": params["retrieval"]["top_k"],
                 "llm": params["llm"]["provider"], "corpus_version": params["corpus"]["version"]},
                metrics, {"corpus_hash": info["corpus_hash"], "gates": "OK" if not failures else "FAIL"},
                [out / f"metrics_{name}.json", out / f"details_{name}.jsonl", ROOT / "params.yaml"])


if __name__ == "__main__":
    main()
