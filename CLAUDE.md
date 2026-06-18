# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Idioma de trabalho: **pt-BR**, tom conciso e direto (definido em [.agent.md](.agent.md)).

## Estado atual

✅ **MVP completo — 4 sprints concluídos.** S1 (esqueleto FastAPI + contratos + CI), S2 (workers,
pipeline de 5 estágios, sinais, telemetria, gate de memória), S3 (contexto do LLM: tokens +
sumarização hierárquica, validação/retry do relatório, Ollama/tiktoken reais), **S4 (frontend
Next.js seguindo o DESIGN.md, auth básica, retenção, logs JSON, teste E2E)**. Relatórios:
[SPRINT1.md](SPRINT1.md), [SPRINT2.md](SPRINT2.md), [SPRINT3.md](SPRINT3.md), [SPRINT4.md](SPRINT4.md).

## Decisões de setup (definidas com o usuário)

- **Arquitetura:** FastAPI único (ver seção Arquitetura). NestJS descartado.
- **Tooling:** **uv + `pyproject.toml`** (lockfile `uv.lock`), **Python 3.12** (`requires-python`
  e `.python-version`; mediapipe ainda não suporta 3.13/3.14 de forma estável — o uv baixa o 3.12).
- **Escopo do Sprint 1:** esqueleto lean — só FastAPI + SQLite + infra + mocks.
- **Pipeline real vs dublê (Sprint 2):** o CI roda **sempre com dublês** (determinístico). As libs
  pesadas vivem em `app/integrations/` (import preguiçoso) e ficam num **extra opcional `ml`**
  (`uv sync --extra ml`); só são usadas com `APP_USE_REAL_PIPELINE=true` (estágio final). `psutil`
  é dep direta (telemetria). `app/integrations/*` e `app/workers/processor.py` ficam fora da cobertura.
- **Gates do Harness:** rodam **localmente** via `ci/*.sh` + `docker-compose.harness.yml` (sem GitHub
  Actions por ora; migrável depois).
- **`ffmpeg`:** dependência de sistema (não-pip), necessária só a partir do Sprint 2.

### Allowlist de dependências (oficial — validada por `ci/validate_requirements.py`)

Qualquer dependência **direta** fora desta lista reprova o build. Adições exigem aprovação explícita.

- **Runtime:** `fastapi`, `uvicorn[standard]`, `python-multipart`, `sqlmodel`, `pydantic-settings`,
  `httpx`, `opencv-python`, `mediapipe`, `faster-whisper`, `tiktoken`, `psutil`, `numpy`
- **Dev/Harness:** `ruff`, `mypy`, `pytest`, `pytest-cov`, `pytest-asyncio`, `memory_profiler`
- **Sistema (não-pip):** `ffmpeg`

## O que é o projeto

SaaS *lean* **local-first** para vendedores B2B que transforma gravações de reuniões em insights
comportamentais acionáveis. O objetivo **não** é detectar mentiras/emoções, e sim sinalizar
interesse, engajamento, confusão e resistência para melhorar follow-ups.

Pipeline central (RF-005 do PRD):

```
upload de vídeo → extração de áudio → transcrição (Faster-Whisper)
→ análise facial (MediaPipe Face Mesh) → timeline de sinais (JSON)
→ relatório Markdown via Ollama (LLM local)
```

## Arquitetura alvo

> **Decisão de arquitetura (canônica): FastAPI único.** Um único backend FastAPI faz API +
> workers + acesso ao banco. O Bloco 1 do [questionário](.specs/Harness_Engineering_System_Design_Questionnaire.md)
> propõe dois serviços (NestJS orquestrador + FastAPI workers), mas essa opção foi **descartada** —
> ignore qualquer menção a NestJS naquele documento.

Arquitetura **Local-First** com separação rígida entre o servidor web e o processamento pesado:

- **Backend:** FastAPI, todas as rotas sob o prefixo `/api/v1/`. `/openapi.json` é a fonte única
  de verdade dos contratos; validação estrita via Pydantic (retornar **422** em payload inválido).
  Campos novos devem ser retrocompatíveis (`Optional[str] = None`). Breaking change → criar
  `/api/v2/` mantendo `/api/v1/` intacta. Docstrings nas rotas alimentam o Swagger (`/docs`).
