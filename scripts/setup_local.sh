#!/usr/bin/env bash
# Configura o ambiente local: uv, deps ML, ffmpeg, Ollama, modelo LLM, frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OLLAMA_URL="${APP_OLLAMA_URL:-http://localhost:11434}"
OLLAMA_MODEL="${APP_OLLAMA_MODEL:-llama3:8b}"
SKIP_MODEL_PULL=false

for arg in "$@"; do
  case "$arg" in
    --skip-model-pull) SKIP_MODEL_PULL=true ;;
    -h|--help)
      echo "Uso: bash scripts/setup_local.sh [--skip-model-pull]"
      echo "  --skip-model-pull  Não baixa llama3:8b (útil se já tiver o modelo ou modo dublê)"
      exit 0
      ;;
  esac
done

echo "==> Setup local — micro-expressions-utility"
echo "    Raiz: $ROOT"
echo

install_ffmpeg() {
  if command -v ffmpeg >/dev/null 2>&1; then
    return 0
  fi
  echo "==> Instalando ffmpeg..."
  case "$(uname -s)" in
    Darwin)
      if ! command -v brew >/dev/null 2>&1; then
        echo "Erro: Homebrew necessário para instalar ffmpeg no macOS."
        echo "      https://brew.sh/"
        exit 1
      fi
      brew install ffmpeg
      ;;
    Linux)
      if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y ffmpeg curl
      else
        echo "Instale ffmpeg manualmente e rode este script novamente."
        exit 1
      fi
      ;;
    *)
      echo "SO não suportado para instalação automática de ffmpeg."
      exit 1
      ;;
  esac
}

install_ollama() {
  if command -v ollama >/dev/null 2>&1; then
    return 0
  fi
  echo "==> Instalando Ollama..."
  case "$(uname -s)" in
    Darwin)
      if ! command -v brew >/dev/null 2>&1; then
        echo "Erro: Homebrew necessário para instalar Ollama no macOS."
        exit 1
      fi
      brew install ollama
      ;;
    Linux)
      curl -fsSL https://ollama.com/install.sh | sh
      ;;
    *)
      echo "Instale Ollama manualmente: https://ollama.com/download"
      exit 1
      ;;
  esac
}

ensure_ollama_running() {
  if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    echo "==> Ollama já está rodando em ${OLLAMA_URL}"
    return 0
  fi

  echo "==> Iniciando Ollama..."
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    brew services start ollama 2>/dev/null || true
    sleep 2
  fi

  if ! curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    echo "    Subindo ollama serve em background..."
    nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
    sleep 3
  fi

  if ! curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    echo "Erro: não foi possível conectar ao Ollama em ${OLLAMA_URL}"
    echo "      Tente manualmente: ollama serve"
    exit 1
  fi
  echo "==> Ollama respondendo em ${OLLAMA_URL}"
}

pull_ollama_model() {
  if [[ "$SKIP_MODEL_PULL" == "true" ]]; then
    echo "==> Pulando download do modelo (--skip-model-pull)"
    return 0
  fi
  if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "${OLLAMA_MODEL}"; then
    echo "==> Modelo ${OLLAMA_MODEL} já disponível"
    return 0
  fi
  echo "==> Baixando modelo ${OLLAMA_MODEL} (~4.7 GB na primeira vez)..."
  ollama pull "${OLLAMA_MODEL}"
}

# --- uv ---
if ! command -v uv >/dev/null 2>&1; then
  echo "==> Instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

install_ffmpeg
install_ollama

echo "==> Sincronizando dependências Python (inclui stack ML)..."
uv sync --extra ml

echo "==> Criando diretórios de dados..."
mkdir -p data/uploads data/jobs

if [[ ! -f .env ]]; then
  echo "==> Criando .env a partir de .env.example..."
  cp .env.example .env
else
  echo "==> .env já existe (mantido)"
fi

ensure_ollama_running
pull_ollama_model

echo "==> Instalando dependências do frontend..."
(cd frontend && npm install)

echo
echo "==> Verificação final..."
bash scripts/check_prerequisites.sh

echo
echo "============================================================"
echo " Setup concluído. Para rodar o projeto (3 terminais):"
echo
echo "  Terminal 1 — API:"
echo "    uv run uvicorn app.main:app --reload --reload-dir app"
echo
echo "  Terminal 2 — Worker:"
echo "    uv run python scripts/run_worker.py"
echo
echo "  Terminal 3 — Frontend:"
echo "    cd frontend && npm run dev"
echo
echo " Pipeline real (MediaPipe + Whisper + Ollama):"
echo "    APP_USE_REAL_PIPELINE=true uv run uvicorn app.main:app --reload --reload-dir app"
echo "    APP_USE_REAL_PIPELINE=true uv run python scripts/run_worker.py"
echo
echo " Login: vendedor / changeme — http://localhost:3000"
echo "============================================================"
