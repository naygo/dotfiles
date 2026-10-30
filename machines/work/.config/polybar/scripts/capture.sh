#!/usr/bin/env bash
set -euo pipefail
flameshot gui --raw | xclip -selection clipboard -t image/png