- **Persistência:** SQLAlchemy/SQLModel. **SQLite (dev) e PostgreSQL (prod) usam o MESMO schema** —
  JSON é salvo como **TEXT** (string serializada), **nunca JSONB**, para portabilidade imediata.
  Vídeos ficam **só no filesystem** (ex. `/var/data/uploads/`); o banco guarda apenas o caminho.
  Tabela `jobs`: `id`, `meeting_id`, `status` ∈ {`pending`,`processing`,`completed`,`failed`},
  `created_at`, `updated_at`, `error_log` (+ coluna `telemetry` com tempos por estágio). Relação
  `jobs` **1-para-muitos** com `meetings` (cada reprocessamento = nova linha em `jobs`). Tabela
  `meetings` guarda `report_markdown` (sobrescrito no reprocessamento; sem histórico no MVP).
  Banco guarda transcrições, sinais (JSON-string) e o relatório; **não** guarda vídeos nem prompts
  (prompts ficam versionados no código). Retenção: cron diário apaga vídeos com job > 7 dias.
  Exclusão pelo usuário = *hard delete* (registro + `os.remove()` do arquivo).
- **Fila (no próprio banco, sem Redis no MVP):** `ProcessPoolExecutor` com **concorrência = 1**
  (sequencial); dequeue com **lock atômico** (`pending`→`processing` na mesma transação) para evitar
  processamento duplicado. **Timeout rígido de 30 min/job**. Detecção de worker travado: jobs em
  `processing` com `updated_at` parado > 30 min são marcados `failed`. Sem estados `retry`/`cancelled`
  (cancelamento = worker marca `failed` no próximo passo do loop).
- **Workers:** worker com `nice -n 10` para não disputar CPU com a API (que deve responder < 2s).
  Tracebacks completos (`traceback.format_exc()`) gravados em `jobs.error_log`. **3 tentativas** em
  memória com backoff (2s, 5s, 10s) antes de `failed` — o contador é local, nunca volta a `pending`
  automaticamente. Erros temporários (rede/Ollama, timeout leve) são reprocessáveis; definitivos
  (vídeo corrompido, falta de codec, disco cheio) vão direto a `failed`. Telemetria via `psutil`
  (CPU por etapa) e `time.perf_counter()` por estágio.
- **Visão/Áudio:** Faster-Whisper (modelo `base`) instanciado como **singleton** na inicialização do
  worker; MediaPipe instanciado **por job**. Frames extraídos via gerador `cv2.VideoCapture`,
  descartando cada frame da memória logo após a análise.
- **LLM:** HTTP para Ollama local (`llama3:8b`, janela 8k), instruído a retornar **só Markdown
  estruturado**. Contar tokens (`tiktoken`); se prompt+transcrição+sinais > **7.500 tokens**,
  comprimir via **sumarização hierárquica**: dividir a transcrição em duas metades, resumir cada
  uma e juntar com o JSON de sinais. **Nunca remover** trechos com valores monetários, prazos de
  fechamento ou objeções verbais explícitas. Cabeçalhos Markdown obrigatórios na saída: `# Relatório
  de Análise Comercial`, `## 1. Resumo Executivo`, `## 2. Objeções Identificadas`, `## 3. Momentos
  de Alto Engajamento`, `## 4. Próximos Passos Recomendados`. Validar por regex (`re.search`); em
  falha estrutural, **retry único com `temperature=0.2`**. Meta: < 5% de falhas estruturais.
- **Sincronização temporal:** `Timestamp(ms) = (Frame Index / FPS) × 1000`. Heurística agrupa
  sinais do MediaPipe dentro dos segmentos temporais do Whisper.
- **Frontend (Sprint 4):** Next.js + React + Tailwind; upload multipart, *polling* de status a cada
  5s até `completed`, render do relatório com `react-markdown`.

Estrutura atual do código:

```
app/
  main.py · config.py · db.py · models.py · schemas.py · security.py · observability.py
  api/meetings.py · api/auth.py   # endpoints /api/v1/meetings/* e /api/v1/auth/login
  core/                      # lógica pura e testável
    timestamp.py timeline.py signals.py telemetry.py types.py tokens.py prompt.py report.py
  services/                  # orquestração (testada com dublês)
    interfaces.py (Protocols) · fake_components.py · factory.py · pipeline.py
    context.py (orçamento+compressão) · report_builder.py (validação+retry) · errors.py
  integrations/              # impls reais (lazy, extra `ml`, fora da cobertura)
    audio_ffmpeg.py frames_cv2.py whisper_real.py mediapipe_real.py ollama_real.py tiktoken_counter.py
  workers/                   # fila e execução
    manager.py (JobQueue/JobRunner) · processor.py (entrypoint mprof, nice -n 10)
  services/retention.py      # purge de vídeos > 7 dias (cron)
frontend/                    # Next.js + Tailwind (DESIGN.md): login, upload, polling, react-markdown
mocks/   scripts/   ci/   tests/{unit,integration,e2e}
```

