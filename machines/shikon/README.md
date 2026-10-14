# shikon

Configurações deste computador: Debian 13, i3 4.24, Polybar 3.7.2 e Picom 12.5.

- Monitor principal: HDMI-0, 1680×1050; secundário: DP-0, 1920×1080 na vertical.
- Gruvbox Dark; informações à esquerda, workspaces no centro, ações à direita.
- Aplicativos com opacidade de 90%, blur e cantos de 16 px.
- Pílulas com fundos translúcidos e composição SOURCE para evitar linhas nas junções.
- Notificações Gruvbox com ícones compactos, cantos de 16 px e glass do Picom.
- Launcher Rofi minimalista e centralizado, com busca simples, ícones compactos e seleção discreta.
- Painel de volume e terminais abrem flutuando e centralizados.
- Workspaces com números centralizados em espaços iguais, ativo amarelo e inativos com contraste maior.
- Grupos de abas com cantos superiores na faixa e inferiores no conteúdo; junção reta, sem sombra entre as peças.
- Abas ativas douradas, títulos com mais espaço e melhor contraste.
- Fontes: SF Pro Text nas interfaces, SF Mono tamanho 10 no Kitty e no GNOME Terminal; Symbols Nerd Font/Mono nos ícones.
- VS Code e Cursor com Menlo no editor (SF Mono como alternativa) e SF Mono no terminal integrado.
- Dia e horário em amarelo e semibold; pílulas sem sombras retangulares e com extremidades alinhadas.
- Ícones das janelas reduzidos dentro de uma área transparente, preservando fonte e padding das abas.
- Super+Shift+B: esconder/mostrar as barras e liberar/restaurar o espaço das janelas; Super+Shift+R: recarregar o i3.

## Arquivos

`.config/` contém i3, Polybar, Picom (incluindo shaders), Kitty, GNOME Terminal, VS Code, Cursor, Dunst, Rofi, GTK e Fontconfig.
`.local/bin/install-mac-fonts` baixa e instala as fontes a partir dos arquivos oficiais da Apple; os arquivos das fontes não são incluídos no repositório.
A Menlo é instalada separadamente: copie `Menlo-Regular.ttf` para `~/.local/share/fonts/menlo/` (crie a pasta se necessário) e execute `fc-cache -f`. O arquivo da fonte não é incluído no repositório. Sem Menlo, os editores usam SF Mono.
`.screenlayout/monitors.sh` define os monitores; `.Xresources` configura recursos do X11.
As configurações de monitores, interface de rede e caminhos são específicas deste PC.

## Restaurar

Faça backup das configurações existentes. Dentro desta pasta:

```bash
cp -a .config/. "$HOME/.config/"
mkdir -p "$HOME/.local/bin"
cp -a .local/bin/install-mac-fonts "$HOME/.local/bin/"
~/.local/bin/install-mac-fonts
gsettings set org.gnome.desktop.interface monospace-font-name "SF Mono 10"
dconf load /org/gnome/terminal/ < .config/gnome-terminal/settings.dconf
mkdir -p "$HOME/.screenlayout"
cp -a .screenlayout/monitors.sh "$HOME/.screenlayout/"
cp -a .Xresources "$HOME/.Xresources"
~/.config/i3/apply-theme.sh
/usr/bin/python3 ~/.config/i3/sync-window-icons.py &
dunstctl reload
```

Os scripts dos popovers precisam de Python 3, PyGObject/GTK 3, sensors,
nvidia-smi (para GPU NVIDIA), upower e das ferramentas pactl/df.
O ajuste automático dos grupos usa xprop (x11-utils).
O ajuste dos ícones usa `/usr/bin/python3`, PyGObject/GdkPixbuf e libX11.
O instalador das fontes usa curl, fontconfig e 7zip (obtido localmente pelo apt caso não esteja instalado).
Ações da barra usam CopyQ, Flameshot, xclip, dunstctl e pavucontrol.
O launcher do i3 usa Rofi; a sessão também inicia feh, nm-applet e blueman-applet.

As credenciais de Claude/Codex permanecem locais. O popover de uso lê os
arquivos locais desses clientes quando aberto; eles não estão neste snapshot.
