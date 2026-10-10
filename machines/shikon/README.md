# shikon

Configurações deste computador: Debian 13, i3 4.24, Polybar 3.7.2 e Picom 12.5.

- Monitor principal: HDMI-0, 1680×1050; secundário: DP-0, 1920×1080 na vertical.
- Gruvbox Dark; informações à esquerda, workspaces no centro, ações à direita.
- Aplicativos com opacidade de 90%, blur e cantos de 16 px.
- Pílulas com fundos translúcidos e composição SOURCE para evitar linhas nas junções.
- Fontes: JetBrains Mono e Symbols Nerd Font/Mono.
- Super+Shift+B: esconder/mostrar as barras; Super+Shift+R: recarregar o i3.

## Arquivos

`.config/` contém i3, Polybar, Picom (incluindo shader) e Kitty.
`.screenlayout/monitors.sh` define os monitores; `.Xresources` configura recursos do X11.
As configurações de monitores, interface de rede e caminhos são específicas deste PC.

## Restaurar

Faça backup das configurações existentes. Dentro desta pasta:

```bash
cp -a .config/. "$HOME/.config/"
mkdir -p "$HOME/.screenlayout"
cp -a .screenlayout/monitors.sh "$HOME/.screenlayout/"
cp -a .Xresources "$HOME/.Xresources"
~/.config/i3/apply-theme.sh
```

Os scripts dos popovers precisam de Python 3, PyGObject/GTK 3, sensors,
nvidia-smi (para GPU NVIDIA), upower e das ferramentas pactl/df.
Ações da barra usam CopyQ, Flameshot, xclip, dunstctl e pavucontrol.
O launcher do i3 usa Rofi; a sessão também inicia feh, nm-applet e blueman-applet.

As credenciais de Claude/Codex permanecem locais. O popover de uso lê os
arquivos locais desses clientes quando aberto; eles não estão neste snapshot.
