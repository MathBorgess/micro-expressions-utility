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
    assert obs[0].confidence == round(0.8 * 0.6, 3)


def test_multimodal_bonus_when_objection_and_gaze() -> None:
    signals = [
        SignalEvent(1000, "olhar_desviado", 0.7, meta={"duration_seconds": 4.0}),
    ]
    segments = [Segment(0, 5000, "Cliente", "o preço está caro")]
    conv = ConversationFeatures([], [0], [])
    obs = build_observations(signals, segments, conv)
    assert obs[0].confidence == round(0.7 * 1.0, 3)
    assert "transcrição" in obs[0].modalities
    assert "vídeo" in obs[0].modalities


def test_video_only_gets_lower_modality_bonus() -> None:
    signals = [
        SignalEvent(1000, "olhar_desviado", 0.7, meta={"duration_seconds": 4.0}),
    ]
    segments = [Segment(0, 5000, "Cliente", "sobre o produto")]
    conv = ConversationFeatures([], [], [])
    obs = build_observations(signals, segments, conv)
    assert obs[0].confidence == round(0.7 * 0.6, 3)
