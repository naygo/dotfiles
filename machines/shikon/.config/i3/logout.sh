#!/bin/bash
escolha=$(echo -e "Sim\nNao" | rofi -dmenu -p "Sair do i3?")
if [ "$escolha" = "Sim" ]; then
    i3-msg exit
fi
