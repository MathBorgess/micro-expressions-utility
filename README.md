# micro-expressions-utility

Ferramenta local-first de análise comportamental de reuniões de vendas. O sistema recebe um vídeo de reunião, extrai o áudio, transcreve a fala, detecta sinais não-verbais (microexpressões via MediaPipe) e gera um relatório em Markdown com insights sobre o comportamento dos participantes — tudo rodando localmente, sem enviar dados para nuvem.

O pipeline usa **FastAPI** no backend, **Next.js** no frontend e **Ollama** para geração do relatório com LLM local. Por padrão, roda com dublês determinísticos no lugar dos modelos de IA, o que permite testar o fluxo completo sem GPU ou dependências pesadas.

---

## Pré-requisitos

- **Python 3.12** (exatamente — MediaPipe não suporta 3.13+)
- **uv** — gerenciador de pacotes Python
- **Node.js** 18+

### Instalar o uv (caso não tenha)

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Como rodar

O projeto precisa de **3 terminais** abertos simultaneamente.

### Configuração inicial (apenas na primeira vez)

```bash
cp .env.example .env
mkdir -p data/uploads
uv sync
```

---

### Terminal 1 — Backend (API)

```bash
uv run uvicorn app.main:app --reload --reload-dir app
```

API disponível em: http://localhost:8000  
Documentação interativa: http://localhost:8000/docs

---

### Terminal 2 — Worker (processamento dos vídeos)

```bash
uv run python -c "
from app.db import engine
from app.config import get_settings
from app.workers.manager import JobRunner
import time

settings = get_settings()
runner = JobRunner(engine, settings)
print('Worker iniciado, aguardando jobs...')
while True:
    result = runner.run_once()
    if result:
        print(f'Job processado: {result}')
    time.sleep(2)
"
```

O worker fica em loop verificando a fila a cada 2 segundos e processa os vídeos enviados.

---

### Terminal 3 — Frontend (interface web)

```bash
cd frontend
npm install   # apenas na primeira vez
npm run dev
```

Interface disponível em: http://localhost:3000

---

## Uso

1. Acesse **http://localhost:3000**
2. Faça login com as credenciais padrão:
   - **Usuário:** `vendedor`
   - **Senha:** `changeme`
3. Envie um vídeo de reunião (`.mp4`, `.mov` ou `.webm` — até 200 MB / 30 minutos)
4. Aguarde o processamento (o status atualiza automaticamente a cada 5s)
5. Visualize o relatório gerado

> Para resultados mais ricos, use vídeos com áudio de conversas de vendas — o pipeline detecta palavras-chave como "produto" e "preço" na transcrição.

---

## Pipeline com modelos reais (opcional)

Por padrão o projeto usa dublês no lugar de MediaPipe/Whisper. Para ativar o pipeline real:

```bash
uv sync --extra ml
APP_USE_REAL_PIPELINE=true uv run uvicorn app.main:app --reload --reload-dir app
```

Requer Ollama rodando localmente (`http://localhost:11434`).

---

## Testes

```bash
uv run pytest                # 73 testes + relatório de cobertura
uv run ruff check .          # lint
uv run mypy --strict .       # checagem de tipos
```

Cobertura atual: **96%** | Memória em pico: **~30 MiB**
