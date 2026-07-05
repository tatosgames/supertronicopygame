#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL=0
RUN_APP=0

if [[ "${1:-}" == "--install" ]]; then
  INSTALL=1
  shift
fi

if [[ "${1:-}" == "--run-app" ]]; then
  RUN_APP=1
  shift
fi

if [[ "$INSTALL" -eq 1 ]]; then
  sudo apt update
  sudo apt install -y python3-pygame xinit xserver-xorg xserver-xorg-legacy x11-xserver-utils
fi

APP_ARGS=(--profile pi --fullscreen --width 480 --height 320 --scale 1)

if [[ "$RUN_APP" -eq 1 ]]; then
  cd "$ROOT_DIR"
  exec python3 main.py "${APP_ARGS[@]}" "$@"
fi

if [[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]]; then
  cd "$ROOT_DIR"
  exec python3 main.py "${APP_ARGS[@]}" "$@"
fi

if ! command -v startx >/dev/null 2>&1; then
  echo "startx not found. Run: bash scripts/rpi.sh --install"
  exit 1
fi

cd "$ROOT_DIR"
exec startx "$SCRIPT_DIR/rpi.sh" -- --run-app "$@"
