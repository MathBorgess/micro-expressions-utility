from app.core.observations import build_observations
from app.core.types import ConversationFeatures, Segment, SignalEvent


def test_gaze_away_produces_observation_not_emotion() -> None:
    signals = [
        SignalEvent(
            timestamp_ms=5000,
            signal_type="olhar_desviado",
            confidence=0.8,
            meta={"duration_seconds": 3.5},
        )
    ]
    segments = [Segment(0, 10000, "Cliente", "sobre o preço")]
    conv = ConversationFeatures([], [], [])
    obs = build_observations(signals, segments, conv)
    assert len(obs) >= 1
    assert "medo" not in obs[0].observation.lower()
    assert "rejeit" not in obs[0].observation.lower()
    assert len(obs[0].hypotheses) >= 2
    assert obs[0].confidence <= 0.8


def test_multimodal_boost_when_objection_and_gaze() -> None:
    signals = [
        SignalEvent(1000, "olhar_desviado", 0.7, meta={"duration_seconds": 4.0}),
    ]
    segments = [Segment(0, 5000, "Cliente", "o preço está caro")]
    conv = ConversationFeatures([], [0], [])
    obs = build_observations(signals, segments, conv)
    assert obs[0].confidence > 0.7
    assert "transcrição" in obs[0].modalities or "vídeo" in obs[0].modalities
