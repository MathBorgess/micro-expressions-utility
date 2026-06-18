"""Geração do relatório com validação estrutural e retry único com temperatura menor.

Meta do Harness: < 5% de falhas estruturais. Se a 1ª resposta não tiver os cabeçalhos
obrigatórios, refaz uma única vez com ``temperature=0.2`` (mais determinística).
"""

from dataclasses import dataclass

from app.core.report import validate_report
from app.services.interfaces import ReportGenerator

RETRY_TEMPERATURE = 0.2


@dataclass
class ReportOutput:
    markdown: str
    valid: bool
    attempts: int


def generate_validated_report(
    *, prompt: str, generator: ReportGenerator, retry_temperature: float = RETRY_TEMPERATURE
) -> ReportOutput:
    markdown = generator.generate(prompt)
    if validate_report(markdown):
        return ReportOutput(markdown=markdown, valid=True, attempts=1)
    retried = generator.generate(prompt, temperature=retry_temperature)
    return ReportOutput(markdown=retried, valid=validate_report(retried), attempts=2)
