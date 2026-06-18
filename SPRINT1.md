# Sprint 1 — Infraestrutura, Banco e Rotas Base

**Status:** ✅ Concluído · **Escopo:** esqueleto *lean* + mocks · **Data:** Jun/2026

> Objetivo do sprint (spec): estabelecer os contratos OpenAPI, o banco SQLite e a fila de
> processamento, com os gates do Harness rodando localmente e verdes.

---

## 1. Decisões de setup (definidas com o time)

| Tema | Decisão |
|---|---|
| Arquitetura | **FastAPI único** (API + workers + DB). NestJS do questionário foi descartado. |
| Tooling | **uv + `pyproject.toml`** (lockfile `uv.lock`), **Python 3.12** (mediapipe não suporta 3.13+) |
| Escopo do Sprint 1 | Esqueleto lean: FastAPI + SQLite + infra + mocks. Libs de IA/vídeo **autorizadas** mas só instaladas no Sprint 2. |
| Gates do Harness | Rodam **localmente** (`ci/*.sh` + `docker-compose.harness.yml`); GitHub Actions fica para depois. |
| Dependências | Allowlist oficial aprovada; deps fora da lista reprovam o build. |

Detalhes consolidados em [CLAUDE.md](CLAUDE.md).

---

## 2. O que foi entregue

### Backend FastAPI ([app/](app/))

| Arquivo | Responsabilidade |
|---|---|
| [app/main.py](app/main.py) | App FastAPI, rota `/health`, rotas de negócio sob `/api/v1/`, `lifespan` (cria banco e diretório de uploads) |
| [app/api/meetings.py](app/api/meetings.py) | Endpoints de reuniões (upload, list, status, report, delete) |
| [app/models.py](app/models.py) | Tabelas `Meeting` e `Job` (SQLModel); `JobStatus` como `StrEnum`; JSON salvo como TEXT |
| [app/db.py](app/db.py) | Engine, `init_db`, dependência `get_session` |
| [app/config.py](app/config.py) | `Settings` via pydantic-settings (prefixo `APP_`), limites de upload (200 MB / 30 min) |
| [app/schemas.py](app/schemas.py) | Contratos Pydantic de entrada/saída (retrocompatíveis) |
| [app/core/timestamp.py](app/core/timestamp.py) | Conversão `frame → ms → HH:MM:SS` (fórmula oficial) |

### Mocks determinísticos ([mocks/](mocks/))

- [mocks/ollama_fake.py](mocks/ollama_fake.py) — Markdown estático com os cabeçalhos obrigatórios do relatório.
- [mocks/whisper_fake.py](mocks/whisper_fake.py) — segmentos fixos contendo **"produto"** e **"preço"**.
- [mocks/mediapipe_fake.py](mocks/mediapipe_fake.py) — sinais fixos com `signal_type` e `schema_version`.

### CI local / Harness ([ci/](ci/))

- [ci/validate_requirements.py](ci/validate_requirements.py) — valida deps diretas contra a allowlist (REQ-010).
- [ci/run_tests.sh](ci/run_tests.sh) — roda todos os gates: allowlist → ruff → ruff format → mypy → pytest+cobertura.
- [ci/mprof_check.sh](ci/mprof_check.sh) — telemetria de memória (stub até o Sprint 2).

### Infraestrutura

- [Dockerfile](Dockerfile) — imagem `python:3.12-slim` com `ffmpeg` e uv.
- [docker-compose.yml](docker-compose.yml) — sandbox de dev (app + ollama).
- [docker-compose.harness.yml](docker-compose.harness.yml) — sandbox restrita (`mem_limit: 4g`, `cpus: 2`).
- [pyproject.toml](pyproject.toml) — deps (uv) + config de ruff, mypy `--strict` e pytest.
- [.gitignore](.gitignore), [.python-version](.python-version), [.env.example](.env.example).

---

