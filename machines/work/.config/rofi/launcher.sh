#!/usr/bin/env bash
# Rofi com os itens do GNOME: Configurações e seus painéis (Wi-Fi, Som, Tela…).
set -euo pipefail

# Itens com OnlyShowIn=GNOME só aparecem, e o Configurações só abre, com GNOME no desktop atual.
export XDG_CURRENT_DESKTOP="i3:GNOME"

# Os painéis vêm com NoDisplay=true; cópias visíveis ficam num diretório lido só pelo rofi,
# para não aparecerem duplicadas no app grid da sessão GNOME.
panels="$HOME/.local/share/rofi-gnome/applications"
if [[ ! -d "$panels" || /usr/share/applications -nt "$panels" ]]; then
    rm -rf -- "$panels"
    mkdir -p -- "$panels"
    for f in /usr/share/applications/gnome-*-panel.desktop; do
        sed 's/^NoDisplay=true$/NoDisplay=false/' "$f" > "$panels/${f##*/}"
    done
fi
export XDG_DATA_DIRS="$HOME/.local/share/rofi-gnome:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

exec rofi "$@"