Regra de ouro: **lógica nova vai em `core/` (pura) ou `services/` (orquestração) com testes**;
o que toca hardware/modelos vai em `integrations/` atrás de um Protocol de `interfaces.py`.

## Pipeline de processamento (5 estágios com checkpoint)

Estágios independentes, cada um persiste resultado intermediário em disco no diretório do job:

```
extract-audio → transcribe → face-analysis → timeline-builder → llm-analysis
```

Checkpoints físicos em disco ao concluir cada etapa crítica: `audio.wav`, `transcript.json`,
`signals.json`. Em falha na geração do relatório, **retomar a partir do llm-analysis** lendo os
JSONs já salvos — **nunca reprocessar vídeo/áudio** (etapa mais cara é MediaPipe, depois Whisper;
Ollama é a mais barata). Áudio extraído é temporário (descartado após o relatório). Vídeo original
descartado após processar, salvo se necessário para reprocesso.

**Limites de upload:** vídeo ≤ **200 MB**, duração ≤ **30 min**. Formato canônico interno:
MP4 / H.264. Transcodificar com `ffmpeg` **só quando** o upload não estiver nesse formato; normalizar
para 24 FPS CFR. FPS para cálculos é o nativo (`cv2.CAP_PROP_FPS`), não um valor fixo.

## Sinais comportamentais (heurísticos, MVP)

3 sinais via limiares geométricos de landmarks do MediaPipe (zero IA pesada):
`olhar_desviado` (sem olhar p/ câmera > 3s), `aceno_cabeca_positivo`/`aceno_cabeca_negativo`,
`afastamento_da_tela` (redução súbita do tamanho da face). Heurística de **resistência** = acúmulo
de `olhar_desviado`/`afastamento_da_tela` coincidindo com palavras-chave (`preço`, `contrato`,
`prazo`, `concorrente`) na transcrição. Whisper retorna **segmentos** (frases, 2–7s), não palavras.
Associação sinal↔fala por interseção de intervalo de tempo.

Schema de evento (`schema_version: 1`, com `source` da regra de origem):
```json
{ "timestamp_ms": 312000, "signal_type": "olhar_desviado", "confidence": 0.91,
  "meta": {"duration_seconds": 3.5} }
```
Timeline consolidada: lista cronológica de segmentos `{start_time, end_time, speaker, text, signals[]}`.

## Endpoints da API

`POST /api/v1/auth/login` · `POST /api/v1/meetings/upload` · `GET /api/v1/meetings/` ·
`GET /api/v1/meetings/{id}/status` · `GET /api/v1/meetings/{id}/report` ·
`DELETE /api/v1/meetings/{id}`. Front faz *polling* de `status` a cada 5s até `completed`, depois
busca `report`. Latência alvo de `meetings/` e `report`: **< 200 ms**.

## Observabilidade

Logs **JSON estruturados** em stdout via `logging`, com chaves obrigatórias
`{timestamp, level, job_id, component, message}` — o `job_id` permite rastrear toda a jornada do arquivo.

## Harness Engineering — regras de gate (obrigatórias)

O projeto é governado por um "Harness" que atua como **gatekeeper de merge** (ver [.specs/spec.md](.specs/spec.md)).
Toda contribuição precisa passar em **todos** estes critérios — falha em qualquer um reprova o build:

| Critério | Condição de aprovação |
|---|---|
| Tipagem estática | `mypy --strict .` → **zero erros** |
| Formatação/lint | `ruff check .` → limpo |
| Cobertura | **≥ 70%** focada em regras de negócio, utils e rotas (`app/core`, `app/services` e rotas) |
| Testes unitários + CI | 100% passando, **CI < 5 min** |
| E2E | detecta as palavras **"preço"** e **"produto"** no mock; **< 3 min** |
| Memória | `mprof` confirma pico de RAM **< 2.5 GB** durante a simulação |
| Dependências | `requirements.txt`/`pyproject.toml` **intocados** sem pacotes não autorizados |

