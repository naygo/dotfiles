#!/usr/bin/env bash
# Rofi; no GNOME, também com os itens do Configurações e seus painéis (Wi-Fi, Som, Tela…).
set -euo pipefail

# Sem o Configurações do GNOME (ex.: shikon), é só o Rofi.
if command -v gnome-control-center >/dev/null; then
    # Itens com OnlyShowIn=GNOME só aparecem, e o Configurações só abre, com GNOME no desktop atual.
    export XDG_CURRENT_DESKTOP="i3:GNOME"

    # Os painéis vêm com NoDisplay=true; cópias visíveis ficam num diretório lido só pelo rofi,
    # para não aparecerem duplicadas no app grid da sessão GNOME.
    panels="$HOME/.local/share/rofi-gnome/applications"
    if [[ ! -d "$panels" || /usr/share/applications -nt "$panels" ]]; then
        rm -rf -- "$panels"
        mkdir -p -- "$panels"
        for f in /usr/share/applications/gnome-*-panel.desktop; do
            [[ -f "$f" ]] || continue
            sed 's/^NoDisplay=true$/NoDisplay=false/' "$f" > "$panels/${f##*/}"
        done
    fi
    export XDG_DATA_DIRS="$HOME/.local/share/rofi-gnome:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
fi

exec rofi "$@"
