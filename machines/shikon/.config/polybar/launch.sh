#!/usr/bin/env bash
set -euo pipefail

python3 "$HOME/.config/i3/sync-bar-gaps.py"

pkill -u "$(id -u)" -x polybar || true
for ((attempt = 0; attempt < 50; attempt++)); do
    if ! pgrep -u "$(id -u)" -x polybar >/dev/null; then break; fi
    sleep 0.1
done
if pgrep -u "$(id -u)" -x polybar >/dev/null; then
    echo "A Polybar anterior não encerrou; tente novamente." >&2
    exit 1
fi
for bar in left workspaces right; do
    polybar "$bar" --config="$HOME/.config/polybar/config.ini" &
done
