#!/usr/bin/env bash
# Início da sessão (exec do i3, não roda em reload): monitores e programas da máquina,
# definidos em XRANDR e AUTOSTART no machine.env (dotfiles/machines/<máquina>.env).
env="$HOME/.config/dotfiles/machine.env"
XRANDR=
AUTOSTART=()
[[ -f "$env" ]] && . "$env"
[[ -n "$XRANDR" ]] && bash -c "$XRANDR"
for program in "${AUTOSTART[@]}"; do
    setsid -f "$program" >/dev/null 2>&1
done
