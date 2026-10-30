# ~/.bashrc: executed by bash(1) for non-login shells.

# Se não for interativo, não faz nada
case $- in
    *i*) ;;
      *) return;;
esac

# ─── Histórico ───────────────────────────────────────────────────────────────

HISTCONTROL=ignoreboth
HISTSIZE=5000
HISTFILESIZE=10000
shopt -s histappend

# ─── Opções do shell ─────────────────────────────────────────────────────────

shopt -s checkwinsize
shopt -s globstar

# ─── Less ────────────────────────────────────────────────────────────────────

[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# ─── Chroot ──────────────────────────────────────────────────────────────────

if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# ─── Prompt (PS1) com cursor em bloco forçado ────────────────────────────────

# Cores
_RESET='\[\e[0m\]'
_BOLD='\[\e[1m\]'
_GREEN='\[\e[1;32m\]'
_YELLOW='\[\e[33m\]'
_BLUE='\[\e[35m\]'
_AQUA='\[\e[1;36m\]'
_FG='\[\e[38;2;255;255;255m\]'         # Neutral prompt
_DIM='\[\e[90m\]'
_CURSOR_BLOCK='\[\e[2 q\]'             # Cursor bloco fixo

# Função para mostrar git branch no prompt
_git_branch() {
    local branch
    branch=$(git symbolic-ref --short HEAD 2>/dev/null)
    if [ -n "$branch" ]; then
        local status
        status=$(git status --porcelain 2>/dev/null)
        if [ -n "$status" ]; then
            echo " ${branch}*"
        else
            echo " ${branch}"
        fi
    fi
}

# PS1: user@host:dir [branch] $
PS1="${_CURSOR_BLOCK}${debian_chroot:+($debian_chroot)}"
PS1+="${_GREEN}${_BOLD}\u${_RESET}"
PS1+="${_DIM}@${_RESET}"
PS1+="${_AQUA}${_BOLD}\h${_RESET}"
PS1+="${_DIM}:${_RESET}"
PS1+="${_YELLOW}\w${_RESET}"
PS1+="${_BLUE}\$(_git_branch)${_RESET}"
PS1+="${_FG} \$${_RESET} "

export PS1

# Título da janela
case "$TERM" in
xterm*|rxvt*|kitty*)
    PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD}\007"'
    ;;
esac

# ─── Cores ───────────────────────────────────────────────────────────────────

if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
fi

# ─── Aliases ─────────────────────────────────────────────────────────────────

# Navegação
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# ls com cores e ícones
alias ls='ls --color=auto --group-directories-first'
alias ll='ls -lhF --color=auto --group-directories-first'
alias la='ls -lahF --color=auto --group-directories-first'
alias l='ls -CF'

# grep com cor
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# Confirmação antes de sobrescrever
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -i'

# Atalhos úteis
alias c='clear'
alias h='history'
alias reload='source ~/.bashrc'
alias bashrc='vim ~/.bashrc'
alias i3config='vim ~/.config/i3/config'
alias polybar='vim ~/.config/polybar/config.ini'
alias kittyconf='vim ~/.config/kitty/kitty.conf'

# apt
alias update='sudo apt update && sudo apt upgrade -y'
alias install='sudo apt install'
alias remove='sudo apt remove'
alias search='apt search'

# i3
alias reli3='i3-msg restart'

# ─── Completions ─────────────────────────────────────────────────────────────

if ! shopt -oq posix; then
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi
fi

# ─── Aliases extras (arquivo separado) ───────────────────────────────────────

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
export PATH="$HOME/.local/bin:$PATH"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# Específico de cada PC (caminhos, tokens): fora do git.
[ -f ~/.bashrc.local ] && . ~/.bashrc.local
