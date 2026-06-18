"""Testes do formatador de logs JSON estruturados."""

import json
import logging

from app.observability import JsonFormatter


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="pipeline.mediapipe",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Processing frame %d",
        args=(240,),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formatter_emits_required_keys() -> None:
    formatted = JsonFormatter().format(_record(job_id="412", component="pipeline.mediapipe"))
    payload = json.loads(formatted)
    assert set(payload) >= {"timestamp", "level", "job_id", "component", "message"}
    assert payload["job_id"] == "412"
    assert payload["message"] == "Processing frame 240"


def test_formatter_defaults_component_to_logger_name() -> None:
    payload = json.loads(JsonFormatter().format(_record()))
    assert payload["component"] == "pipeline.mediapipe"
    assert payload["job_id"] is None
