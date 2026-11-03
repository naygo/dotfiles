# dotfiles

this repo contains my personal dotfiles setup for i3.

## requirements

before using these configs, make sure you have the following installed:

- picom
- kitty
- polybar
- rofi

## additional resources

some stuff need to be downloaded separately:

- polybar pulseaudio control: [https://github.com/marioortizmanero/polybar-pulseaudio-control](https://github.com/marioortizmanero/polybar-pulseaudio-control)

## updating

after pulling changes from this repo, run the update script to reapply the configs of your machine:

```bash
./update.sh            # git pull + copy configs + reload i3/dunst
./update.sh --full     # also run the heavy installers (fonts, dconf, gsettings)
./update.sh --no-pull  # skip git pull
```

the first run asks which machine this is (`work` or `shikon`) and remembers it in `~/.config/dotfiles-machine`.
the copy overwrites files in `$HOME`, so commit anything you edited there first.
