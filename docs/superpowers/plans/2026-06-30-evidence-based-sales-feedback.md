# Evidence-Based Sales Feedback — Implementation Plan (Fase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir inferências emocionais por observações comportamentais evidenciadas, com confiança calibrada heuristicamente, novo prompt/relatório e percepção facial melhorada — sem novas dependências pip.

**Architecture:** Camada `observations` entre `signals`/`conversation` e o LLM; `face_quality` filtra frames ruins; MediaPipe usa landmarks de íris; `conversation` extrai gaps e flags verbais da transcrição; prompt e validação de relatório exigem estrutura evidence-first e bloqueiam frases de leitura mental.

**Tech Stack:** Python 3.12, MediaPipe Face Mesh, OpenCV (já na allowlist), numpy, Ollama, pytest — zero deps novas.

**Spec:** `docs/superpowers/specs/2026-06-30-evidence-based-sales-feedback-design.md`

---

## File Map

| Arquivo | Responsabilidade |
|---------|------------------|
| `app/core/face_quality.py` | Score 0–1 por frame (blur, tamanho face, tracking) |
| `app/core/conversation.py` | Gaps de silêncio, flags verbais, latência de resposta |
| `app/core/observations.py` | Pacotes evidência + hipóteses + confiança a partir de sinais |
| `app/core/types.py` | `FrameMetrics` enriquecido, `BehavioralObservation`, `ConversationFeatures` |
| `app/core/signals.py` | Respeitar `min_quality` ao detectar eventos |
| `app/integrations/mediapipe_real.py` | Íris, pose proxy, quality por frame |
| `app/core/prompt.py` | SYSTEM_PROMPT evidence-first + builders |
| `app/core/report.py` | Novos headers + `FORBIDDEN_PHRASES` |
| `app/core/timeline.py` | Anexar observations à timeline |
| `app/services/context.py` | Incluir bloco de observations no prompt |
| `mocks/ollama_fake.py` | Relatório estático compatível com novos headers |
| `tests/unit/test_*.py` | Cobertura TDD por módulo |
| `tests/e2e/test_pipeline_e2e.py` | Atualizar asserções de headers |

---

### Task 1: Face Quality Scoring

**Files:**
- Create: `app/core/face_quality.py`
- Create: `tests/unit/test_face_quality.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_face_quality.py
"""Testes de pontuação de qualidade facial por frame."""

import numpy as np

from app.core.face_quality import score_frame_quality


def test_high_quality_sharp_large_face() -> None:
    # Gradiente forte simula frame nítido
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    frame[100:300, 200:440] = np.random.randint(0, 255, (200, 240, 3), dtype=np.uint8)
    result = score_frame_quality(
        frame_bgr=frame,
        face_bbox=(200, 100, 440, 300),
        landmark_visibility=1.0,
    )
    assert 0.0 <= result <= 1.0
    assert result >= 0.4


def test_low_quality_tiny_face() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = score_frame_quality(
        frame_bgr=frame,
        face_bbox=(300, 220, 320, 240),
        landmark_visibility=0.5,
    )
    assert result < 0.5


def test_blurry_frame_lower_than_sharp() -> None:
    sharp = np.random.randint(0, 255, (120, 120, 3), dtype=np.uint8)
    blurry = np.full((120, 120, 3), 128, dtype=np.uint8)
    bbox = (10, 10, 110, 110)
    assert score_frame_quality(sharp, bbox, 1.0) > score_frame_quality(blurry, bbox, 1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_face_quality.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.face_quality'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/core/face_quality.py
"""Pontuação de qualidade de frame facial (0..1) para filtrar ruído de percepção."""

from typing import Sequence

import cv2
import numpy as np

MIN_FACE_AREA_RATIO = 0.02  # face deve ocupar >=2% do frame
BLUR_VAR_LOW = 50.0
BLUR_VAR_HIGH = 400.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _blur_score(roi: np.ndarray) -> float:
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if variance <= BLUR_VAR_LOW:
        return 0.0
    if variance >= BLUR_VAR_HIGH:
        return 1.0
    return (variance - BLUR_VAR_LOW) / (BLUR_VAR_HIGH - BLUR_VAR_LOW)


def _size_score(bbox: Sequence[int], frame_shape: tuple[int, ...]) -> float:
    x1, y1, x2, y2 = bbox
    face_area = max(0, x2 - x1) * max(0, y2 - y1)
    frame_area = frame_shape[0] * frame_shape[1]
    if frame_area == 0:
        return 0.0
    ratio = face_area / frame_area
    if ratio < MIN_FACE_AREA_RATIO:
        return ratio / MIN_FACE_AREA_RATIO * 0.5
    return _clamp(ratio / 0.15)


def score_frame_quality(
    *,
    frame_bgr: np.ndarray,
    face_bbox: tuple[int, int, int, int],
    landmark_visibility: float,
) -> float:
    """Combina nitidez, tamanho relativo da face e visibilidade dos landmarks."""
    x1, y1, x2, y2 = face_bbox
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    roi = frame_bgr[y1:y2, x1:x2]
    blur = _blur_score(roi)
    size = _size_score((x1, y1, x2, y2), (h, w))
    visibility = _clamp(landmark_visibility)
    return round(_clamp(blur * 0.4 + size * 0.35 + visibility * 0.25), 3)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_face_quality.py -v`  
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/core/face_quality.py tests/unit/test_face_quality.py
git commit -m "feat: add per-frame face quality scoring"
```

---

### Task 2: Enrich FrameMetrics

**Files:**
- Modify: `app/core/types.py`
- Modify: `tests/unit/test_signals.py` (se necessário defaults)
- Test: `tests/unit/test_types.py` (criar)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_types.py
"""Testes dos tipos de domínio enriquecidos."""

from app.core.types import FrameMetrics


def test_frame_metrics_optional_fields_default() -> None:
    m = FrameMetrics(
        timestamp_ms=0,
        looking_at_screen=True,
        face_size_ratio=0.1,
        face_center_x=0.5,
        face_center_y=0.5,
    )
    assert m.quality_score == 1.0
    assert m.head_yaw_deg == 0.0
    assert m.gaze_offset_x == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_types.py -v`  
