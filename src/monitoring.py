"""Monitoring minimal : agrege le journal JSON des requetes."""
import argparse
import json
from pathlib import Path


def p95(values):
    values = sorted(values)
    return values[int(0.95 * (len(values) - 1))] if values else 0.0


def load_events(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize(events):
    n = len(events)
    if n == 0:
        return {"n_requests": 0}
    lat = [e["latency_ms"] for e in events]
    return {
        "n_requests": n,
        "error_rate": sum(1 for e in events if e.get("error")) / n,
        "refusal_rate": sum(1 for e in events if e.get("refused")) / n,
        "latency_mean_ms": sum(lat) / n,
        "latency_p95_ms": p95(lat),
        "tokens_mean": sum(e.get("prompt_tokens", 0) + e.get("completion_tokens", 0) for e in events) / n,
        "top_score_mean": sum(e.get("top_score", 0.0) for e in events) / n,
        "flagged_total": sum(e.get("flagged", 0) for e in events),
    }


def main():
    parser = argparse.ArgumentParser(description="Resume du journal des requetes")
    parser.add_argument("--log", default="logs/requests.jsonl")
    args = parser.parse_args()
    for key, value in summarize(load_events(args.log)).items():
        print(f"{key:>18} : {value:.3f}" if isinstance(value, float) else f"{key:>18} : {value}")


if __name__ == "__main__":
    main()
