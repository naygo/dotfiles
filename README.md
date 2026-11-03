# dotfiles

Meu setup de i3 (Polybar, Picom, Kitty, Rofi, Dunst) no tema macOS Graphite, com troca dark/light.
É **uma configuração só** para todos os computadores; o que muda entre eles fica em arquivos
de parâmetros pequenos, incluídos em pontos fixos da configuração comum.

## Estrutura

```
.config/ .local/bin/ .bashrc .Xresources   configuração comum (igual em todas as máquinas)
machines/<máquina>/                        parâmetros + arquivos exclusivos, na estrutura do $HOME
machines/<máquina>.sh                      hooks do update.sh (instaladores do --full)
wallpapers/                                papéis de parede compartilhados
```

Cada ferramenta inclui o arquivo da máquina com o mecanismo nativo dela:

| Config comum | Inclui | O que a máquina define |
| --- | --- | --- |
| `i3/config` | `i3/machine.conf` | fonte, programas iniciados, atalhos de volume/brilho/screenshot, gerenciador de arquivos, monitores dos workspaces |
| `polybar/config.ini` | `polybar/machine.ini` | seção `[machine]` (fontes, ação do som) e o `[module/network]` (herda de `network-base`) |
| `polybar/launch.sh`, `i3/sync-bar-gaps.py` | `polybar/machine.env` | `BAR_MONITORS` (`all` ou `primary`) e `PRIMARY_MONITOR` |
| `picom/picom.conf` | `picom/machine.conf` | regras de glass (quais janelas ficam translúcidas) |
| `kitty/kitty.conf` | `kitty/machine.conf` | fonte do terminal |
| `dunst/dunstrc` | `dunst/dunstrc.d/machine.conf` | fonte das notificações |
| `rofi/macos-glass.rasi` | `rofi/machine.rasi` | fonte (`ui-font`) e tema de ícones |

Para mudar algo de uma máquina só, edite o arquivo dela em `machines/<máquina>/`; para mudar em
todas, edite a configuração comum. Os valores atuais e as particularidades de cada computador estão
em [`machines/README.md`](machines/README.md).

## Atualizar

Depois de puxar mudanças, rode o script para reaplicar as configs:

```bash
./update.sh            # git pull + copia comum + máquina + recarrega i3/dunst
./update.sh --full     # também roda os instaladores pesados da máquina (fontes, dconf)
./update.sh --no-pull  # não faz git pull
```

A primeira execução pergunta qual máquina é esta (`work` ou `shikon`) e salva em `~/.config/dotfiles-machine`.
A cópia sobrescreve os arquivos em `$HOME` (o `.bashrc` anterior vai para `.bashrc.bak`), então
traga para o repo o que tiver editado lá antes. O tema dark/light em uso é mantido.

## Tema claro/escuro

`Super+Shift+T` (ou `theme [dark|light|toggle]`) alterna entre dark e light: troca os links `*-current`
(i3, Polybar, Dunst, Rofi e Kitty) e recarrega tudo, o GTK e o esquema de cores do GNOME. As paletas
ficam em `theme-*.conf` e `colors-*` (`.ini`, `.conf`, `.rasi`). O padrão do repo é dark.

## Dependências

i3, Picom, Kitty, Polybar, Rofi, Dunst, CopyQ, Flameshot, xclip, feh e xrandr.
Os popovers da Polybar usam Python 3, PyGObject/GTK 3, sensors, upower, pactl e df (e nvidia-smi
com GPU NVIDIA); o ajuste dos grupos usa xprop (x11-utils); o dos ícones, `/usr/bin/python3`,
PyGObject/GdkPixbuf e libX11. Os símbolos ✳ ◑ dos títulos usam Noto Sans Symbols2
(`fonts-noto-core`). O volume da barra precisa do
[polybar-pulseaudio-control](https://github.com/marioortizmanero/polybar-pulseaudio-control).

As credenciais de Claude/Codex ficam locais; o popover de uso só lê os arquivos desses clientes.

Testes do ajuste de margens da barra: `cd .config/i3 && python3 -m unittest discover -s tests`.
