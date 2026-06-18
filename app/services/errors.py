"""Erros do pipeline: distinguem falhas temporárias (retentáveis) de definitivas."""


class PipelineError(Exception):
    """Erro base do pipeline."""


class TemporaryError(PipelineError):
    """Falha possivelmente transitória (rede/Ollama, timeout leve) — elegível a retry."""


class DefinitiveError(PipelineError):
    """Falha definitiva (vídeo corrompido, codec ausente, disco cheio) — sem retry."""
