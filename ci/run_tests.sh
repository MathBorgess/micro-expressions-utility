#!/usr/bin/env bash
# Gates do Harness (execução local). Para no primeiro gate que reprovar.
# Alvo: pipeline completo < 5 min.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/5] Validação de dependências (allowlist)"
uv run python ci/validate_requirements.py

echo "==> [2/5] Ruff (lint)"
uv run ruff check .

echo "==> [3/5] Ruff (format --check)"
uv run ruff format --check .

echo "==> [4/5] Mypy (strict)"
uv run mypy .

echo "==> [5/5] Pytest (+ cobertura >= 70%)"
uv run pytest

echo "==> Todos os gates do Harness passaram. ✅"