Expected: FAIL — `FrameMetrics` sem campos novos

- [ ] **Step 3: Write minimal implementation**

Em `app/core/types.py`, estender `FrameMetrics`:

```python
@dataclass
class FrameMetrics:
    timestamp_ms: int
    looking_at_screen: bool
    face_size_ratio: float
    face_center_x: float
    face_center_y: float
    confidence: float = 1.0
    quality_score: float = 1.0
    head_yaw_deg: float = 0.0
    head_pitch_deg: float = 0.0
    gaze_offset_x: float = 0.0
    gaze_offset_y: float = 0.0
```

Adicionar também:

```python
@dataclass
class BehavioralObservation:
    timestamp_ms: int
    observation: str
    evidence: dict[str, object]
    hypotheses: list[str]
    confidence: float
    modalities: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp_ms": self.timestamp_ms,
            "observation": self.observation,
            "evidence": self.evidence,
            "hypotheses": self.hypotheses,
            "confidence": self.confidence,
            "modalities": self.modalities,
        }


@dataclass
class ConversationFeatures:
    response_gaps_ms: list[int]
    verbal_objection_segments: list[int]
    verbal_agreement_segments: list[int]

    def to_dict(self) -> dict[str, object]:
        return {
            "response_gaps_ms": self.response_gaps_ms,
            "verbal_objection_segments": self.verbal_objection_segments,
            "verbal_agreement_segments": self.verbal_agreement_segments,
        }
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_types.py tests/unit/test_signals.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/types.py tests/unit/test_types.py
git commit -m "feat: enrich FrameMetrics and add observation types"
```

---

### Task 3: Conversation Features from Transcript

**Files:**
- Create: `app/core/conversation.py`
- Create: `tests/unit/test_conversation.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_conversation.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_conversation.py -v`  
Expected: FAIL `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# app/core/conversation.py
"""Features conversacionais derivadas só da transcrição (sem nova dep)."""

import re

from app.core.types import ConversationFeatures, Segment

GAP_THRESHOLD_MS = 1500
_OBJECTION_RE = re.compile(
    r"(caro|pre[çc]o|or[çc]amento|concorrente|n[aã]o\s+sei|dif[ií]cil)", re.IGNORECASE
)
_AGREEMENT_RE = re.compile(
    r"(concordo|faz sentido|interessante|gostei|perfeito|ok\b)", re.IGNORECASE
)


def extract_conversation_features(segments: list[Segment]) -> ConversationFeatures:
    sorted_segments = sorted(segments, key=lambda s: s.start_ms)
    gaps: list[int] = []
    objections: list[int] = []
    agreements: list[int] = []

    for index, segment in enumerate(sorted_segments):
        if _OBJECTION_RE.search(segment.text):
            objections.append(index)
        if _AGREEMENT_RE.search(segment.text):
            agreements.append(index)
        if index == 0:
            continue
        prev = sorted_segments[index - 1]
        gap = segment.start_ms - prev.end_ms
        if gap >= GAP_THRESHOLD_MS:
            gaps.append(gap)

    return ConversationFeatures(
        response_gaps_ms=gaps,
        verbal_objection_segments=objections,
        verbal_agreement_segments=agreements,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_conversation.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/conversation.py tests/unit/test_conversation.py
git commit -m "feat: extract conversation features from transcript"
```

