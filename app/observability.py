"""Logs estruturados em JSON no stdout (observabilidade — Bloco 15).

Cada linha contém as chaves obrigatórias: timestamp, level, job_id, component, message.
Use ``logger.info(msg, extra={"job_id": ..., "component": ...})`` para rastrear a jornada.
"""

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "job_id": getattr(record, "job_id", None),
            "component": getattr(record, "component", record.name),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
