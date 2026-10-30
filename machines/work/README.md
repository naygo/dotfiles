# work

Notebook da empresa: Ubuntu 26.04 com GNOME, i3 4.25, Polybar 3.7.2, Rofi 2.0 e Picom.
Baseado no [shikon](../shikon/README.md), adaptado para usar o que o GNOME já fornece
em vez de pacotes extras.

- Monitor único: eDP-1, 1366×768; interface de rede `wlp0s20f3`.
- Mesmo tema macOS Graphite do shikon na Polybar, Rofi, Dunst, Kitty e i3.
- Fontes: Ubuntu Sans nas interfaces e Ubuntu Sans Mono no Kitty (SF Pro/SF Mono não podem
  ser instaladas aqui); Symbols Nerd Font nos ícones.
- Rofi (`$mod+d` e logo da barra) via `rofi/launcher.sh`: roda com `XDG_CURRENT_DESKTOP=i3:GNOME`
  e lista o Configurações e seus painéis (Wi-Fi, Som, Tela…). As cópias visíveis dos painéis ficam
  em `~/.local/share/rofi-gnome/`, lida só pelo Rofi, e são geradas automaticamente.
- Volume e rede da barra abrem os painéis do Configurações (no lugar de pavucontrol e nm-applet);
  teclas de volume usam `wpctl` (PipeWire).
- Bluetooth pelo painel do Configurações; o i3 inicia o `gsd-rfkill`, sem o qual o painel
  não encontra o adaptador e pede um dongle.
- Teclas de brilho: `i3/brightness.sh`, que usa o helper do mutter via `pkexec` (o polkit libera a
  sessão ativa sem senha) e mostra o nível no Dunst. O `gsd-power` desta versão só controla o
  brilho do teclado.
- Screenshot: PrtSc ou botão da barra, Flameshot copiando para a área de transferência.
- `$mod+t` abre o Nautilus.
- Papel de parede: recorte quadrado de 480 px da Hilux 98 (`i3/wallpaper.jpg`), no meio da tela
  sobre fundo preto pelo `feh --bg-center`.

## Restaurar

Faça backup das configurações existentes. Dentro desta pasta:

```bash
sudo apt install flameshot
cp -a .config/. "$HOME/.config/"
mkdir -p "$HOME/.local/bin"
cp -a .local/bin/install-nerd-symbols "$HOME/.local/bin/"
~/.local/bin/install-nerd-symbols
cp -a .Xresources .xinitrc "$HOME/"
~/.config/i3/apply-theme.sh
dunstctl reload
```

Também são necessários i3, Picom, Kitty, Polybar, Rofi, Dunst, CopyQ, xclip e feh.
A interface de rede e o monitor são específicos deste notebook.
