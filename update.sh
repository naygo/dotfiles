#!/usr/bin/env bash
# Atualiza o ambiente a partir do repo: git pull + cópia das configs + reload.
#
# Uso: ./update.sh [máquina] [--full] [--no-pull]
#   --full     também roda os instaladores pesados da máquina (fontes, dconf…)
#   --no-pull  não faz git pull (só reaplica o que já está no repo)
#
# Copia a configuração comum (raiz do repo) e, por cima, machines/<máquina>/,
# que tem os parâmetros (machine.conf, machine.ini…) e os arquivos exclusivos.
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
    -h|--help) sed -n '2,11p' "${BASH_SOURCE[0]}"; exit 0 ;;
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

OVERLAY="$REPO/machines/$MACHINE"
[[ -d "$OVERLAY" ]] || { echo "máquina inexistente: $MACHINE" >&2; exit 1; }
mkdir -p "$(dirname "$STATE")"
echo "$MACHINE" > "$STATE"

full_install() { :; }
[[ -f "$REPO/machines/$MACHINE.sh" ]] && source "$REPO/machines/$MACHINE.sh"

step() { printf '\n==> %s\n' "$*"; }

if (( PULL )); then
  step "git pull"
  git -C "$REPO" pull --ff-only
fi

# O repo guarda os links *-current no tema dark; manter o tema em uso.
theme="$(readlink "$HOME/.config/i3/theme-current.conf" 2>/dev/null || true)"
theme="${theme#theme-}"; theme="${theme%.conf}"

step "Copiando configs comuns + $MACHINE (sobrescreve o que está em \$HOME)"
cp -a "$REPO/.config/." "$HOME/.config/"
cp -a "$REPO/.Xresources" "$HOME/"
mkdir -p "$HOME/.local/bin"
cp -a "$REPO/.local/bin/." "$HOME/.local/bin/"

if [[ -f "$HOME/.bashrc" ]] && ! cmp -s "$REPO/.bashrc" "$HOME/.bashrc"; then
  cp -a "$HOME/.bashrc" "$HOME/.bashrc.bak"
fi
cp -a "$REPO/.bashrc" "$HOME/.bashrc"

# Parâmetros e arquivos exclusivos da máquina, na mesma estrutura do $HOME.
cp -a "$OVERLAY/." "$HOME/"

if [[ $theme == light ]]; then
  "$HOME/.local/bin/theme" light >/dev/null
fi

if (( FULL )); then
  step "Instaladores (--full)"
  full_install
fi

step "Recarregando"
[[ -x "$HOME/.config/i3/apply-theme.sh" ]] && "$HOME/.config/i3/apply-theme.sh"
command -v i3-msg >/dev/null && i3-msg reload >/dev/null || true
command -v dunstctl >/dev/null && dunstctl reload || true

echo
echo "Pronto."
