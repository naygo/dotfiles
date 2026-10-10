#!/usr/bin/env bash
# Alterna entre os engines de teclado do ibus (us <-> br)

case "$(ibus engine)" in
  xkb:us::eng) ibus engine xkb:br::por ;;
  *)           ibus engine xkb:us::eng ;;
esac

# Notificação opcional (dunst já roda no i3)
command -v notify-send >/dev/null && \
  notify-send -t 800 -h string:x-dunst-stack-tag:kblayout \
    "Teclado: $(ibus engine | sed 's/xkb:\([a-z]*\).*/\U\1/')"
