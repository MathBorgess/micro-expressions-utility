"""Telemetria de execução: tempo por estágio (perf_counter) e CPU (psutil)."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

try:  # psutil é opcional; ausência não deve quebrar o pipeline.
    import psutil

    _PROCESS: Any = psutil.Process()
except Exception:  # pragma: no cover - caminho de ambiente sem psutil
    _PROCESS = None


@dataclass
class StageTelemetry:
    stage: str
    duration_ms: float
    cpu_percent: float


@dataclass
class Telemetry:
    """Acumula medições por estágio para persistir na coluna ``jobs.telemetry``."""

    stages: list[StageTelemetry] = field(default_factory=list)

    def add(self, stage: str, duration_ms: float, cpu_percent: float) -> None:
        self.stages.append(StageTelemetry(stage, round(duration_ms, 2), round(cpu_percent, 2)))

    def total_ms(self) -> float:
        return round(sum(s.duration_ms for s in self.stages), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_ms": self.total_ms(),
            "stages": [
                {"stage": s.stage, "duration_ms": s.duration_ms, "cpu_percent": s.cpu_percent}
                for s in self.stages
            ],
        }


@contextmanager
def measure(telemetry: Telemetry, stage: str) -> Iterator[None]:
    """Mede duração e uso de CPU do bloco, registrando em ``telemetry``."""
    if _PROCESS is not None:
        _PROCESS.cpu_percent(None)  # zera a janela de medição
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        cpu = float(_PROCESS.cpu_percent(None)) if _PROCESS is not None else 0.0
        telemetry.add(stage, duration_ms, cpu)
