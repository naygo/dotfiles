#!/usr/bin/env bash
# Apple Cinema 20" (HDMI-0) principal; Samsung 240Hz (DP-0) vertical à direita.
xrandr \
  --output HDMI-0 --mode 1680x1050 --pos 0x0 --rotate normal --primary \
  --output DP-0 --mode 1920x1080 --rate 239.76 --rotate left --pos 1680x0
