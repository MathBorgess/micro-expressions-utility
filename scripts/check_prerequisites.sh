#!/usr/bin/env bash
# Verifica pré-requisitos para rodar o projeto localmente (deps Python, Node, ffmpeg, Ollama).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

errors=0
warnings=0

ok() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; warnings=$((warnings + 1)); }
fail() { echo -e "${RED}✗${NC} $1"; errors=$((errors + 1)); }

echo "==> Verificando pré-requisitos em ${ROOT}"
echo

# --- Ferramentas de sistema ---
if command -v uv >/dev/null 2>&1; then
  ok "uv ($(uv --version 2>/dev/null | head -1))"
else
  fail "uv não encontrado — https://docs.astral.sh/uv/getting-started/installation/"
fi

if command -v node >/dev/null 2>&1; then
  ok "Node.js ($(node --version))"
else
  fail "Node.js não encontrado — https://nodejs.org/ (18+)"
fi

if command -v npm >/dev/null 2>&1; then
  ok "npm ($(npm --version))"
else
  fail "npm não encontrado"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg ($(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f1-3))"
else
  fail "ffmpeg não encontrado — necessário para pipeline real (Sprint 2+)"
  echo "    macOS:  brew install ffmpeg"
  echo "    Debian: sudo apt-get install -y ffmpeg"
fi

if command -v ollama >/dev/null 2>&1; then
  ok "ollama ($(ollama --version 2>/dev/null || echo instalado))"
else
  fail "Ollama não encontrado — necessário para relatórios com LLM real"
  echo "    macOS:  brew install ollama"
  echo "    Linux:  https://ollama.com/download"
fi

# --- Ollama rodando ---
if command -v ollama >/dev/null 2>&1; then
  if curl -sf "${APP_OLLAMA_URL:-http://localhost:11434}/api/tags" >/dev/null 2>&1; then
    ok "Ollama API respondendo em ${APP_OLLAMA_URL:-http://localhost:11434}"
    if ollama list 2>/dev/null | grep -q "llama3:8b"; then
      ok "Modelo llama3:8b disponível"
    else
      warn "Modelo llama3:8b não encontrado — rode: ollama pull llama3:8b"
    fi
  else
    warn "Ollama instalado mas API offline — rode: ollama serve (ou brew services start ollama)"
  fi
fi

# --- Python / venv ---
if [[ -d ".venv" ]]; then
  ok "Ambiente virtual .venv"
  if [[ -f ".venv/bin/python" ]]; then
    py_version="$(.venv/bin/python --version 2>&1)"
    if echo "$py_version" | grep -q "3.12"; then
      ok "Python no venv: $py_version"
    else
      warn "Esperado Python 3.12, encontrado: $py_version"
    fi
  fi
else
  warn "Ambiente .venv ausente — rode: uv sync --extra ml"
fi

# --- Frontend deps ---
if [[ -d "frontend/node_modules" ]]; then
  ok "frontend/node_modules"
else
  warn "Deps do frontend ausentes — rode: cd frontend && npm install"
fi

# --- Diretórios de dados ---
for dir in data/uploads data/jobs; do
  if [[ -d "$dir" ]]; then
    ok "Diretório $dir"
  else
    warn "Diretório $dir ausente — será criado no setup"
  fi
done

# --- .env ---
if [[ -f ".env" ]]; then
  ok "Arquivo .env"
else
  warn "Arquivo .env ausente — rode: cp .env.example .env"
fi

echo
if [[ $errors -gt 0 ]]; then
  echo -e "${RED}$errors erro(s), $warnings aviso(s)${NC}"
  exit 1
fi

if [[ $warnings -gt 0 ]]; then
  echo -e "${YELLOW}OK com $warnings aviso(s) — projeto pode rodar (modo dublê ou após corrigir avisos)${NC}"
else
  echo -e "${GREEN}Todos os pré-requisitos OK${NC}"
fi

exit 0
