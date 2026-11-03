#!/usr/bin/env bash
# Abre o workspace 1 no notebook e o 2 em cada monitor externo, para nenhum
# começar vazio. Roda só no início da sessão (exec), não em cada reload do i3.
primary=eDP-1
workspace=1
i3-msg -q "focus output $primary; workspace number $workspace"
for output in $(xrandr --query | awk '/ connected/ {print $1}'); do
    [[ $output == "$primary" ]] && continue
    workspace=$((workspace + 1))
    i3-msg -q "focus output $output; workspace number $workspace"
done
i3-msg -q "focus output $primary"
