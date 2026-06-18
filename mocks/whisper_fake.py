"""Dublê do Faster-Whisper: devolve segmentos fixos contendo 'produto' e 'preço'."""

FAKE_SEGMENTS: list[dict[str, str]] = [
    {
        "start_time": "00:00:00",
        "end_time": "00:00:05",
        "speaker": "Cliente",
        "text": (
            "Gostei do produto, mas precisamos discutir as condições de preço na próxima semana."
        ),
    },
]


def transcribe(audio_path: str = "") -> list[dict[str, str]]:
    """Simula a transcrição, ignorando o áudio e devolvendo segmentos predefinidos."""
    return FAKE_SEGMENTS
