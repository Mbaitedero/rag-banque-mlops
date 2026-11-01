"""Interface en ligne de commande : python -m src.app --role agent --question "..." """
import argparse
import json

from src.config import load_params
from src.rag import build_pipeline


def main():
    parser = argparse.ArgumentParser(description="Assistant documentaire bancaire (RAG)")
    parser.add_argument("--role", default="agent", help="agent ou conformite")
    parser.add_argument("--question", required=True)
    parser.add_argument("--config", default=None, help="fichier params.yaml alternatif")
    args = parser.parse_args()
    pipeline = build_pipeline(load_params(args.config))
    res = pipeline.answer(args.question, args.role)
    print(json.dumps({k: res[k] for k in ("answer", "references", "refused", "reason", "latency_ms")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
