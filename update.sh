#!/usr/bin/env bash
# Atualiza o ambiente a partir do repo: git pull + cópia das configs + reload.
#
# Uso: ./update.sh [máquina] [--full] [--no-pull]
#   --full     também roda o FULL_INSTALL da máquina (fontes, dconf…)
#   --no-pull  não faz git pull (só reaplica o que já está no repo)
#
# A configuração é uma só; o que muda por máquina está em machines/<máquina>.env.
# Cada {{NOME}} dos arquivos é trocado pelo valor do .env antes da cópia para o $HOME.
# A máquina é escolhida pelo argumento, por ~/.config/dotfiles-machine
# ou perguntada na primeira execução (e salva nesse arquivo).
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
state="$HOME/.config/dotfiles-machine"
full=0
pull=1
machine=""

for arg in "$@"; do
  case "$arg" in
    --full) full=1 ;;
    --no-pull) pull=0 ;;
    -h|--help) sed -n '2,11p' "${BASH_SOURCE[0]}"; exit 0 ;;
    -*) echo "opção desconhecida: $arg" >&2; exit 1 ;;
    *) machine="$arg" ;;
  esac
done

if [[ -z "$machine" && -f "$state" ]]; then
  machine="$(<"$state")"
fi

if [[ -z "$machine" ]]; then
  echo "Qual máquina é esta?"
  select machine in $(cd "$repo/machines" && ls *.env | sed 's/\.env$//'); do
    [[ -n "$machine" ]] && break
  done
fi

env_file="$repo/machines/$machine.env"
[[ -f "$env_file" ]] || { echo "máquina inexistente: $machine (sem machines/$machine.env)" >&2; exit 1; }

step() { printf '\n==> %s\n' "$*"; }

if (( pull )); then
  step "git pull"
  git -C "$repo" pull --ff-only
fi

# Parâmetros da máquina, exportados para o preenchimento dos {{NOME}}.
set -a
# shellcheck source=/dev/null
source "$env_file"
set +a

# Linhas do i3 com o monitor de cada workspace (WS_OUTPUTS) e o espaço da Polybar no topo,
# só nos workspaces que ficam num monitor com barra.
i3_workspaces() {
  local spec range out ws
  local -A output=()
  for spec in ${WS_OUTPUTS:-}; do
    range=${spec%%:*}; out=${spec#*:}
    for ((ws = ${range%-*}; ws <= ${range#*-}; ws++)); do output[$ws]=$out; done
  done
  for ((ws = 1; ws <= 10; ws++)); do
    [[ -n ${output[$ws]:-} ]] && echo "workspace \$ws$ws output ${output[$ws]}"
  done
  for ((ws = 1; ws <= 10; ws++)); do
    out=${output[$ws]:-}
    if [[ ${BAR_MONITORS:-all} == all || -z $out || -z ${PRIMARY_MONITOR:-} || $out == "$PRIMARY_MONITOR" ]]; then
      echo "workspace \$ws$ws gaps top 38"
    fi
  done
}
I3_WORKSPACES="$(i3_workspaces)"
export I3_WORKSPACES

step "Montando configs de $machine"
stage="$(mktemp -d)"
trap 'rm -rf -- "$stage"' EXIT
excludes=()
for path in ${SKIP:-}; do excludes+=("--exclude=$path"); done
tar -C "$repo" -cf - "${excludes[@]}" .config .local .bashrc .Xresources .xinitrc | tar -C "$stage" -xf -
# Trocar os {{NOME}}; com algum parâmetro faltando, para aqui sem tocar no $HOME.
python3 - "$stage" "$machine" <<'PY'
import os, re, sys
from pathlib import Path
stage, machine = Path(sys.argv[1]), sys.argv[2]
pattern = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
missing = {}
for path in sorted(stage.rglob("*")):
    if path.is_symlink() or not path.is_file():
        continue
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        continue
    if not pattern.search(text):
        continue
    for name in pattern.findall(text):
        if name not in os.environ:
            missing.setdefault(name, []).append(str(path.relative_to(stage)))
    path.write_text(pattern.sub(lambda m: os.environ.get(m.group(1), m.group(0)), text))
if missing:
    for name, files in missing.items():
        print(f"faltando em machines/{machine}.env: {name} (usado em {', '.join(files)})", file=sys.stderr)
    sys.exit(1)
PY

# Lido em tempo de execução por launch.sh, sync-bar-gaps.py e autostart.sh.
mkdir -p "$stage/.config/dotfiles"
cp -- "$env_file" "$stage/.config/dotfiles/machine.env"

# O repo guarda os links *-current no tema dark; manter o tema em uso.
theme="$(readlink "$HOME/.config/i3/theme-current.conf" 2>/dev/null || true)"
theme="${theme#theme-}"; theme="${theme%.conf}"

step "Copiando para \$HOME (sobrescreve o que está lá)"
if [[ -f "$HOME/.bashrc" ]] && ! cmp -s "$stage/.bashrc" "$HOME/.bashrc"; then
  cp -a "$HOME/.bashrc" "$HOME/.bashrc.bak"
fi
cp -a "$stage/." "$HOME/"
echo "$machine" > "$state"

if [[ $theme == light ]]; then
  "$HOME/.local/bin/theme" light >/dev/null
fi

if (( full )) && [[ -n ${FULL_INSTALL:-} ]]; then
  step "Instaladores (--full)"
  PATH="$HOME/.local/bin:$PATH" bash -c "$FULL_INSTALL"
fi

step "Recarregando"
[[ -x "$HOME/.config/i3/apply-theme.sh" ]] && "$HOME/.config/i3/apply-theme.sh"
command -v i3-msg >/dev/null && i3-msg reload >/dev/null || true
command -v dunstctl >/dev/null && dunstctl reload || true

echo
echo "Pronto."
