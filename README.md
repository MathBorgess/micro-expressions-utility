# micro-expressions-utility

Ferramenta local-first de análise comportamental de reuniões de vendas. O sistema recebe um vídeo de reunião, extrai o áudio, transcreve a fala, detecta sinais não-verbais (MediaPipe) e gera um relatório em Markdown com observações comportamentais evidenciadas — tudo rodando localmente, sem enviar dados para nuvem.

**Stack:** FastAPI · Next.js · Ollama (`llama3:8b`) · ffmpeg · MediaPipe · Faster-Whisper

---

## Pré-requisitos

| Ferramenta | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.12 exato | MediaPipe não suporta 3.13+ |
| **uv** | recente | Gerenciador de pacotes Python |
| **Node.js** | 18+ | Frontend Next.js |
| **ffmpeg** | qualquer recente | Extração de áudio / normalização de vídeo |
| **Ollama** | recente | LLM local para relatórios |

---

## Setup automático (recomendado)

Instala dependências Python (com stack ML), Node, verifica/instala **ffmpeg** e **Ollama**, baixa o modelo `llama3:8b` e prepara diretórios:

```bash
bash scripts/setup_local.sh
```

Verificar pré-requisitos sem instalar:

```bash
bash scripts/check_prerequisites.sh
```

---

## Setup manual

### 1. uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. ffmpeg

```bash
# macOS
brew install ffmpeg

# Debian/Ubuntu
sudo apt-get install -y ffmpeg
```

### 3. Ollama

```bash
# macOS
brew install ollama
brew services start ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
ollama serve   # em outro terminal, se necessário
```

Baixar o modelo usado pelo pipeline:

```bash
ollama pull llama3:8b
```

### 4. Projeto

```bash
cp .env.example .env
mkdir -p data/uploads data/jobs
uv sync --extra ml
cd frontend && npm install && cd ..
```

---

## Como rodar

O projeto precisa de **3 terminais** simultâneos.

### Terminal 1 — API (backend)

```bash
uv run uvicorn app.main:app --reload --reload-dir app
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

### Terminal 2 — Worker (processamento de vídeos)

```bash
uv run python scripts/run_worker.py
```

O worker verifica a fila a cada 2s e processa uploads pendentes.

### Terminal 3 — Frontend

```bash
cd frontend
npm run dev
```

- UI: http://localhost:3000  

---

## Modos de pipeline

### Modo dublê (padrão)

Sem GPU nem modelos pesados. Ideal para desenvolvimento e testes rápidos.

```bash
# .env
APP_USE_REAL_PIPELINE=false
```

### Modo real (produção local)

MediaPipe + Whisper + Ollama. Requer `uv sync --extra ml`, **ffmpeg** e **Ollama** rodando.

```bash
# .env
APP_USE_REAL_PIPELINE=true
```

```bash
# Terminal 1
APP_USE_REAL_PIPELINE=true uv run uvicorn app.main:app --reload --reload-dir app

# Terminal 2
APP_USE_REAL_PIPELINE=true uv run python scripts/run_worker.py
```

Ollama deve estar acessível em `http://localhost:11434` (configurável via `APP_OLLAMA_URL`).

---

## Uso da interface

1. Acesse http://localhost:3000  
2. Login: `vendedor` / `changeme`  
3. Envie um vídeo (`.mp4`, `.mov`, `.webm` — até 200 MB / 30 min)  
4. Aguarde o processamento (polling a cada 5s)  
5. Leia o relatório evidence-based gerado  

---

## Docker (alternativa para Ollama)

Subir apenas o Ollama via Docker enquanto API/worker rodam no host:

```bash
docker compose up ollama -d
ollama pull llama3:8b   # no host, apontando para localhost:11434
```

O `docker-compose.yml` inclui app + Ollama; para dev local, os 3 terminais acima são mais práticos.

---

## Testes e qualidade

```bash
bash ci/run_tests.sh          # gates completos do Harness
uv run pytest                 # testes unitários + integração + E2E
uv run ruff check .           # lint
uv run mypy .                 # tipos strict
```

---

## Variáveis de ambiente

Copie `.env.example` → `.env`. Principais:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `APP_USE_REAL_PIPELINE` | `false` | Ativa integrações reais |
| `APP_OLLAMA_URL` | `http://localhost:11434` | Endpoint Ollama |
| `APP_WHISPER_MODEL` | `base` | Modelo Faster-Whisper |
| `APP_AUTH_USERNAME` | `vendedor` | Login dev |
| `APP_AUTH_PASSWORD` | `changeme` | Senha dev |

---

## Estrutura de dados local

```
data/
  app.db          # SQLite
  uploads/        # vídeos enviados
  jobs/           # artefatos do pipeline (audio, transcript, signals, report)
```
