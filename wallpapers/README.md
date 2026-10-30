# wallpapers

Imagens compartilhadas entre os computadores. Para escolher uma, use `$mod+Shift+w`
ou o comando [`wallpaper`](../.local/bin/wallpaper):

```bash
wallpaper                          # lista no Rofi, com miniaturas
wallpaper ghibli-sky.jpg           # aplica direto
wallpaper --restore hilux-98.jpg   # reaplica a última escolha (usado pelo i3 ao iniciar)
```

Imagens menores que o monitor ficam centralizadas sobre fundo preto; as demais preenchem a
tela. A escolha fica salva em `~/.local/state/wallpaper`. O comando procura as imagens em
`~/dotfiles/wallpapers` (mude com `WALLPAPER_DIR`) e usa `feh`, `xrandr` e `rofi`.

Instalação: `cp -a .local/bin/wallpaper ~/.local/bin/` a partir da raiz do repositório.

| Arquivo | Imagem |
| --- | --- |
| `japanese-garden.png` | Jardim japonês, 1920×1080 (padrão do i3 genérico) |
| `laptop-beer.png` | Notebook e cerveja sobre fundo oliva, 1920×1080 (shikon) |
| `ghibli-sky.jpg` | Céu com nuvens no estilo Ghibli, 1920×1038 |
| `green.jpg` | Textura verde-oliva, 900×900 |
| `hilux-98.jpg` | Hilux 98 na neblina, quadrado de 480×480 (work) |
