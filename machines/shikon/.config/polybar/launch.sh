#!/usr/bin/env bash
set -euo pipefail

# Limpeza única do painel antigo, que não tinha fechamento confiável.
if [[ -f "$HOME/.config/polybar/close-old-vitals-once" ]]; then
    pkill -u "$(id -u)" -f '/home/naygo/\.config/polybar/scripts/vitals_popover\.py([[:space:]]|$)' || true
    rm -f -- "$HOME/.config/polybar/close-old-vitals-once"
fi

python3 "$HOME/.config/i3/sync-bar-gaps.py" --reset

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
# Ajustar também os workspaces criados enquanto a barra estiver escondida.
python3 "$HOME/.config/i3/sync-bar-gaps.py" --watch &
