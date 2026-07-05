#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL=0
RUN_APP=0
AUTO_UPDATE=1

if [[ "${1:-}" == "--install" ]]; then
  INSTALL=1
  shift
fi

if [[ "${1:-}" == "--run-app" ]]; then
  RUN_APP=1
  shift
fi

if [[ "${1:-}" == "--no-update" ]]; then
  AUTO_UPDATE=0
  shift
fi

if [[ "$INSTALL" -eq 1 ]]; then
  sudo apt update
  sudo apt install -y python3-pygame xinit xserver-xorg xserver-xorg-legacy x11-xserver-utils
fi

APP_ARGS=(--profile pi --fullscreen --width 480 --height 320 --scale 1)

maybe_update_repo() {
  if [[ "$AUTO_UPDATE" -ne 1 ]]; then
    return 0
  fi

  if ! command -v git >/dev/null 2>&1; then
    return 0
  fi

  if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  if ! git -C "$ROOT_DIR" fetch --quiet origin main; then
    echo "Auto-update skipped: network unavailable or remote unreachable."
    return 0
  fi

  local local_head remote_head
  local_head="$(git -C "$ROOT_DIR" rev-parse HEAD)"
  remote_head="$(git -C "$ROOT_DIR" rev-parse origin/main)"

  if [[ "$local_head" == "$remote_head" ]]; then
    echo "Already up to date."
    return 0
  fi

  echo "Updating repo from origin/main..."
  if git -C "$ROOT_DIR" pull --ff-only origin main; then
    echo "Update complete."
  else
    echo "Auto-update failed; local changes may be blocking a fast-forward pull."
  fi
}

cd "$ROOT_DIR"

if [[ "$RUN_APP" -eq 1 || -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]]; then
  python3 main.py "${APP_ARGS[@]}" "$@"
  app_status=$?
  maybe_update_repo
  exit "$app_status"
fi

if ! command -v startx >/dev/null 2>&1; then
  echo "startx not found. Run: bash scripts/hdmi.sh --install"
  exit 1
fi

startx "$SCRIPT_DIR/hdmi.sh" -- --run-app "$@"
app_status=$?
maybe_update_repo
exit "$app_status"