---

### Task 4: Behavioral Observations Builder

**Files:**
- Create: `app/core/observations.py`
- Create: `tests/unit/test_observations.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_observations.py
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
    conv = ConversationFeatures([], [0], [])
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_observations.py -v`  
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/core/observations.py
"""Converte sinais brutos em observações evidenciadas com hipóteses alternativas."""

from app.core.timeline import signals_in_segment
from app.core.types import BehavioralObservation, ConversationFeatures, Segment, SignalEvent

_SIGNAL_COPY: dict[str, str] = {
    "olhar_desviado": "Contato visual reduzido por período prolongado",
    "afastamento_da_tela": "Afastamento físico em relação à câmera",
    "aceno_cabeca_positivo": "Movimento rítmico de cabeça (vertical)",
    "aceno_cabeca_negativo": "Movimento rítmico de cabeça (horizontal)",
}

_GAZE_HYPOTHESES = [
    "Processamento cognitivo ou reflexão",
    "Desconforto ou discordância possível (não conclusivo)",
    "Distração ambiental ou fadiga",
]
_DEFAULT_HYPOTHESES = [
    "Mudança postural sem significado afetivo específico",
    "Resposta a estímulo externo à conversa",
]
_MULTIMODAL_BONUS = 0.15
_MAX_CONFIDENCE = 0.95


def _hypotheses_for(signal_type: str) -> list[str]:
    if signal_type == "olhar_desviado":
        return list(_GAZE_HYPOTHESES)
    return list(_DEFAULT_HYPOTHESES)


def _modalities_for(
  segment_index: int, conv: ConversationFeatures, has_video: bool
) -> list[str]:
    mods: list[str] = []
    if has_video:
        mods.append("vídeo")
    if segment_index in conv.verbal_objection_segments:
        mods.append("transcrição")
    if segment_index in conv.verbal_agreement_segments:
        mods.append("transcrição")
    return mods


def build_observations(
    signals: list[SignalEvent],
    segments: list[Segment],
    conversation: ConversationFeatures,
) -> list[BehavioralObservation]:
    observations: list[BehavioralObservation] = []
    sorted_segments = sorted(segments, key=lambda s: s.start_ms)

    for index, segment in enumerate(sorted_segments):
        matched = signals_in_segment(segment, signals)
        for signal in matched:
            base_conf = min(signal.confidence, 1.0)
            modalities = _modalities_for(index, conversation, has_video=True)
            confidence = base_conf
            if "transcrição" in modalities and signal.signal_type in (
                "olhar_desviado",
                "afastamento_da_tela",
            ):
                confidence = min(_MAX_CONFIDENCE, base_conf + _MULTIMODAL_BONUS)

            observations.append(
                BehavioralObservation(
                    timestamp_ms=signal.timestamp_ms,
                    observation=_SIGNAL_COPY.get(signal.signal_type, signal.signal_type),
                    evidence={
                        "signal_type": signal.signal_type,
                        "segment_text": segment.text,
                        "meta": signal.meta,
                        "speaker": segment.speaker,
                    },
                    hypotheses=_hypotheses_for(signal.signal_type),
                    confidence=round(confidence, 3),
                    modalities=modalities,
                )
            )
    observations.sort(key=lambda o: o.timestamp_ms)
    return observations
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_observations.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/observations.py tests/unit/test_observations.py
git commit -m "feat: build evidence-based behavioral observations"
```

---

### Task 5: Filter Low-Quality Frames in Signals

**Files:**
- Modify: `app/core/signals.py`
- Modify: `tests/unit/test_signals.py`

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/unit/test_signals.py`:

