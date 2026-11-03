# dotfiles

Meu setup de i3 (Polybar, Picom, Kitty, Rofi, Dunst) no tema macOS Graphite, com troca dark/light.
É **uma configuração só** para todos os computadores. O que muda entre eles são valores
(fontes, monitores, comandos de volume, quais janelas têm glass…), todos num único arquivo por
máquina: [`machines/work.env`](machines/work.env) e [`machines/shikon.env`](machines/shikon.env).

## Estrutura

```
.config/ .local/bin/ .bashrc .Xresources .xinitrc   configuração comum, com marcadores {{NOME}}
machines/<máquina>.env                               todos os valores da máquina
wallpapers/                                          papéis de parede compartilhados
```

Nos pontos que mudam por máquina, os configs têm um marcador, por exemplo
`font pango:{{FONT_UI}} 11` no i3 ou `interface = {{NET_INTERFACE}}` na Polybar. O `update.sh`
troca cada marcador pelo valor do `.env` ao copiar para o `$HOME`. Se faltar algum valor, ele
para antes de copiar e diz qual falta e onde é usado. Os scripts que decidem algo em tempo de
execução (`polybar/launch.sh`, `i3/sync-bar-gaps.py`, `i3/autostart.sh`) leem
`~/.config/dotfiles/machine.env`, a cópia do `.env` da máquina.

- **Mudar algo de uma máquina só:** edite o `.env` dela.
- **Mudar em todas:** edite a configuração comum.
- **Novo valor por máquina:** ponha `{{NOME}}` no config e `NOME=...` em todos os `.env`.
- **Nova máquina:** copie um `.env`, ajuste os valores e rode `./update.sh <nome>`.

Os arquivos comuns ficam válidos só depois do `update.sh`; edite sempre no repo, não no `$HOME`.
O `SKIP` do `.env` lista caminhos que a máquina não recebe (o work não recebe as configs do
VS Code/Cursor, GTK, fontconfig e GNOME Terminal do shikon).

## Atualizar

Depois de puxar mudanças, rode o script para reaplicar as configs:

```bash
./update.sh            # git pull + monta as configs da máquina + recarrega i3/dunst
./update.sh --full     # também roda o FULL_INSTALL da máquina (fontes, dconf)
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
