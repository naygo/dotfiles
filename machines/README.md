# Máquinas

Cada pasta tem só o que difere da configuração comum: os arquivos de parâmetros (`machine.*`,
veja a tabela no [README principal](../README.md)) e os arquivos que só existem naquele computador.
A estrutura é a do `$HOME`; o `update.sh` copia a pasta por cima da configuração comum.
O `<máquina>.sh` ao lado define o `full_install`, rodado pelo `./update.sh --full`.

**Nova máquina:** copie uma das pastas e o `.sh`, ajuste os valores e rode `./update.sh <nome>`.

## shikon

PC com Debian 13, i3 4.24, Polybar 3.7.2 e Picom 12.5.

- Monitores (`.screenlayout/monitors.sh`): Apple Cinema HDMI-0 1680×1050 principal e Samsung
  DP-0 1920×1080 240 Hz na vertical. Workspaces 1-6 no HDMI-0 e 7-10 no DP-0; só o HDMI-0 tem
  Polybar (`BAR_MONITORS=primary`). Rede cabeada `enp5s0`.
- Fontes: SF Pro Text nas interfaces e SF Mono 10 no Kitty e no GNOME Terminal; Font Awesome nos
  ícones das ações da barra. `--full` roda `install-mac-fonts`, que baixa as fontes dos arquivos
  oficiais da Apple (usa curl, fontconfig e 7zip, obtido pelo apt se faltar) e carrega o perfil do
  GNOME Terminal. Os arquivos das fontes não ficam no repo.
- VS Code e Cursor com Menlo no editor (SF Mono como alternativa) e SF Mono no terminal integrado.
  A Menlo é instalada à parte: copie `Menlo-Regular.ttf` para `~/.local/share/fonts/menlo/` e rode `fc-cache -f`.
- Glass do Picom em todas as janelas, menos Minecraft, Google Chrome e Stremio.
- Volume com `pactl`, rede com nm-applet, Bluetooth com blueman-applet, arquivos no Thunar,
  screenshot com `Ctrl+Shift+4`, brilho com `brightnessctl`.
- Papel de parede por monitor via `~/.local/share/desktop-theme/set-wallpapers.sh`; `$mod+Shift+w`
  escolhe um dos de [`wallpapers/`](../wallpapers/README.md) até o próximo reinício do i3.
- Exclusivos: GTK 3/4, fontconfig (SF como sans/mono padrão), GNOME Terminal, VS Code, Cursor.

## work

Notebook da empresa: Ubuntu 26.04 com GNOME, i3 4.25, Polybar 3.7.2, Rofi 2.0 e Picom.
Usa o que o GNOME já fornece em vez de pacotes extras.

- Monitores: notebook eDP-1 (1366×768) e externo HDMI-1, cada um com sua Polybar
  (`BAR_MONITORS=all`; a bandeja fica na do principal). Workspaces não são presos a monitores;
  ao iniciar, o principal abre o 1 e o externo o 2 (`i3/init-workspaces.sh`). Wi-Fi `wlp0s20f3`.
- Fontes: Ubuntu Sans nas interfaces e Ubuntu Sans Mono no Kitty (SF Pro/SF Mono não podem ser
  instaladas aqui); Symbols Nerd Font nos ícones (`--full` roda `install-nerd-symbols`).
- Glass do Picom só em kitty, VS Code, Rofi, Dunst e Obsidian; os demais ficam opacos.
- Rofi com os painéis do Configurações (Wi-Fi, Som, Tela…): o `rofi/launcher.sh` comum os inclui
  sempre que o `gnome-control-center` existe. Volume e rede da barra abrem esses painéis.
- Volume com `wpctl` (PipeWire); Bluetooth pelo Configurações, com o i3 iniciando o `gsd-rfkill`
  (sem ele o painel não encontra o adaptador).
- Brilho: `i3/brightness.sh`, que usa o helper do mutter via `pkexec` e mostra o nível no Dunst
  (o `gsd-power` desta versão só controla o brilho do teclado).
- Screenshot: PrtSc ou botão da barra, Flameshot copiando para a área de transferência. `$mod+t` abre o Nautilus.
- Papel de parede: `hilux-98.jpg` de [`wallpapers/`](../wallpapers/README.md), centralizado; `$mod+Shift+w` escolhe outro.
- Exclusivo: `.xinitrc`.