```python
from app.core.signals import detect_signals, MIN_FRAME_QUALITY


def test_detect_signals_skips_low_quality_frames() -> None:
    frames = [
        FrameMetrics(0, False, 0.1, 0.5, 0.5, quality_score=0.1),
        FrameMetrics(100, False, 0.1, 0.5, 0.5, quality_score=0.1),
        FrameMetrics(4000, False, 0.1, 0.5, 0.5, quality_score=0.9),
    ]
    events = detect_signals(frames, min_quality=MIN_FRAME_QUALITY)
    assert events == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_signals.py::test_detect_signals_skips_low_quality_frames -v`  
Expected: FAIL — `detect_signals()` unexpected keyword `min_quality`

- [ ] **Step 3: Write minimal implementation**

Em `app/core/signals.py`:

```python
MIN_FRAME_QUALITY = 0.35

def _quality_frames(frames: list[FrameMetrics], min_quality: float) -> list[FrameMetrics]:
    return [f for f in frames if f.quality_score >= min_quality]


def detect_signals(
    frames: list[FrameMetrics], *, min_quality: float = MIN_FRAME_QUALITY
) -> list[SignalEvent]:
    filtered = _quality_frames(frames, min_quality)
    events: list[SignalEvent] = []
    events.extend(detect_gaze_away(filtered))
    events.extend(detect_withdrawal(filtered))
    events.extend(detect_head_gestures(filtered))
    events.sort(key=lambda event: event.timestamp_ms)
    return events
```

- [ ] **Step 4: Run all signal tests**

Run: `uv run pytest tests/unit/test_signals.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/signals.py tests/unit/test_signals.py
git commit -m "feat: filter signal detection by frame quality"
```

---

### Task 6: Improve MediaPipe Metrics (Iris + Quality)

**Files:**
- Modify: `app/integrations/mediapipe_real.py`

- [ ] **Step 1: Write integration-style unit test with monkeypatch**

Criar `tests/unit/test_mediapipe_metrics.py` que testa `_to_metrics` isoladamente via objeto fake de landmarks (sem carregar vídeo real).

```python
# tests/unit/test_mediapipe_metrics.py
from types import SimpleNamespace

from app.integrations.mediapipe_real import MediaPipeFaceAnalyzer


class _Pt:
    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x, self.y, self.z = x, y, z


def test_to_metrics_uses_variable_confidence() -> None:
    analyzer = MediaPipeFaceAnalyzer()
    # 478 landmarks fake: índices usados pelo analyzer
    points = [_Pt(0.5, 0.5) for _ in range(478)]
    points[1] = _Pt(0.52, 0.48)   # nose
    points[33] = _Pt(0.40, 0.45)  # left eye
    points[263] = _Pt(0.60, 0.45) # right eye
    points[468] = _Pt(0.42, 0.46) # left iris
    points[473] = _Pt(0.58, 0.46) # right iris
    result = SimpleNamespace(multi_face_landmarks=[SimpleNamespace(landmark=points)])
    metric = analyzer._to_metrics(result, timestamp_ms=1000, frame_bgr=None)
    assert metric is not None
    assert metric.confidence <= 1.0
    assert hasattr(metric, "gaze_offset_x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_mediapipe_metrics.py -v`  
Expected: FAIL

- [ ] **Step 3: Update mediapipe_real.py**

Alterar `analyze` para passar `frame` a `_to_metrics` e calcular:
- `gaze_offset_x/y` a partir do centro das írisas vs centro dos olhos
- `looking_at_screen` se `abs(gaze_offset_x) < 0.08` e `abs(head_yaw_deg) < 15`
- `head_yaw_deg` aproximado por assimetria olhos-nariz
- `quality_score` via `score_frame_quality` quando `frame_bgr` disponível
- `confidence` = `quality_score * tracking_stability` (default quality se sem frame)

Assinatura: `_to_metrics(self, result, timestamp_ms, frame_bgr=None) -> FrameMetrics | None`

- [ ] **Step 4: Run test**

Run: `uv run pytest tests/unit/test_mediapipe_metrics.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/integrations/mediapipe_real.py tests/unit/test_mediapipe_metrics.py
git commit -m "feat: improve MediaPipe gaze and per-frame confidence"
```

---

### Task 7: Evidence-First Prompt

