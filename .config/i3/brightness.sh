#!/usr/bin/env bash
# Brilho da tela pelo helper do GNOME (mutter); o polkit libera a sessão ativa sem senha.
# Uso: brightness.sh up|down
set -euo pipefail

step=5
backlight=$(ls -d /sys/class/backlight/* | head -n1)
max=$(<"$backlight/max_brightness")
current=$(<"$backlight/brightness")
percent=$(( (current * 100 + max / 2) / max ))

case "${1:-}" in
    up)   percent=$(( percent + step > 100 ? 100 : percent + step )) ;;
    down) percent=$(( percent - step < 1 ? 1 : percent - step )) ;;
    *)    echo "Uso: $0 up|down" >&2; exit 1 ;;
esac

# O helper espera o caminho real do dispositivo, não o link em /sys/class/backlight.
pkexec /usr/libexec/mutter-backlight-helper "$(realpath "$backlight")" $(( max * percent / 100 ))

notify-send -a brightness -u low -t 1200 -h string:x-dunst-stack-tag:brightness \
    -h "int:value:$percent" "󰃠  Brilho" "$percent%"
