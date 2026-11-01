"""python -m scripts.promote --config B : promeut la configuration si tous les gates passent."""
import argparse
import datetime
import json
import sys

from src.config import ROOT, load_params
from src.evaluation import check_gates
from src.ingest import corpus_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--approve", action="store_true", help="simule l'approbation humaine")
    args = parser.parse_args()
    params = load_params()
    metrics_path = ROOT / "eval" / "results" / f"metrics_{args.config}.json"
    if not metrics_path.exists():
        sys.exit(f"Aucune metrique pour la configuration {args.config} : lancez scripts.run_eval d'abord.")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    baseline_path = ROOT / "eval" / "baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else None
    failures = check_gates(metrics, params["quality_gate"], baseline)
    if failures:
        sys.exit(f"Promotion refusee : {failures}")
    print(f"Gates OK pour la configuration {args.config}.")
    if not args.approve:
        print("Aucune approbation : la configuration reste candidate.")
        return
    champion = {"config": args.config, "metrics": metrics, "corpus_hash": corpus_hash(params, ROOT),
                "corpus_version": params["corpus"]["version"], "approval_status": "approved",
                "date": datetime.datetime.now(datetime.UTC).isoformat()}
    (ROOT / "eval" / "results" / "champion.json").write_text(json.dumps(champion, indent=2), encoding="utf-8")
    print(f"champion -> configuration {args.config}")


if __name__ == "__main__":
    main()
