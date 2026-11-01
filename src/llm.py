"""Abstraction LLM : extractive (sans API), Groq (API autorisee) ou Ollama (local)."""
import os
import re

import requests

from src.embeddings import tokenize
from src.prompts import build_prompt

REFUSAL_TEXT = "Information insuffisante dans les documents autorises."


class ExtractiveLLM:
    """Reponse deterministe : phrases du contexte les plus proches de la question.
    Utile pour la CI et pour mesurer le retrieval sans dependre d'une API."""
    name = "extractive"

    def __call__(self, question, passages):
        q = set(tokenize(question))
        scored = []
        for rank, p in enumerate(passages[:2]):
            for sent in re.split(r"(?<=[.!?])\s+", p["text"]):
                sent = sent.strip()
                if not sent or sent.endswith("?"):
                    continue
                overlap = len(q & set(tokenize(sent)))
                scored.append((overlap, -rank, sent))
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        best = [s for o, _, s in scored[:2] if o > 0]
        text = " ".join(best) if best else REFUSAL_TEXT
        return {"text": text, "prompt_tokens": 0, "completion_tokens": len(text.split())}


class GroqLLM:
    name = "groq"

    def __init__(self, model, temperature, timeout):
        self.model, self.temperature, self.timeout = model, temperature, timeout

    def __call__(self, question, passages):
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY manquante (voir .env.example)")
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": self.model, "temperature": self.temperature,
                  "messages": [{"role": "user", "content": build_prompt(question, passages)}]},
            timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        return {"text": data["choices"][0]["message"]["content"].strip(),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0)}


class OllamaLLM:
    name = "ollama"

    def __init__(self, model, temperature, timeout, url):
        self.model, self.temperature, self.timeout, self.url = model, temperature, timeout, url

    def __call__(self, question, passages):
        resp = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": build_prompt(question, passages), "stream": False,
                  "options": {"temperature": self.temperature}},
            timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return {"text": data["response"].strip(),
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0)}


def get_llm(params):
    cfg = params["llm"]
    if cfg["provider"] == "extractive":
        return ExtractiveLLM()
    if cfg["provider"] == "groq":
        return GroqLLM(cfg["model"], cfg["temperature"], cfg["timeout_s"])
    if cfg["provider"] == "ollama":
        return OllamaLLM(cfg["model"], cfg["temperature"], cfg["timeout_s"], cfg["ollama_url"])
    raise ValueError(f"provider LLM inconnu : {cfg['provider']}")