## 3. Contratos da API (`/api/v1`)

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `POST` | `/api/v1/meetings/upload` | Upload de vídeo + consentimento; enfileira job `pending` | 201 / 415 / 413 / 422 |
| `GET` | `/api/v1/meetings/` | Lista reuniões | 200 |
| `GET` | `/api/v1/meetings/{id}/status` | Status do processamento | 200 / 404 |
| `GET` | `/api/v1/meetings/{id}/report` | Relatório Markdown (nulo até `completed`) | 200 / 404 |
| `DELETE` | `/api/v1/meetings/{id}` | Hard delete (registro + arquivo) | 204 / 404 |
| `GET` | `/health` | Healthcheck | 200 |

`/openapi.json` e `/docs` gerados automaticamente; validação estrita via Pydantic (422).

---

## 4. Resultado dos gates do Harness

Todos verdes (`bash ci/run_tests.sh`):

| Gate | Resultado |
|---|---|
| Allowlist de dependências | ✅ 12 diretas, todas autorizadas |
| Ruff (lint) | ✅ limpo |
| Ruff (format `--check`) | ✅ 19 arquivos formatados |
| Mypy `--strict` | ✅ 0 erros em 19 arquivos |
| Pytest | ✅ **20 testes passaram** |
| Cobertura | ✅ **94%** (mínimo exigido: 70%) |

### Cobertura por módulo

```
Name                    Stmts   Miss Branch BrPart  Cover
app/api/meetings.py        73      3     14      1    95%
app/config.py              15      0      0      0   100%
app/core/timestamp.py      13      0      6      0   100%
app/db.py                  14      4      0      0    71%
app/main.py                21      4      0      0    81%
app/models.py              27      0      0      0   100%
app/schemas.py             18      0      0      0   100%
TOTAL                     182     11     20      1    94%
```

Smoke test real (servidor de fato no ar): `/health` → `{"status":"ok"}`, `/openapi.json` → 200 com
todas as rotas, e o `lifespan` criou `data/app.db` + `data/uploads/`.

---

## 5. Como rodar

```bash
uv sync                                   # cria .venv e instala deps (baixa Python 3.12 se preciso)
uv run uvicorn app.main:app --reload      # API em http://127.0.0.1:8000 (docs em /docs)
bash ci/run_tests.sh                       # roda todos os gates do Harness
docker compose up                          # sandbox dev (app + ollama)
docker compose -f docker-compose.harness.yml up --build   # sandbox restrita 4g/2cpu
```

---

## 6. Rastreabilidade (tarefas do plano)

| Task | Descrição | Status |
|---|---|---|
| T001 | docker-compose com limites 4g/2cpu | ✅ (`docker-compose.harness.yml`) |
| T002 | `.env.example` | ✅ |
| T003 | `app/main.py` (`/api/v1/` + `/health`) | ✅ |
| T004 | `app/db.py` + modelo `jobs` (+ `meetings`) | ✅ |
| T005 | `pyproject.toml` + ruff + mypy | ✅ |
| T006 | validação de dependências | ✅ (`ci/validate_requirements.py`) |
| T008/T009 | mocks Ollama/Whisper/MediaPipe | ✅ adiantado (stubs) |
| T017 | endpoints upload/status/report | ✅ adiantado |

Mapa completo REQ → Plano → Task em [plan.md](plan.md) e [checkpoints/](checkpoints/).

---

## 7. Pendências e tech debt (registrados para os próximos sprints)

- **Estratégia de produção** e **whitelist de novos pacotes** ainda em aberto ([research.md](research.md)).
- Validação de vídeo corrompido e limite de memória no upload (marcados como tech debt pós-MVP).
- Fallback quando o Ollama está indisponível (Q7 do questionário).
- `ffmpeg` é dependência de sistema (já incluída no Dockerfile), necessária a partir do Sprint 2.

---

## 8. Próximo: Sprint 2 — Workers e Visão/Áudio

- `ProcessPoolExecutor` (concorrência 1) com `nice -n 10`; dequeue com lock atômico, timeout 30 min.
- Normalização `ffmpeg` (24 FPS CFR / H.264) + extração de frames em streaming (`cv2.VideoCapture`).
- Whisper `base` (singleton) e MediaPipe (por job) reais, substituindo os mocks no estágio final.
- Telemetria de memória com `mprof` (gate de pico < 2.5 GB) e tempos por estágio (`psutil`).
- Pipeline em 5 estágios com checkpoints em disco (`audio.wav`, `transcript.json`, `signals.json`).
