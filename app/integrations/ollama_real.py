"""Geração de relatório e sumarização reais via Ollama local (HTTP)."""

from app.services.errors import TemporaryError

_SUMMARY_INSTRUCTION = (
    "Resuma o trecho de conversa abaixo em poucas frases, em português, PRESERVANDO "
    "obrigatoriamente valores monetários, prazos de fechamento e objeções explícitas:\n\n"
)


def _call_ollama(base_url: str, model: str, prompt: str, temperature: float) -> str:
    import httpx

    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=120.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TemporaryError(f"falha ao chamar o Ollama: {exc}") from exc
    return str(response.json().get("response", ""))


class OllamaReportGenerator:
    def __init__(self, base_url: str, model: str = "llama3:8b") -> None:
        self._base_url = base_url
        self._model = model

    def generate(self, prompt: str, *, temperature: float = 0.7) -> str:
        return _call_ollama(self._base_url, self._model, prompt, temperature)


class OllamaSummarizer:
    def __init__(self, base_url: str, model: str = "llama3:8b") -> None:
        self._base_url = base_url
        self._model = model

    def summarize(self, text: str) -> str:
        if not text.strip():
            return ""
        return _call_ollama(self._base_url, self._model, f"{_SUMMARY_INSTRUCTION}{text}", 0.2)
