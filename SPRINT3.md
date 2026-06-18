# Sprint 3 — Sincronização Temporal e Integração LLM

**Status:** ✅ Concluído · **Escopo:** contexto do LLM (tokens + compressão) + geração validada do relatório · **Data:** Jun/2026

> Objetivo do sprint (spec): montar o contexto para o Ollama respeitando a janela de tokens,
> comprimir quando necessário **sem perder informação comercial crítica**, e garantir que o
> relatório final tenha a estrutura Markdown obrigatória (com retry).

---

## 1. O que foi entregue

### Núcleo testável ([app/core/](app/core/))

| Arquivo | Responsabilidade |
|---|---|
| [app/core/tokens.py](app/core/tokens.py) | `estimate_tokens` — estimativa heurística (~4 chars/token), pura e offline |
| [app/core/prompt.py](app/core/prompt.py) | `build_prompt` (cabeçalhos obrigatórios), `build_transcript_text`/`build_signals_text`, `is_protected` (valores monetários, prazos, objeções) |
| [app/core/report.py](app/core/report.py) | `validate_report`/`missing_headers` — validação por regex dos 5 cabeçalhos |

### Serviços ([app/services/](app/services/))

| Arquivo | Responsabilidade |
|---|---|
| [app/services/context.py](app/services/context.py) | `build_context` — se cabe no orçamento usa íntegro; senão **sumarização hierárquica** (2 metades) mantendo **trechos protegidos verbatim** |
| [app/services/report_builder.py](app/services/report_builder.py) | `generate_validated_report` — valida e, se falhar, refaz **1× com `temperature=0.2`** |

### Integração no pipeline

O estágio **llm-analysis** agora: monta o contexto (com orçamento `max_context_tokens`, padrão
**7.500**), comprime se necessário e gera o relatório com validação + retry. Checkpoint/retomada
em `report.md` preservados.

### Integrações reais ([app/integrations/](app/integrations/) — extra `ml`)

- [app/integrations/ollama_real.py](app/integrations/ollama_real.py) — `OllamaReportGenerator` (passa `temperature` nas options) e `OllamaSummarizer` (resume preservando dados críticos).
- [app/integrations/tiktoken_counter.py](app/integrations/tiktoken_counter.py) — contagem real via `tiktoken` (`cl100k_base`), injetada pela factory no modo real.

### Contratos atualizados

`ReportGenerator.generate(prompt, *, temperature=0.7)` (recebe prompt já montado) e novo
`Summarizer.summarize(text)`. Dublês: `FakeReportGenerator`, `FakeSummarizer`.

---

## 2. Como a compressão preserva o que importa (Q88/Q89)

```
prompt = sistema + transcrição + sinais
se tokens(prompt) <= 7.500 → usa íntegro
senão:
  protegidos (R$/%/desconto, prazo/mês/fechamento, preço/objeção/contrato) → mantidos VERBATIM
  restante → dividido em 2 metades → cada metade resumida → recombina (protegidos + resumos + sinais)
```

---

## 3. Resultado dos gates do Harness

| Gate | Resultado |
|---|---|
| Allowlist de dependências | ✅ 18 diretas, todas autorizadas (`tiktoken` no extra `ml`) |
| Ruff (lint + format) | ✅ limpo |
| Mypy `--strict` | ✅ 0 erros |
| Pytest | ✅ **61 testes passaram** |
| Cobertura | ✅ **96%** |
| Memória (`mprof`) | ✅ pico **~35 MiB** (limite 2.5 GB) |

Novos testes: `test_tokens`, `test_prompt`, `test_report`, `test_context` (sem/com compressão +
trecho protegido verbatim), `test_report_builder` (válido em 1 tentativa; retry com `temperature=0.2`).

---

## 4. Rastreabilidade (tarefas do plano)

| Task | Descrição | Status |
|---|---|---|
| T015 | Cliente HTTP do Ollama | ✅ `app/integrations/ollama_real.py` |
| T016 | Validador do relatório + retry temperatura | ✅ `app/core/report.py` + `app/services/report_builder.py` |
| (extra) | Contagem de tokens + sumarização hierárquica | ✅ `app/core/tokens.py` + `app/services/context.py` |

---

## 5. Pendências / tech debt

- Ollama/tiktoken reais ainda **não exercitados em CI** (precisam de `--extra ml` + servidor Ollama) — validação no estágio final.
- `tiktoken` baixa a codificação na 1ª chamada (rede); por isso fica no modo real, e o CI usa a estimativa heurística.
- Telemetria de qualidade do relatório (tempo de leitura, 👍/👎) é do produto/frontend (Sprint 4).

---

## 6. Próximo: Sprint 4 — Frontend e E2E

- UI **Next.js + Tailwind** seguindo o [.specs/DESIGN.md](.specs/DESIGN.md): upload multipart, polling de status a cada 5s, render com `react-markdown`.
- Teste **E2E** com o vídeo padrão (10s) validando "preço"/"produto", **< 3 min**.
- Auth básica (`/api/v1/auth/login`), retenção (cron 7 dias), tratamento de erros global.
