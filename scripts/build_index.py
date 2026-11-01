"""python -m scripts.build_index --config A : construit l'index et journalise dans MLflow."""
import argparse
import json

from src.build import build
from src.config import ROOT, load_params
from src.tracking import log_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None, help="A ou B (defaut : params.chunking.active)")
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()
    params = load_params()
    info = build(params, args.config)
    print(json.dumps(info, indent=2, ensure_ascii=False))
    if not args.no_mlflow:
        cfg = params["chunking"]["configs"][info["config"]]
        log_run(params["mlflow"]["experiment"], f"build-{info['config']}",
                {"stage": "build", "config": info["config"], "chunk_size": cfg["size"],
                 "chunk_overlap": cfg["overlap"], "embedder": info["embedder"],
                 "corpus_version": params["corpus"]["version"]},
                {"n_documents": info["n_documents"], "n_chunks": info["n_chunks"],
                 "build_time_s": info["build_time_s"]},
                {"corpus_hash": info["corpus_hash"]},
                [ROOT / "params.yaml"])


if __name__ == "__main__":
    main()