Sandbox dos agentes (`docker-compose.harness.yml`): `mem_limit: 4g`, `cpus: 2`, acesso externo à
internet monitorado/bloqueado, execução embrulhada em `mprof`. Bibliotecas instaladas **apenas** de
um cache local pré-aprovado de pacotes Python. O Harness intercepta chamadas a Ollama/Whisper com
dados estáticos em cache durante os ciclos de CI; modelos reais só rodam no **estágio final de
aprovação**. Performance: o processo web do FastAPI não pode sustentar 100% de CPU (medir via `psutil`).

## Comandos (uv)

```bash
uv sync                          # cria .venv e instala deps (baixa Python 3.12 se preciso)
uv run uvicorn app.main:app --reload   # sobe a API (http://127.0.0.1:8000, docs em /docs)
uv run ruff check .              # lint/formatação
uv run ruff format .             # formatar
uv run mypy .                    # tipagem strict (config em pyproject; deve dar zero erros)
uv run pytest                    # testes
uv run pytest --cov=app          # com cobertura (mínimo 70%)
uv run pytest tests/unit/test_x.py::test_y   # rodar um teste específico
bash ci/run_tests.sh             # roda todos os gates locais (lint+type+test+cobertura)
uv run python ci/validate_requirements.py  # valida deps contra a allowlist
bash ci/mprof_check.sh           # gate de memória (mprof, pico < 2.5 GB)
uv sync --extra ml               # instala a stack pesada (pipeline real, estágio final)
docker compose up                # sandbox local (App + Banco + Ollama)
docker compose -f docker-compose.harness.yml up   # sandbox restrita (4g/2cpu)
```

Vídeo padrão de teste (E2E): MP4, **10s**, 24 FPS CFR, 640x480, áudio em PT com a frase
*"Gostei do produto, mas precisamos discutir as condições de preço na próxima semana"*.
Normalização via `ffmpeg` (24 FPS CFR, H.264).

## Mocks determinísticos (CI rápido)

Para não consumir hardware no CI, as integrações pesadas são substituídas por dublês:
- **Ollama:** servidor HTTP fake que devolve Markdown estático imediatamente.
- **MediaPipe:** retorna JSON fixo de coordenadas (com ao menos um evento contendo `signal_type`).
- **Faster-Whisper:** intercepta chamadas de áudio e devolve blocos de texto predefinidos.

## Convenções de trabalho (de .agent.md)

- **Edits atômicos e mínimos**, uma responsabilidade por mudança.
- **Não adicionar dependências** (`requirements.txt`/`pyproject.toml`) sem aprovação explícita —
  além de violar o gate do Harness, há clarificação pendente sobre a whitelist (ver [research.md](research.md)).
- **Não acessar a internet externa** sem permissão explícita.
- Pedir confirmação antes de mexer em infra/CI crítica.
- Manter rastreabilidade: o fluxo é **spec → plano → tasks → checkpoints**.

## Mapa dos artefatos de planejamento

- [.specs/spec.md](.specs/spec.md) — spec do Harness + roadmap de 4 sprints (Agent Directives + gates por sprint).
- [.specs/PRD_SaaS_Lean_Ollama_MVP.md](.specs/PRD_SaaS_Lean_Ollama_MVP.md) — PRD do produto (RF-001…RF-005, KPIs, IA responsável, riscos).
- [.specs/Harness_Engineering_System_Design_Questionnaire.md](.specs/Harness_Engineering_System_Design_Questionnaire.md) — **questionário de design (120 decisões, fonte mais detalhada)**. ⚠️ O Bloco 1 propõe NestJS+FastAPI, mas a arquitetura canônica é **FastAPI único** (ver acima).
- [.specs/DESIGN.md](.specs/DESIGN.md) — **design system do frontend** (tokens, tipografia, componentes, motion, acessibilidade; estilo Linear/Vercel/Notion). É a **fonte da verdade visual** a seguir ao construir a UI Next.js do **Sprint 4** (React + Tailwind, Inter + JetBrains Mono, 2 cores por tela, sem gradientes/sombras pesadas).
- [plan.md](plan.md) — plano de implementação: requisitos sintetizados REQ-001…REQ-010, fases P1–P4, tarefas **T001–T020** e matriz de rastreabilidade.
- [research.md](research.md) — clarificações pendentes (whitelist de pacotes; estratégia de produção).
- [checkpoints/](checkpoints/) — rastreabilidade YAML: `spec-to-plan.yaml` (REQ→Plano) e `plan-to-tasks.yaml` (Plano→Tasks).

Ao iniciar implementação, comece por **Sprint 1 / Phase 1** (tasks T001–T006: docker-compose,
FastAPI+`/api/v1/`, SQLite+`jobs`, ruff/mypy, controle de deps).
