#!/usr/bin/env bash
# Telemetria de memória (mprof). Gate: pico de RAM < 2.5 GB durante o processamento.
# Mede o pipeline com os dublês (rápido). Para o pipeline real:
#   APP_USE_REAL_PIPELINE=true uv sync --extra ml && bash ci/mprof_check.sh
set -euo pipefail
cd "$(dirname "$0")/.."

LIMIT_MIB=2560

echo "[mprof_check] Medindo pico de memória do pipeline..."
rm -f mprofile_*.dat
uv run mprof run -C scripts/mprof_target.py >/dev/null
PEAK="$(uv run mprof peak | awk '/MiB/ {print $(NF-1)}')"
rm -f mprofile_*.dat

echo "[mprof_check] Pico: ${PEAK} MiB (limite ${LIMIT_MIB} MiB)"
if (( ${PEAK%.*} > LIMIT_MIB )); then
  echo "[mprof_check] REPROVADO: pico acima do limite."
  exit 1
fi
echo "[mprof_check] OK. ✅"
