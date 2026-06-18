"""Testes da telemetria de execução."""

from app.core.telemetry import Telemetry, measure


def test_measure_records_stage() -> None:
    telemetry = Telemetry()
    with measure(telemetry, "extract-audio"):
        pass
    assert len(telemetry.stages) == 1
    assert telemetry.stages[0].stage == "extract-audio"
    assert telemetry.stages[0].duration_ms >= 0


def test_telemetry_to_dict_structure() -> None:
    telemetry = Telemetry()
    telemetry.add("a", 10.0, 1.0)
    telemetry.add("b", 20.0, 2.0)
    data = telemetry.to_dict()
    assert data["total_ms"] == 30.0
    assert [s["stage"] for s in data["stages"]] == ["a", "b"]
