# Sprint 4 — Frontend, Integração e Refinamento E2E

**Status:** ✅ Concluído (MVP completo) · **Data:** Jun/2026

> Objetivo do sprint (spec): construir a interface de consumo (Next.js) e garantir o ciclo
> completo cliente → pipeline, com teste E2E dentro dos limites do Harness.

---

## 1. Frontend Next.js ([frontend/](frontend/))

UI seguindo o design system [`.specs/DESIGN.md`](.specs/DESIGN.md): App Router + React 18 +
Tailwind, fontes **Inter** + **JetBrains Mono**, 2 cores por tela (neutro + acento `#5e6ad2`),
bordas 1px, `shadow-sm`, sem gradientes, motion 150ms, foco visível e `prefers-reduced-motion`.

| Arquivo | Responsabilidade |
|---|---|
| [frontend/app/page.tsx](frontend/app/page.tsx) | Orquestra auth + layout (upload + lista) |
| [frontend/components/LoginForm.tsx](frontend/components/LoginForm.tsx) | Login (`/auth/login`) |
| [frontend/components/UploadForm.tsx](frontend/components/UploadForm.tsx) | Upload multipart + consentimento |
| [frontend/components/MeetingsPanel.tsx](frontend/components/MeetingsPanel.tsx) | Lista + **polling de status a cada 5s** |
| [frontend/components/ReportView.tsx](frontend/components/ReportView.tsx) | Render do relatório com `react-markdown` |
| [frontend/components/ui.tsx](frontend/components/ui.tsx) | Button/Card/Input/Label/StatusBadge (tokens do DESIGN) |
| [frontend/lib/api.ts](frontend/lib/api.ts) | Cliente HTTP do backend |
| [frontend/tailwind.config.ts](frontend/tailwind.config.ts) | Tokens do design system |

**Verificado:** `npm install` (188 pacotes), `npx tsc --noEmit` limpo e `next build` ✓
(4 páginas estáticas).

## 2. Backend — auth, retenção, observabilidade

| Arquivo | Responsabilidade |
|---|---|
| [app/api/auth.py](app/api/auth.py) + [app/security.py](app/security.py) | `POST /api/v1/auth/login` + token HMAC (stdlib, sem deps) |
| [app/services/retention.py](app/services/retention.py) | `purge_old_videos` — apaga vídeos > 7 dias (cron: [scripts/retention.py](scripts/retention.py)) |
| [app/observability.py](app/observability.py) | Logs **JSON** em stdout (`timestamp, level, job_id, component, message`) |
| [app/main.py](app/main.py) | CORS (libera `localhost:3000`), handler de erro global, logging |

## 3. Teste E2E ([tests/e2e/test_pipeline_e2e.py](tests/e2e/test_pipeline_e2e.py))

Fluxo completo determinístico: **login → upload → worker → relatório**, validando os critérios
do Harness — gera `audio.wav`, transcrição com **"produto"/"preço"**, `signals.json` com
`signal_type`, relatório estruturado não vazio — em **< 3 minutos**.

## 4. Resultado dos gates do Harness

| Gate | Resultado |
|---|---|
| Allowlist de dependências | ✅ 18 diretas, todas autorizadas |
| Ruff (lint + format) | ✅ limpo |
| Mypy `--strict` | ✅ 0 erros |
| Pytest | ✅ **73 testes passaram** (inclui E2E) |
| Cobertura | ✅ **96%** |
| Memória (`mprof`) | ✅ pico **~30 MiB** (limite 2.5 GB) |
| E2E | ✅ "preço"/"produto" detectados, < 3 min |
| Frontend | ✅ `tsc` limpo + `next build` |

Smoke real: login OK, 401 em credenciais inválidas, **CORS** liberando `http://localhost:3000`,
listagem 200.

## 5. Rastreabilidade

| Task | Status |
|---|---|
| T017 — endpoints + auth | ✅ |
| T018 — teste E2E | ✅ |
| T019 — critério do vídeo padrão (via dublês determinísticos) | ✅ |
| T020 — CI docs + validação de deps | ✅ |

## 6. Estado do projeto

**MVP completo (4/4 sprints).** Para subir tudo:
```bash
uv run uvicorn app.main:app --reload     # backend (8000)
cd frontend && npm install && npm run dev # frontend (3000)
```

### Pendências / tech debt remanescentes
- Pipeline real (`--extra ml`) e Ollama/tiktoken ainda validados só fora do CI (estágio final).
- Auth básica não é enforçada nas rotas de meetings (escopo MVP); enforce é follow-up simples.
- Diarização de falante, validação de vídeo corrompido e estratégia de produção seguem como tech debt.