**Files:**
- Modify: `app/core/prompt.py`
- Modify: `tests/unit/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
# adicionar em tests/unit/test_prompt.py
from app.core.prompt import SYSTEM_PROMPT, build_observations_text, FORBIDDEN_EXAMPLE_PHRASES


def test_system_prompt_forbids_mind_reading() -> None:
    assert "NUNCA" in SYSTEM_PROMPT or "nunca" in SYSTEM_PROMPT.lower()
    assert "emoç" in SYSTEM_PROMPT.lower() or "emoções" in SYSTEM_PROMPT.lower()


def test_build_observations_text_includes_hypotheses() -> None:
    from app.core.types import BehavioralObservation

    obs = [
        BehavioralObservation(
            1000,
            "Contato visual reduzido",
            {"signal_type": "olhar_desviado"},
            ["hipótese A", "hipótese B"],
            0.6,
            ["vídeo"],
        )
    ]
    text = build_observations_text(obs)
    assert "hipótese A" in text
    assert "0.6" in text or "0.60" in text


def test_forbidden_phrases_list_not_empty() -> None:
    assert "perdeu confiança" in FORBIDDEN_EXAMPLE_PHRASES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_prompt.py -v`  
Expected: FAIL

- [ ] **Step 3: Rewrite prompt.py**

Substituir `SYSTEM_PROMPT` e adicionar:

```python
FORBIDDEN_EXAMPLE_PHRASES = (
    "perdeu confiança",
    "ficou com medo",
    "odiou",
    "rejeitou o produto",
    "não gostou",
)

SYSTEM_PROMPT = (
    "Você é um analista de comunicação comercial. "
    "NUNCA afirme emoções, intenções internas ou atitudes sem evidência multimodal explícita.\n"
    "Separe: (1) Observação mensurável (2) Hipótese com alternativas (3) Recomendação.\n"
    "Use 'pode indicar' — nunca certeza.\n"
    "Cite timestamps [HH:MM:SS] e modalidade (vídeo/transcrição/silêncio).\n"
    "Estrutura OBRIGATÓRIA:\n"
    "# Relatório de Análise Comercial\n"
    "## 1. Comportamentos Observados\n"
    "## 2. Linha do Tempo\n"
    "## 3. Mudanças de Comportamento\n"
    "## 4. Hipóteses Interpretativas\n"
    "## 5. Contexto Conversacional\n"
    "## 6. Confiança e Limitações\n"
    "## 7. Perguntas de Follow-up Sugeridas\n"
    "## 8. Oportunidades e Coaching\n"
)

def build_observations_text(observations: list[BehavioralObservation]) -> str:
    lines: list[str] = []
    for ob in observations:
        hyps = "; ".join(ob.hypotheses)
        mods = ", ".join(ob.modalities)
        lines.append(
            f"[{ob.timestamp_ms}ms] {ob.observation} | conf={ob.confidence} | "
            f"modalidades={mods} | hipóteses: {hyps}"
        )
    return "\n".join(lines)

def build_conversation_text(features: ConversationFeatures) -> str:
    return (
        f"Gaps de resposta (ms): {features.response_gaps_ms}\n"
        f"Segmentos com objeção verbal: {features.verbal_objection_segments}\n"
        f"Segmentos com concordância verbal: {features.verbal_agreement_segments}"
    )

def build_prompt(
    transcript_text: str,
    observations_text: str,
    conversation_text: str,
) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"## Transcrição\n{transcript_text}\n\n"
        f"## Observações comportamentais (pré-processadas)\n{observations_text}\n\n"
        f"## Features conversacionais\n{conversation_text}\n"
    )
```

Atualizar imports e remover `build_signals_text` do fluxo principal (manter função deprecated ou redirecionar por compat).

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_prompt.py -v`  
Expected: PASS após ajustar testes antigos que usavam `build_prompt("T","S")`

- [ ] **Step 5: Commit**

```bash
git add app/core/prompt.py tests/unit/test_prompt.py
git commit -m "feat: evidence-first LLM prompt template"
```

---

### Task 8: Report Validation + Forbidden Phrases

**Files:**
- Modify: `app/core/report.py`
- Modify: `tests/unit/test_report.py`
- Modify: `app/services/report_builder.py`

- [ ] **Step 1: Write the failing test**

```python
# adicionar em tests/unit/test_report.py
from app.core.prompt import FORBIDDEN_EXAMPLE_PHRASES
from app.core.report import contains_forbidden_phrases, validate_report


def test_forbidden_phrases_detected() -> None:
    bad = "# Relatório\n## 1. Comportamentos Observados\nO cliente perdeu confiança."
    assert contains_forbidden_phrases(bad, FORBIDDEN_EXAMPLE_PHRASES)


