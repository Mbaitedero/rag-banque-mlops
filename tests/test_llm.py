from unittest.mock import Mock

from src.llm import GroqLLM


def test_groq_uses_bearer_api_key(monkeypatch):
    api_key = "test-api-key"
    monkeypatch.setenv("GROQ_API_KEY", api_key)
    response = Mock()
    response.json.return_value = {
        "choices": [{"message": {"content": "Réponse test"}}],
        "usage": {"prompt_tokens": 2, "completion_tokens": 3},
    }
    post = Mock(return_value=response)
    monkeypatch.setattr("src.llm.requests.post", post)

    result = GroqLLM("model", 0.0, 10)("question", [])

    assert post.call_args.kwargs["headers"]["Authorization"] == f"Bearer {api_key}"
    assert result == {
        "text": "Réponse test",
        "prompt_tokens": 2,
        "completion_tokens": 3,
    }
