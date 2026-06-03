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

- [ ] T001 [Plan:1.1] Criar `docker-compose.yml` na raiz com `mem_limit: 4g` e `cpus: 2`.
- [ ] T002 [Plan:1.1] Adicionar `.env.example` com variáveis de sandbox e instruções de execução.
- [ ] T003 [Plan:1.2] Criar `app/main.py` iniciando FastAPI e incluindo prefixo `/api/v1/` e rota `/health`.
- [ ] T004 [Plan:1.3] Implementar `app/db.py` com SQLAlchemy/SQLModel e criar migration inicial (sqlite) e modelo `jobs`.
- [ ] T005 [Plan:1.4] Adicionar `pyproject.toml`/`requirements.txt` e configurar `ruff` e `mypy` em `pyproject.toml`.
- [ ] T006 [Plan:1.5] Implementar hook local que detecta diffs em `requirements.txt` e falha a validação.
- [ ] T007 [Plan:2.1] Implementar `app/workers/manager.py` com `ProcessPoolExecutor(concurrency=1)` e wrapper de `nice`.
- [ ] T008 [Plan:2.2] Criar `mocks/ollama_server.py` que responde Markdown estático em HTTP.
- [ ] T009 [Plan:2.2] Criar `mocks/whisper_fake.py` e `mocks/mediapipe_fake.py` retornando JSON predefinido.
- [ ] T010 [Plan:2.3] Adicionar script `scripts/normalize_video.sh` usando `ffmpeg` para CFR 24FPS H.264.
- [ ] T011 [Plan:2.3] Implementar `app/services/frame_extractor.py` usando OpenCV como gerador de frames.
- [ ] T012 [Plan:2.4] Integrar `mprof` em `app/workers/processor.py` e registrar pico de memória; abortar se >2.5GB.
- [ ] T013 [Plan:3.1] Implementar `app/core/timestamp.py` com função de conversão de frame->ms e testes unitários.
- [ ] T014 [Plan:3.2] Implementar `app/core/timeline_builder.py` que agrupa sinais e transcrições; adicionar testes unitários cobrindo heurísticas.
- [ ] T015 [Plan:3.2] Adicionar integração HTTP cliente para Ollama local em `app/services/llm_client.py`.
- [ ] T016 [Plan:3.3] Implementar `app/validators/report_validator.py` que valida se subtítulos exigidos existem; retry com temperature ajustado.
- [ ] T017 [Plan:4.1] Implementar endpoints de upload e status em `app/api/meetings.py` e handlers Pydantic para upload.
- [ ] T018 [Plan:4.2] Escrever teste E2E `tests/e2e/test_pipeline_e2e.py` que usa o vídeo padrão e mocks.
- [ ] T019 [Plan:4.2] Criar o arquivo de vídeo padrão `tests/fixtures/mock_video_10s.mp4` e fixture de áudio com a frase em PT.
- [ ] T020 [Plan:4.3] Documentar instruções CI em `ci/README.md` e script de validação de dependências.

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