def test_new_headers_required() -> None:
    old_style = "# Relatório de Análise Comercial\n## 1. Resumo Executivo\n"
    assert not validate_report(old_style)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_report.py -v`  
Expected: FAIL

- [ ] **Step 3: Update report.py**

```python
REQUIRED_HEADERS: tuple[tuple[str, str], ...] = (
    (r"#\s*Relatório de Análise Comercial", "# Relatório de Análise Comercial"),
    (r"##\s*1\.\s*Comportamentos Observados", "## 1. Comportamentos Observados"),
    (r"##\s*2\.\s*Linha do Tempo", "## 2. Linha do Tempo"),
    (r"##\s*3\.\s*Mudanças de Comportamento", "## 3. Mudanças de Comportamento"),
    (r"##\s*4\.\s*Hipóteses Interpretativas", "## 4. Hipóteses Interpretativas"),
    (r"##\s*5\.\s*Contexto Conversacional", "## 5. Contexto Conversacional"),
    (r"##\s*6\.\s*Confiança e Limitações", "## 6. Confiança e Limitações"),
    (r"##\s*7\.\s*Perguntas de Follow-up Sugeridas", "## 7. Perguntas de Follow-up Sugeridas"),
    (r"##\s*8\.\s*Oportunidades e Coaching", "## 8. Oportunidades e Coaching"),
)


def contains_forbidden_phrases(markdown: str, phrases: tuple[str, ...]) -> bool:
    lowered = markdown.lower()
    return any(p.lower() in lowered for p in phrases)


def validate_report(markdown: str, *, forbidden_phrases: tuple[str, ...] = ()) -> bool:
    if not markdown.strip() or missing_headers(markdown):
        return False
    if forbidden_phrases and contains_forbidden_phrases(markdown, forbidden_phrases):
        return False
    return True
```

Em `report_builder.py`, passar `FORBIDDEN_EXAMPLE_PHRASES` para `validate_report` e repetir retry se frase proibida detectada.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_report.py tests/unit/test_report_builder.py -v`  
Expected: PASS após atualizar mocks

- [ ] **Step 5: Commit**

```bash
git add app/core/report.py app/services/report_builder.py tests/unit/test_report.py
git commit -m "feat: validate evidence-based report structure and forbidden phrases"
```

---

### Task 9: Wire Pipeline (context + timeline + pipeline)

**Files:**
- Modify: `app/services/context.py`
- Modify: `app/core/timeline.py`
- Modify: `app/services/pipeline.py`
- Modify: `tests/unit/test_context.py`
- Modify: `tests/unit/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Em `tests/unit/test_context.py`, atualizar para novo `build_prompt` com 3 blocos e verificar presença de "Observações comportamentais".

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_context.py -v`  
Expected: FAIL

- [ ] **Step 3: Update context.py**

```python
from app.core.conversation import extract_conversation_features
from app.core.observations import build_observations
from app.core.prompt import (
    build_conversation_text,
    build_observations_text,
    build_prompt,
    build_transcript_text,
    is_protected,
)

def build_context(...) -> ContextResult:
    conversation = extract_conversation_features(segments)
    observations = build_observations(
        # signals precisam ser passados — alterar assinatura para incluir signals: list[SignalEvent]
        signals,
        segments,
        conversation,
    )
    observations_text = build_observations_text(observations)
    conversation_text = build_conversation_text(conversation)
    full_prompt = build_prompt(
        build_transcript_text(segments),
        observations_text,
        conversation_text,
    )
    ...
```

Alterar `build_context` para aceitar `signals: list[SignalEvent]`.

Em `pipeline.py`, passar `signals` ao `build_context`.

