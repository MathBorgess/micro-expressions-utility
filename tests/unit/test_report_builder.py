"""Testes da geração validada do relatório (retry com temperatura menor)."""

from app.services.report_builder import generate_validated_report
from mocks.ollama_fake import STATIC_REPORT_MARKDOWN


class _ScriptedGenerator:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = outputs
        self.temperatures: list[float] = []

    def generate(self, prompt: str, *, temperature: float = 0.7) -> str:
        result = self._outputs[len(self.temperatures)]
        self.temperatures.append(temperature)
        return result


def test_valid_on_first_attempt() -> None:
    generator = _ScriptedGenerator([STATIC_REPORT_MARKDOWN])
    output = generate_validated_report(prompt="p", generator=generator)
    assert output.valid is True
    assert output.attempts == 1


def test_retries_once_with_lower_temperature() -> None:
    generator = _ScriptedGenerator(["resposta incompleta", STATIC_REPORT_MARKDOWN])
    output = generate_validated_report(prompt="p", generator=generator)
    assert output.attempts == 2
    assert output.valid is True
    assert generator.temperatures[1] == 0.2
