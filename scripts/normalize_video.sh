#!/usr/bin/env bash
# Normaliza um vídeo para CFR de 24 FPS e codec H.264 (questionário Q34).
# Uso: scripts/normalize_video.sh <entrada> <saida.mp4>
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "uso: $0 <entrada> <saida.mp4>" >&2
  exit 2
fi

INPUT="$1"
OUTPUT="$2"

ffmpeg -y -i "$INPUT" -r 24 -vcodec libx264 "$OUTPUT"
echo "normalizado: $OUTPUT (24 FPS CFR, H.264)"
