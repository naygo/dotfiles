# Hooks do update.sh para o work (lido com `source`; $REPO e $HOME já definidos).

# Instaladores pesados, só com --full.
full_install() {
    "$HOME/.local/bin/install-nerd-symbols"
}
