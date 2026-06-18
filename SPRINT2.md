# Sprint 2 — Workers de Processamento e Visão/Áudio

**Status:** ✅ Concluído · **Escopo:** arquitetura de pipeline testável + integrações reais atrás de fronteira · **Data:** Jun/2026

> Objetivo do sprint (spec): isolar o processamento pesado fora do loop do FastAPI, com workers
> sequenciais, pipeline em estágios com checkpoints, heurísticas de sinais e gate de memória.

---

## 1. Abordagem

CI **determinístico com dublês** (sem libs pesadas); as integrações reais
(OpenCV/MediaPipe/Faster-Whisper/ffmpeg/Ollama) ficam em `app/integrations/` com **import
preguiçoso** e num **extra opcional `ml`**, acionadas só com `APP_USE_REAL_PIPELINE=true` — exatamente
o que o Harness descreve ("modelos reais apenas no estágio final de aprovação"). Toda a lógica de
valor (heurísticas, timeline, orquestração, fila, telemetria) é Python puro e 100%/quase testável.

---

## 2. O que foi entregue

### Núcleo testável ([app/core/](app/core/))

| Arquivo | Responsabilidade |
|---|---|
| [app/core/types.py](app/core/types.py) | `Segment`, `SignalEvent`, `FrameMetrics`, `TimelineEntry` (+ serialização) |
| [app/core/signals.py](app/core/signals.py) | Heurísticas geométricas: `olhar_desviado`, `afastamento_da_tela`, `aceno_cabeca_positivo/negativo` |
| [app/core/timeline.py](app/core/timeline.py) | Cruza sinais × segmentos por intervalo de tempo; heurística de resistência |
| [app/core/telemetry.py](app/core/telemetry.py) | `measure()` — tempo por estágio (`perf_counter`) + CPU (`psutil`) |

### Serviços / orquestração ([app/services/](app/services/))

| Arquivo | Responsabilidade |
|---|---|
| [app/services/interfaces.py](app/services/interfaces.py) | Protocols: `AudioExtractor`, `Transcriber`, `FaceAnalyzer`, `ReportGenerator` |
| [app/services/fake_components.py](app/services/fake_components.py) | Dublês determinísticos (usam `mocks/`) |
| [app/services/pipeline.py](app/services/pipeline.py) | Orquestrador de 5 estágios + checkpoints + retomada |
| [app/services/factory.py](app/services/factory.py) | Escolhe dublê vs real conforme `use_real_pipeline` |
| [app/services/errors.py](app/services/errors.py) | `TemporaryError` (retentável) vs `DefinitiveError` |

### Integrações reais ([app/integrations/](app/integrations/) — extra `ml`, fora da cobertura)

`audio_ffmpeg.py` (extração + normalização CFR 24/H.264) · `frames_cv2.py` (streaming de frames) ·
`whisper_real.py` (Faster-Whisper `base`, singleton) · `mediapipe_real.py` (Face Mesh por job) ·
`ollama_real.py` (HTTP `llama3:8b`).

### Workers ([app/workers/](app/workers/))

- [app/workers/manager.py](app/workers/manager.py) — `claim_next_job` (dequeue atômico), `reap_stuck_jobs`
  (timeout 30 min), `JobRunner` (retries 3× com backoff 2/5/10s, erros temporário/definitivo, telemetria).
- [app/workers/processor.py](app/workers/processor.py) — entrypoint `ProcessPoolExecutor` (concorrência 1, `nice -n 10`).

### Pipeline de 5 estágios (com checkpoints em disco)

```
extract-audio → transcribe → face-analysis → timeline-builder → llm-analysis
   audio.wav    transcript.json  signals.json   timeline.json    report.md
```
Cada estágio é pulado se o artefato já existe (`force=False`) → **retomada** a partir de qualquer
ponto sem reprocessar vídeo/áudio.

### Infra / CI

- [scripts/normalize_video.sh](scripts/normalize_video.sh) — ffmpeg CFR 24 FPS / H.264.
- [scripts/mprof_target.py](scripts/mprof_target.py) + [ci/mprof_check.sh](ci/mprof_check.sh) — gate de memória real.
- [pyproject.toml](pyproject.toml) — extra `ml`, overrides de mypy (cv2/mediapipe/faster_whisper/psutil), `omit` de cobertura.

---

## 3. Resultado dos gates do Harness

| Gate | Resultado |
|---|---|
| Allowlist de dependências | ✅ 17 diretas, todas autorizadas |
| Ruff (lint + format) | ✅ limpo |
| Mypy `--strict` | ✅ 0 erros |
| Pytest | ✅ **44 testes passaram** |
| Cobertura | ✅ **95%** (core/services bem acima de 70%) |
| Memória (`mprof`) | ✅ pico **~30 MiB** (limite 2.5 GB) |

Novos testes: `test_signals`, `test_timeline`, `test_telemetry`, `test_pipeline`, `test_factory`
(unit) e `test_queue` (integração: claim atômico, sucesso, retries, erro definitivo, reaper, run_once).

---

## 4. Rastreabilidade (tarefas do plano)

| Task | Descrição | Status |
|---|---|---|
| T007 | `ProcessPoolExecutor` concorrência 1 + `nice -n 10` | ✅ `app/workers/` |
| T008/T009 | mocks Ollama/Whisper/MediaPipe | ✅ (Sprint 1) + dublês de componente |
| T010 | script ffmpeg CFR 24/H.264 | ✅ `scripts/normalize_video.sh` |
| T011 | extração de frames em streaming (OpenCV) | ✅ `app/integrations/frames_cv2.py` |
| T012 | `mprof` + abortar se > 2.5 GB | ✅ `ci/mprof_check.sh` |
| T013 | conversão frame→ms | ✅ (Sprint 1) |
| T014 | timeline builder + heurísticas | ✅ `app/core/timeline.py` + `signals.py` |

---

## 5. Pendências / tech debt

- Integrações reais (`app/integrations/*`) ainda **não exercitadas em CI** (precisam de `--extra ml`,
  `ffmpeg` e pesos de modelo) — validação no estágio final de aprovação.
- `speaker` real (diarização) não implementado; Whisper retorna falante genérico.
- Timeout de 30 min por job é aplicado via reaper + `ProcessPoolExecutor`; ainda sem cancelamento cooperativo fino.

---

## 6. Próximo: Sprint 3 — Sincronização Temporal e Integração LLM

- Contagem de tokens (`tiktoken`) e sumarização hierárquica quando > 7.500 tokens.
- Ollama real (`llama3:8b`) com prompt estruturado; validação por regex dos cabeçalhos obrigatórios
  e retry com `temperature=0.2`.
- Refino da timeline e do contexto enviado ao LLM (preservar valores monetários, prazos e objeções).
