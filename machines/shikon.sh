# Hooks do update.sh para o shikon (lido com `source`; $REPO e $HOME já definidos).

# Instaladores pesados, só com --full.
full_install() {
    "$HOME/.local/bin/install-mac-fonts"
    dconf load /org/gnome/terminal/ < "$HOME/.config/gnome-terminal/settings.dconf"
}
