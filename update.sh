#!/usr/bin/env bash
# Atualiza o ambiente a partir do repo: git pull + copia das configs + reload.
#
# Uso: ./update.sh [work|shikon] [--full] [--no-pull]
#   --full     também roda os instaladores pesados (fontes, dconf, gsettings)
#   --no-pull  não faz git pull (só reaplica o que já está no repo)
#
# A máquina é escolhida pelo argumento, por ~/.config/dotfiles-machine
# ou perguntada na primeira execução (e salva nesse arquivo).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HOME/.config/dotfiles-machine"
FULL=0
PULL=1
MACHINE=""

for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    --no-pull) PULL=0 ;;
    -h|--help) sed -n '2,9p' "${BASH_SOURCE[0]}"; exit 0 ;;
    -*) echo "opção desconhecida: $arg" >&2; exit 1 ;;
    *) MACHINE="$arg" ;;
  esac
done

if [[ -z "$MACHINE" && -f "$STATE" ]]; then
  MACHINE="$(<"$STATE")"
fi

if [[ -z "$MACHINE" ]]; then
  echo "Qual máquina é esta?"
  select MACHINE in $(cd "$REPO/machines" && ls -d */ | tr -d /); do
    [[ -n "$MACHINE" ]] && break
  done
fi

SRC="$REPO/machines/$MACHINE"
[[ -d "$SRC" ]] || { echo "máquina inexistente: $MACHINE" >&2; exit 1; }
mkdir -p "$(dirname "$STATE")"
echo "$MACHINE" > "$STATE"

step() { printf '\n==> %s\n' "$*"; }

if (( PULL )); then
  step "git pull"
  git -C "$REPO" pull --ff-only
fi

step "Copiando configs de $MACHINE (sobrescreve o que está em \$HOME)"
cd "$SRC"
cp -a .config/. "$HOME/.config/"
[[ -f .Xresources ]] && cp -a .Xresources "$HOME/"
[[ -f .xinitrc ]] && cp -a .xinitrc "$HOME/"

if [[ -f "$REPO/.bashrc" ]]; then
  if [[ -f "$HOME/.bashrc" ]] && ! cmp -s "$REPO/.bashrc" "$HOME/.bashrc"; then
    cp -a "$HOME/.bashrc" "$HOME/.bashrc.bak"
  fi
  cp -a "$REPO/.bashrc" "$HOME/.bashrc"
fi

mkdir -p "$HOME/.local/bin"
cp -a "$REPO/.local/bin/." "$HOME/.local/bin/"
if [[ -d .local/bin ]]; then
  cp -a .local/bin/. "$HOME/.local/bin/"
fi

if [[ -d .screenlayout ]]; then
  mkdir -p "$HOME/.screenlayout"
  cp -a .screenlayout/. "$HOME/.screenlayout/"
fi

if (( FULL )); then
  step "Instaladores (--full)"
  case "$MACHINE" in
    work)
      "$HOME/.local/bin/install-nerd-symbols"
      ;;
    shikon)
      "$HOME/.local/bin/install-mac-fonts"
      gsettings set org.gnome.desktop.interface monospace-font-name "SF Mono 10"
      dconf load /org/gnome/terminal/ < .config/gnome-terminal/settings.dconf
      ;;
  esac
fi

step "Recarregando"
[[ -x "$HOME/.config/i3/apply-theme.sh" ]] && "$HOME/.config/i3/apply-theme.sh"
command -v i3-msg >/dev/null && i3-msg reload >/dev/null || true
command -v dunstctl >/dev/null && dunstctl reload || true

echo
echo "Pronto."