Em `timeline.py`, opcionalmente adicionar campo `observations` em `TimelineEntry.to_dict()` via helper.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_context.py tests/unit/test_pipeline.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/context.py app/services/pipeline.py app/core/timeline.py tests/
git commit -m "feat: wire observations and conversation into LLM context"
```

---

### Task 10: Update Mocks and E2E

**Files:**
- Modify: `mocks/ollama_fake.py`
- Modify: `tests/e2e/test_pipeline_e2e.py`
- Modify: `tests/unit/test_report.py`

- [ ] **Step 1: Update STATIC_REPORT_MARKDOWN**

```python
STATIC_REPORT_MARKDOWN = """# Relatório de Análise Comercial

## 1. Comportamentos Observados
- [00:00:05] Contato visual reduzido durante menção de preço (vídeo, conf=0.75).

## 2. Linha do Tempo
- 00:00:00–00:00:10: Discussão de produto e preço.

## 3. Mudanças de Comportamento
- Aumento de latência de resposta após custo de implementação.

## 4. Hipóteses Interpretativas
- O padrão visual **pode indicar** processamento cognitivo ou incerteza; alternativa: distração.

## 5. Contexto Conversacional
- Cliente verbalizou preocupação com orçamento (transcrição).

## 6. Confiança e Limitações
- Confiança moderada (0.65). Vídeo único ângulo; sem gaze 3D calibrado.

## 7. Perguntas de Follow-up Sugeridas
- "O que pesaria mais na decisão: custo inicial ou ROI em 12 meses?"

## 8. Oportunidades e Coaching
- Ancorar valor antes de detalhar custos de implementação.
"""
```

- [ ] **Step 2: Update E2E header assertions**

Substituir headers antigos por `## 1. Comportamentos Observados` e `## 8. Oportunidades e Coaching`.

- [ ] **Step 3: Run full CI gate**

Run: `bash ci/run_tests.sh`  
Expected: lint + mypy + tests + coverage ≥70% PASS

- [ ] **Step 4: Commit**

```bash
git add mocks/ollama_fake.py tests/e2e/test_pipeline_e2e.py
git commit -m "test: align mocks and E2E with evidence-based report format"
```

---

### Task 11: Evaluation Scaffold (Golden Set Stub)

**Files:**
- Create: `scripts/eval/README.md`
- Create: `scripts/eval/forbidden_phrase_rate.py`
- Create: `tests/unit/test_eval_forbidden.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_eval_forbidden.py
from scripts.eval.forbidden_phrase_rate import forbidden_phrase_rate
from app.core.prompt import FORBIDDEN_EXAMPLE_PHRASES


def test_rate_zero_on_clean_report() -> None:
    clean = "## 1. Comportamentos Observados\nObservação neutra."
    assert forbidden_phrase_rate(clean, FORBIDDEN_EXAMPLE_PHRASES) == 0.0


def test_rate_one_on_bad_report() -> None:
    bad = "O cliente odiou o produto."
    assert forbidden_phrase_rate(bad, FORBIDDEN_EXAMPLE_PHRASES) == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_eval_forbidden.py -v`  
Expected: FAIL

- [ ] **Step 3: Implement script**

```python
# scripts/eval/forbidden_phrase_rate.py
from app.core.report import contains_forbidden_phrases


def forbidden_phrase_rate(markdown: str, phrases: tuple[str, ...]) -> float:
    return 1.0 if contains_forbidden_phrases(markdown, phrases) else 0.0
```

- [ ] **Step 4: Run test**

Run: `uv run pytest tests/unit/test_eval_forbidden.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/eval/ tests/unit/test_eval_forbidden.py
git commit -m "feat: add forbidden phrase rate eval scaffold"
```

---

## Spec Coverage Self-Review

| Requisito do spec | Task |
|-------------------|------|
| Face quality scoring | Task 1, 5, 6 |
| Iris gaze / pose proxy | Task 6 |
| Conversation multimodal | Task 3 |
| Observations layer | Task 4 |
| Evidence-first prompt | Task 7 |
| New report structure | Task 7, 8 |
| Forbidden mind-reading | Task 8 |
| Confidence heuristic | Task 4 |
| Pipeline integration | Task 9 |
| E2E / mocks | Task 10 |
| Eval scaffold | Task 11 |
| Optical flow / AUs / video transformers | **Fase 2+** (fora deste plano) |
| Human κ study / A/B vendedores | **Fase 2+** |

## Fase 2 Preview (plano separado futuro)

- `app/core/prosody.py` — RMS por segmento do WAV
- Optical flow leve em `integrations/flow_cv2.py`
- Golden set YAML em `scripts/eval/golden/`
- Apex heurístico em `core/apex.py`

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-30-evidence-based-sales-feedback.md`.**

**Design spec saved to `docs/superpowers/specs/2026-06-30-evidence-based-sales-feedback-design.md`.**

**Duas opções de execução:**

1. **Subagent-Driven (recomendado)** — subagente fresco por task, revisão entre tasks
2. **Inline Execution** — executar tasks nesta sessão com checkpoints

**Qual abordagem prefere?**
