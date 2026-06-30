from app.core.conversation import extract_conversation_features
from app.core.types import Segment


def test_detects_gap_between_segments() -> None:
    segments = [
        Segment(0, 2000, "Vendedor", "Qual o orçamento?"),
        Segment(5000, 7000, "Cliente", "Preciso pensar."),
    ]
    features = extract_conversation_features(segments)
    assert 3000 in features.response_gaps_ms


def test_verbal_objection_keyword() -> None:
    segments = [Segment(0, 3000, "Cliente", "O preço está alto.")]
    features = extract_conversation_features(segments)
    assert 0 in features.verbal_objection_segments


def test_verbal_agreement() -> None:
    segments = [Segment(0, 2000, "Cliente", "Faz sentido, concordo.")]
    features = extract_conversation_features(segments)
    assert 0 in features.verbal_agreement_segments
