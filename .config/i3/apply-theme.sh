#!/usr/bin/env bash
set -euo pipefail
i3 -C -c "$HOME/.config/i3/config"
i3-msg reload
python3 "$HOME/.config/i3/sync-grouped-windows.py" >/tmp/i3-groups.log 2>&1 &
pkill -u "$(id -u)" -x picom || true
for ((attempt = 0; attempt < 50; attempt++)); do
    if ! pgrep -u "$(id -u)" -x picom >/dev/null; then break; fi
    sleep 0.1
done
if pgrep -u "$(id -u)" -x picom >/dev/null; then
    echo "O Picom anterior não encerrou; tente novamente." >&2
    exit 1
fi
picom --config "$HOME/.config/picom/picom.conf" --daemon
